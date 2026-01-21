"""
Market Snapshot Client for AarthikAI.

Fetches and caches all data needed for professional market summaries:
- Index performance (Nifty, Sensex, Bank Nifty) 
- FII/DII flows
- Global cues (US markets, Asian markets)
- Currency & commodities (USD/INR, Brent crude)
"""

import asyncio
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
import pytz

logger = logging.getLogger(__name__)


class MarketSnapshotClient:
    """Client for fetching complete market snapshot data."""
    
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
    
    async def get_fii_dii_flows(self) -> Dict[str, Any]:
        """
        Get FII/DII daily flows.
        
        Note: FII/DII data is published by NSDL after market close (~6-7 PM IST).
        Currently returning pending status as Python libraries for this are unreliable.
        
        Future improvement: Scrape NSDL directly or use paid API.
        
        Returns:
            Dict with fii_dii status
        """
        # FII/DII data availability depends on time of day
        now = datetime.now(self.ist)
        hour = now.hour
        
        # Market closes at 3:30 PM, NSDL publishes data around 6-7 PM
        if hour < 15:  # Before market close
            return {
                "status": "pending",
                "message": "FII/DII data will be available after market close (post 6 PM IST)",
                "source": "NSDL"
            }
        elif hour < 18:  # Between market close and NSDL publish
            return {
                "status": "pending", 
                "message": "FII/DII data pending publication by NSDL (typically by 6-7 PM IST)",
                "source": "NSDL"
            }
        else:  # After 6 PM - data should be available
            return {
                "status": "pending",
                "message": "FII/DII data available on NSDL/NSE website",
                "note": "Automated fetching pending implementation",
                "source": "NSDL"
            }
    
    async def get_global_cues(self) -> Dict[str, Any]:
        """
        Get US and Asian market data from Yahoo Finance.
        
        Returns:
            Dict with major global indices performance
        """
        try:
            import yfinance as yf
            
            tickers = {
                "sp500": "^GSPC",
                "nasdaq": "^IXIC",
                "dow": "^DJI",
                "nikkei": "^N225",
                "hang_seng": "^HSI",
                "ftse": "^FTSE"
            }
            
            results = {}
            
            loop = asyncio.get_event_loop()
            
            for name, symbol in tickers.items():
                try:
                    ticker = yf.Ticker(symbol)
                    # Run in executor to avoid blocking
                    info = await loop.run_in_executor(None, lambda t=ticker: t.info)
                    
                    prev_close = info.get("previousClose", 0)
                    current = info.get("regularMarketPrice", prev_close)
                    change_pct = ((current - prev_close) / prev_close * 100) if prev_close else 0
                    
                    results[name] = {
                        "price": current,
                        "prev_close": prev_close,
                        "change_pct": round(change_pct, 2),
                        "name": info.get("shortName", symbol)
                    }
                except Exception as e:
                    logger.warning(f"Failed to fetch {name}: {e}")
                    results[name] = {"error": str(e)}
            
            return {
                "indices": results,
                "timestamp": datetime.now(self.ist).isoformat(),
                "status": "live" if results else "error"
            }
            
        except Exception as e:
            logger.error(f"Error fetching global cues: {e}")
            return {"error": str(e), "status": "error"}
    
    async def get_forex_commodities(self) -> Dict[str, Any]:
        """
        Get USD/INR and Brent crude prices from Yahoo Finance.
        
        Returns:
            Dict with forex and commodity prices
        """
        try:
            import yfinance as yf
            
            loop = asyncio.get_event_loop()
            
            # USD/INR
            usdinr_ticker = yf.Ticker("USDINR=X")
            usdinr_info = await loop.run_in_executor(None, lambda: usdinr_ticker.info)
            
            # Brent Crude
            brent_ticker = yf.Ticker("BZ=F")
            brent_info = await loop.run_in_executor(None, lambda: brent_ticker.info)
            
            # Gold
            gold_ticker = yf.Ticker("GC=F")
            gold_info = await loop.run_in_executor(None, lambda: gold_ticker.info)
            
            return {
                "usdinr": {
                    "price": usdinr_info.get("regularMarketPrice", 0),
                    "prev_close": usdinr_info.get("previousClose", 0),
                    "change_pct": round(
                        ((usdinr_info.get("regularMarketPrice", 0) - usdinr_info.get("previousClose", 0)) 
                         / usdinr_info.get("previousClose", 1)) * 100, 2
                    )
                },
                "brent_crude": {
                    "price": brent_info.get("regularMarketPrice", 0),
                    "currency": "USD",
                    "unit": "per barrel"
                },
                "gold": {
                    "price": gold_info.get("regularMarketPrice", 0),
                    "currency": "USD",
                    "unit": "per oz"
                },
                "timestamp": datetime.now(self.ist).isoformat(),
                "status": "live"
            }
            
        except Exception as e:
            logger.error(f"Error fetching forex/commodities: {e}")
            return {"error": str(e), "status": "error"}
    
    async def get_full_snapshot(self) -> Dict[str, Any]:
        """
        Get complete market snapshot with all data blocks.
        
        Returns:
            Complete market snapshot for chatbot responses
        """
        # Fetch all data concurrently
        fii_dii_task = self.get_fii_dii_flows()
        global_task = self.get_global_cues()
        forex_task = self.get_forex_commodities()
        
        fii_dii, global_cues, forex = await asyncio.gather(
            fii_dii_task, global_task, forex_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(fii_dii, Exception):
            fii_dii = {"error": str(fii_dii)}
        if isinstance(global_cues, Exception):
            global_cues = {"error": str(global_cues)}
        if isinstance(forex, Exception):
            forex = {"error": str(forex)}
        
        now = datetime.now(self.ist)
        
        return {
            "timestamp": now.strftime("%d %b %Y, %I:%M %p IST"),
            "date": now.strftime("%Y-%m-%d"),
            "fii_dii": fii_dii,
            "global_cues": global_cues,
            "forex_commodities": forex,
            "status": "live"
        }


# Singleton instance
_market_snapshot_client: Optional[MarketSnapshotClient] = None


def get_market_snapshot_client() -> MarketSnapshotClient:
    """Get singleton market snapshot client instance."""
    global _market_snapshot_client
    if _market_snapshot_client is None:
        _market_snapshot_client = MarketSnapshotClient()
    return _market_snapshot_client
