"""
NSE Data Client using nselib

Provides fallback data sources for:
- Index P/E and P/B ratios
- FII/DII cash market flows
- Index constituents and weights
- Corporate actions
"""

import asyncio
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

from src.data.redis_client import get_redis_cache

logger = logging.getLogger(__name__)


class NSEClient:
    """
    NSE data client using nselib for public NSE data.
    
    Provides:
    - Index valuations (P/E, P/B)
    - FII/DII flows
    - Index constituents
    """
    
    def __init__(self):
        self.nse = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize nselib client."""
        try:
            from nselib.capital_market import capital_market_data
            self.nse = capital_market_data
            logger.info("NSE client initialized successfully")
        except ImportError:
            logger.warning("nselib not installed - NSE data unavailable")
        except Exception as e:
            logger.error(f"Error initializing NSE client: {e}")
    
    async def get_index_pe_pb(self, index: str = "NIFTY 50") -> Optional[Dict[str, Any]]:
        """
        Get P/E and P/B ratios for index.
        
        Args:
            index: Index name (default: "NIFTY 50")
            
        Returns:
            Dict with pe, pb, as_of timestamp
        """
        if not self.nse:
            logger.warning("NSE client not initialized - P/E, P/B unavailable")
            return None
        
        cache = get_redis_cache()
        cache_key = f"nse_index_valuation:{index}"
        
        # Check cache (24 hour TTL - valuation data updates daily)
        cached = await cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for index valuation: {index}")
            return cached
        
        try:
            # Fetch index data from NSE using correct function name
            # Note: nselib methods are synchronous, run in thread pool
            index_data = await asyncio.to_thread(
                self.nse.index_data,
                index.replace(" ", "")  # "NIFTY 50" -> "NIFTY50"
            )
            
            if not index_data:
                logger.warning(f"No index data returned for {index}")
                return None
            
            # Extract P/E and P/B from the response
            # nselib returns a dict with various index metrics
            pe_ratio = index_data.get("pe", None)
            pb_ratio = index_data.get("pb", None)
            
            if pe_ratio is None and pb_ratio is None:
                logger.warning(f"P/E and P/B not found in index data for {index}")
                return None
            
            result = {
                "pe": round(float(pe_ratio), 2) if pe_ratio else None,
                "pb": round(float(pb_ratio), 2) if pb_ratio else None,
                "as_of": "last close",
                "timestamp": datetime.now().strftime("%Y-%m-%d")
            }
            
            logger.info(f"Successfully fetched P/E: {result['pe']}, P/B: {result['pb']} for {index}")
            
            # Cache for 24 hours
            await cache.set(cache_key, result, ttl=86400)
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching index P/E, P/B for {index}: {e}", exc_info=True)
            return None
    
    async def get_fii_dii_data(self) -> Optional[Dict[str, Any]]:
        """
        Get FII/DII cash market flows (T-1 data).
        
        Returns:
            Dict with fii_net, dii_net, date
        """
        if not self.nse:
            logger.warning("NSE client not initialized - FII/DII data unavailable")
            return None
        
        cache = get_redis_cache()
        cache_key = "nse_fii_dii_flows"
        
        # Check cache (6 hour TTL - updates once daily)
        cached = await cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for FII/DII flows")
            return cached
        
        try:
            # Fetch FII/DII data using correct function name
            fii_dii = await asyncio.to_thread(self.nse.fii_dii_trading_activity)
            
            # Check if we got data (DataFrame check)
            if fii_dii is None or (hasattr(fii_dii, 'empty') and fii_dii.empty):
                logger.warning("No FII/DII data returned")
                return None
            
            # nselib returns a DataFrame or dict with FII/DII activity
            # Get the latest row if it's a DataFrame
            if hasattr(fii_dii, 'iloc'):
                # It's a DataFrame
                latest = fii_dii.iloc[0].to_dict() if len(fii_dii) > 0 else {}
            elif isinstance(fii_dii, list) and len(fii_dii) > 0:
                latest = fii_dii[0]
            else:
                latest = fii_dii if isinstance(fii_dii, dict) else {}
            
            if not latest:
                logger.warning("Empty FII/DII data")
                return None
            
            # Extract FII and DII net values
            # nselib returns DataFrame with columns: category, buyValue, sellValue, netValue, etc.
            # category is either 'DII' or 'FII/FPI'
            fii_net = 0
            dii_net = 0
            
            # Try to extract from DataFrame structure
            if 'category' in latest and 'netValue' in latest:
                # This is a single row dict from DataFrame
                if latest.get('category') == 'FII/FPI':
                    fii_net = latest.get('netValue', 0)
                elif latest.get('category') == 'DII':
                    dii_net = latest.get('netValue', 0)
            else:
                # Fallback: try common field name variations
                fii_net = (latest.get("fii_net") or 
                          latest.get("fii_net_cash") or 
                          latest.get("FII") or 
                          latest.get("FII (Rs. Cr)") or 0)
                
                dii_net = (latest.get("dii_net") or 
                          latest.get("dii_net_cash") or 
                          latest.get("DII") or 
                          latest.get("DII (Rs. Cr)") or 0)
            
            # If we only got one category, we need to get the other from the DataFrame
            if hasattr(fii_dii, 'iloc') and len(fii_dii) > 1:
                for _, row in fii_dii.iterrows():
                    if row.get('category') == 'FII/FPI':
                        fii_net = row.get('netValue', 0)
                    elif row.get('category') == 'DII':
                        dii_net = row.get('netValue', 0)
            
            date = latest.get("date", latest.get("Date", ""))
            
            result = {
                "fii_net": float(fii_net) if fii_net else 0,
                "dii_net": float(dii_net) if dii_net else 0,
                "date": str(date),
                "as_of": "T-1 provisional"
            }
            
            logger.info(f"Successfully fetched FII: ₹{result['fii_net']:.2f} cr, DII: ₹{result['dii_net']:.2f} cr")
            
            # Cache for 6 hours
            await cache.set(cache_key, result, ttl=21600)
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching FII/DII data: {e}", exc_info=True)
            return None
    
    async def get_nifty_constituents_with_weights(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get Nifty 50 constituents with official weights from NSE.
        
        Returns:
            List of dicts with symbol, weight, sector
        """
        if not self.nse:
            return None
        
        cache = get_redis_cache()
        cache_key = "nse_nifty50_constituents"
        
        # Check cache (7 day TTL - weights change infrequently)
        cached = await cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for Nifty 50 constituents")
            return cached
        
        try:
            # Fetch Nifty 50 constituents
            constituents = await asyncio.to_thread(
                self.nse.nifty_50
            )
            
            if not constituents:
                return None
            
            # Format data
            result = []
            for stock in constituents:
                result.append({
                    "symbol": stock.get("symbol", ""),
                    "weight": stock.get("weight", 0),
                    "sector": stock.get("industry", "Unknown")
                })
            
            # Cache for 7 days
            await cache.set(cache_key, result, ttl=604800)
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching Nifty 50 constituents: {e}")
            return None


# Singleton instance
_nse_client_instance: Optional[NSEClient] = None


def get_nse_client() -> NSEClient:
    """Get singleton NSE client instance."""
    global _nse_client_instance
    if _nse_client_instance is None:
        _nse_client_instance = NSEClient()
    return _nse_client_instance
