"""
Dhan API Client - Async Wrapper for Market Data

Features:
- Async wrapper around Dhan SDK
- Token auto-refresh (24-hour validity)
- Optimized instruments caching (memory-efficient)
- Market data (LTP, OHLC, historical)
- Redis caching for low latency

Note: Portfolio queries still use Zerodha (user-specific data)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dhanhq import dhanhq

from src.config import settings
from src.data.redis_client import get_redis_cache

logger = logging.getLogger(__name__)


class DhanClient:
    """
    Async wrapper for Dhan API.
    
    Optimized for:
    - Low latency market data
    - Memory-efficient instruments caching
    - Automatic token refresh
    """
    
    def __init__(self):
        self.client_id = settings.dhan_client_id
        self.access_token = settings.dhan_access_token
        
        # Initialize Dhan client
        self.dhan: Optional[dhanhq] = None
        if self.client_id and self.access_token:
            self.dhan = dhanhq(self.client_id, self.access_token)
            
            # Initialize instruments cache (async, will be done on first use)
            self._instruments_initialized = False
        
        # Instruments cache (lazy-loaded, memory-efficient)
        self._instruments_cache: Dict[str, Any] = {}
        self._cache_initialized = False
    
    async def get_ltp(self, symbols: List[str], exchange: str = "NSE_EQ") -> Dict[str, float]:
        """
        Get Last Traded Price for multiple symbols.
        
        Args:
            symbols: List of symbol names (e.g., ["RELIANCE", "TCS"])
            exchange: Exchange segment (NSE_EQ, BSE_EQ, etc.)
        
        Returns:
            Dict mapping symbol -> LTP
        
        Example:
            >>> ltps = await client.get_ltp(["RELIANCE", "TCS"])
            >>> print(ltps)  # {"RELIANCE": 2450.50, "TCS": 3500.25}
        """
        cache = get_redis_cache()
        cache_key = f"dhan:ltp:{exchange}:{','.join(sorted(symbols))}"
        
        # Check cache (1-minute TTL for LTP)
        cached = await cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for LTP: {symbols}")
            return cached
        
        try:
            # Get security IDs for symbols
            security_ids = await self._get_security_ids(symbols, exchange)
            
            # Prepare request payload
            payload = {exchange: security_ids}
            
            # Call Dhan API (correct method name: ticker_data)
            logger.info(f"Fetching LTP for {len(symbols)} symbols from Dhan")
            response = await asyncio.to_thread(
                self.dhan.ticker_data,
                payload
            )
            
            # Parse response
            ltps = {}
            if response.get("status") == "success":
                data = response.get("data", {}).get(exchange, {})
                for sec_id, info in data.items():
                    symbol = self._get_symbol_from_id(sec_id, exchange)
                    if symbol:
                        ltps[symbol] = info.get("last_price", 0)
            
            # Cache for 1 minute
            await cache.set(cache_key, ltps, ttl=60)
            
            return ltps
            
        except Exception as e:
            logger.error(f"Error fetching LTP from Dhan: {e}")
            return {}
    
    async def get_ohlc(self, symbols: List[str], exchange: str = "NSE_EQ") -> Dict[str, Dict[str, Any]]:
        """
        Get OHLC data for multiple symbols.
        
        Args:
            symbols: List of symbol names
            exchange: Exchange segment
        
        Returns:
            Dict mapping symbol -> {open, high, low, close, volume}
        """
        cache = get_redis_cache()
        cache_key = f"dhan:ohlc:{exchange}:{','.join(sorted(symbols))}"
        
        # Check cache (5-minute TTL for OHLC)
        cached = await cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for OHLC: {symbols}")
            return cached
        
        try:
            # Get security IDs
            security_ids = await self._get_security_ids(symbols, exchange)
            
            if not security_ids:
                logger.warning(f"✗ No security IDs found for any symbols")
                return {}
            
            # Prepare request
            payload = {exchange: security_ids}
            
            # DEBUG: Log the exact payload being sent
            logger.info(f"Fetching OHLC for {len(symbols)} symbols from Dhan")
            logger.debug(f"API Payload: {payload}")
            logger.debug(f"Security IDs: {security_ids[:5]}..." if len(security_ids) > 5 else f"Security IDs: {security_ids}")
            
            # Call Dhan API (correct method name: ohlc_data)
            response = await asyncio.to_thread(
                self.dhan.ohlc_data,
                payload
            )
            
            # DEBUG: Log the response
            logger.debug(f"API Response status: {response.get('status')}")
            logger.debug(f"API Response keys: {list(response.keys())}")
            logger.debug(f"API Response data type: {type(response.get('data'))}")
            if isinstance(response.get('data'), dict):
                logger.debug(f"API Response data keys: {list(response.get('data', {}).keys())}")
            logger.debug(f"Full API Response: {response}")
            
            # Parse response
            ohlc_data = {}
            if response.get("status") == "success":
                # The dhanhq SDK wraps the response in an extra "data" layer
                # Structure: response['data']['data']['NSE_EQ'][security_id]
                outer_data = response.get("data", {})
                
                # Check if there's a nested "data" key (SDK behavior)
                if "data" in outer_data and isinstance(outer_data["data"], dict):
                    inner_data = outer_data["data"]
                    data = inner_data.get(exchange, {})
                else:
                    # Fallback to direct access
                    data = outer_data.get(exchange, {})
                
                if not data:
                    logger.warning(f"✗ No data returned for batch (API returned success but empty data)")
                    logger.debug(f"Outer data keys: {list(outer_data.keys())}")
                    return {}
                
                logger.info(f"✓ Received data for {len(data)} securities")
                
                # Parse response and map to our short symbols
                for sec_id_str, info in data.items():
                    sec_id = int(sec_id_str)
                    
                    # Get our short symbol (e.g., "TCS") instead of Dhan's full name
                    symbol = self._get_symbol_from_id(sec_id, exchange)
                    
                    if symbol:
                        # OHLC data is nested under "ohlc" key
                        ohlc = info.get("ohlc", {})
                        ohlc_data[symbol] = {
                            "open": ohlc.get("open", 0),
                            "high": ohlc.get("high", 0),
                            "low": ohlc.get("low", 0),
                            "close": ohlc.get("close", 0),
                            "volume": info.get("volume", 0),
                            "last_price": info.get("last_price", 0),
                            "change_percent": self._calculate_change_percent(
                                ohlc.get("close", 0),
                                info.get("last_price", 0)
                            ),
                        }
                        logger.debug(f"Mapped security_id {sec_id} → {symbol}: ₹{info.get('last_price')}")
                    else:
                        logger.warning(f"Could not map security_id {sec_id} to symbol")
            
            # Cache for 5 minutes
            await cache.set(cache_key, ohlc_data, ttl=300)
            
            return ohlc_data
            
        except Exception as e:
            logger.error(f"Error fetching OHLC from Dhan: {e}")
            return {}
    
    async def get_intraday_ohlc_for_indices(
        self,
        indices: List[str],
        exchange: str = "IDX_I"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get today's OHLC data for indices using Dhan's intraday API.
        
        This method is specifically for indices (NIFTY 50, NIFTY BANK, etc.)
        which use a different exchange segment (IDX_I) and instrument type (INDEX).
        
        Args:
            indices: List of index names (e.g., ["NIFTY 50", "NIFTY BANK"])
            exchange: Exchange segment (IDX_I for indices)
        
        Returns:
            Dict mapping index name -> {open, high, low, close, volume, last_price, change_percent}
        """
        from datetime import datetime
        
        ohlc_data = {}
        today = datetime.now().strftime("%Y-%m-%d")
        
        for index_name in indices:
            try:
                # Get security ID for index
                security_id = await self._get_security_id_for_index(index_name)
                
                if not security_id:
                    logger.warning(f"No security ID found for index: {index_name}")
                    continue
                
                # Prepare request for intraday data (today's data)
                payload = {
                    "security_id": str(security_id),
                    "exchange_segment": exchange,
                    "instrument_type": "INDEX",
                    "interval": "1",  # 1-minute candles
                    "from_date": f"{today} 09:15:00",  # Market open
                    "to_date": f"{today} 15:30:00"   # Market close
                }
                
                logger.info(f"Fetching intraday OHLC for {index_name} (ID: {security_id})")
                
                # Call Dhan intraday API
                response = await asyncio.to_thread(
                    self.dhan.intraday_minute_data,
                    **payload
                )
                
                # Parse response - get latest candle for today's OHLC
                if isinstance(response, dict) and response.get("open"):
                    opens = response.get("open", [])
                    highs = response.get("high", [])
                    lows = response.get("low", [])
                    closes = response.get("close", [])
                    volumes = response.get("volume", [])
                    
                    if opens and closes:
                        # Calculate today's OHLC from all candles
                        today_open = opens[0]  # First candle's open
                        today_high = max(highs) if highs else 0
                        today_low = min([l for l in lows if l > 0]) if lows else 0
                        today_close = closes[-1]  # Last candle's close (latest)
                        today_volume = sum(volumes) if volumes else 0
                        
                        # Get previous close (yesterday's close)
                        # For now, use first candle's close as approximation
                        prev_close = closes[0] if len(closes) > 1 else today_open
                        
                        ohlc_data[index_name] = {
                            "open": today_open,
                            "high": today_high,
                            "low": today_low,
                            "close": prev_close,  # Yesterday's close
                            "volume": today_volume,
                            "last_price": today_close,  # Current price
                            "change_percent": self._calculate_change_percent(
                                prev_close,
                                today_close
                            ),
                        }
                        
                        logger.info(f"✓ {index_name}: {today_close:,.2f} ({ohlc_data[index_name]['change_percent']:+.2f}%)")
                    else:
                        logger.warning(f"No candle data for {index_name}")
                else:
                    logger.warning(f"Invalid response for {index_name}: {type(response)}")
                    
            except Exception as e:
                logger.error(f"Error fetching intraday OHLC for {index_name}: {e}")
                continue
        
        return ohlc_data
    
    async def _get_security_id_for_index(self, index_name: str) -> Optional[int]:
        """
        Get security ID for an index.
        
        Note: Indices have different security IDs than stocks.
        We'll need to add index mappings to dhan_symbol_mapping.py
        
        Args:
            index_name: Index name (e.g., "NIFTY 50", "NIFTY BANK")
        
        Returns:
            Security ID or None
        """
        # Index security ID mapping (hardcoded for now)
        # TODO: Move to dhan_symbol_mapping.py
        INDEX_SECURITY_IDS = {
            "NIFTY 50": 13,
            "NIFTY BANK": 25,
            "NIFTY IT": 1135,
            "NIFTY PHARMA": 1071,
            "NIFTY AUTO": 1049,
            "NIFTY METAL": 1090,
            "NIFTY FMCG": 1058,
            "NIFTY ENERGY": 1055,
            "NIFTY REALTY": 1074,
            "NIFTY PSU BANK": 1072,
            "NIFTY MEDIA": 1089,
            "NIFTY FIN SERVICE": 1057,
            "NIFTY INFRA": 1063,
        }
        
        return INDEX_SECURITY_IDS.get(index_name)
    
    async def get_historical(
        self,
        symbol: str,
        exchange: str = "NSE_EQ",
        interval: str = "day",
        from_date: str = None,
        to_date: str = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get historical candle data.
        
        Args:
            symbol: Symbol name
            exchange: Exchange segment
            interval: "day" or "1", "5", "15", "25", "60" (minutes)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            days: Number of days (if from_date not provided)
        
        Returns:
            List of candles [{open, high, low, close, volume, timestamp}]
        """
        cache = get_redis_cache()
        cache_key = f"dhan:historical:{symbol}:{exchange}:{interval}:{from_date}:{to_date}"
        
        # Check cache (1-hour TTL for historical)
        cached = await cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for historical: {symbol}")
            return cached
        
        try:
            # Get security ID
            security_id = await self._get_security_id(symbol, exchange)
            
            # Calculate dates if not provided
            if not from_date:
                from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            if not to_date:
                to_date = datetime.now().strftime("%Y-%m-%d")
            
            # Prepare request (use snake_case parameter names)
            payload = {
                "security_id": str(security_id),
                "exchange_segment": exchange,
                "instrument_type": "EQUITY",  # TODO: Detect instrument type
                "from_date": from_date,
                "to_date": to_date
            }
            
            # Choose endpoint based on interval
            if interval == "day":
                logger.info(f"Fetching daily historical for {symbol}")
                response = await asyncio.to_thread(
                    self.dhan.historical_daily_data,
                    **payload
                )
            else:
                # Intraday data (use snake_case parameter names)
                payload["interval"] = interval
                payload["from_date"] = f"{from_date} 09:30:00"
                payload["to_date"] = f"{to_date} 15:30:00"
                
                logger.info(f"Fetching {interval}-min historical for {symbol}")
                response = await asyncio.to_thread(
                    self.dhan.intraday_minute_data,
                    **payload
                )
            
            # Parse response
            candles = []
            if isinstance(response, dict):
                opens = response.get("open", [])
                highs = response.get("high", [])
                lows = response.get("low", [])
                closes = response.get("close", [])
                volumes = response.get("volume", [])
                timestamps = response.get("timestamp", [])
                
                for i in range(len(opens)):
                    candles.append({
                        "open": opens[i],
                        "high": highs[i],
                        "low": lows[i],
                        "close": closes[i],
                        "volume": volumes[i],
                        "timestamp": timestamps[i],
                        "date": datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d")
                    })
            
            # Cache for 1 hour
            await cache.set(cache_key, candles, ttl=3600)
            
            return candles
            
        except Exception as e:
            logger.error(f"Error fetching historical data from Dhan: {e}")
            return []
    
    async def _get_security_ids(self, symbols: List[str], exchange: str) -> List[int]:
        """Get security IDs for symbols using ISIN-based lookup.
        
        Also builds reverse mapping: security_id → our short symbol (e.g., "TCS")
        """
        from src.data.dhan_instruments_cache import get_dhan_instruments_cache
        from src.data.dhan_symbol_mapping import SYMBOL_TO_ISIN
        
        # Initialize cache on first use
        if not self._instruments_initialized:
            cache_obj = get_dhan_instruments_cache()
            await cache_obj.initialize(self.dhan)
            self._instruments_initialized = True
            logger.info("✅ Dhan instruments cache initialized")
        
        cache = get_dhan_instruments_cache()
        security_ids = []
        found_symbols = []
        missing_symbols = []
        
        # Build reverse mapping: security_id → our short symbol
        if not hasattr(self, '_id_to_short_symbol'):
            self._id_to_short_symbol = {}
        
        # Use ISIN-based lookup for each symbol
        for symbol in symbols:
            isin = SYMBOL_TO_ISIN.get(symbol)
            if isin:
                sec_id = await cache.get_security_id_by_isin(isin)
                if sec_id:
                    security_ids.append(sec_id)
                    found_symbols.append(symbol)
                    # Map security_id → our short symbol (e.g., 11536 → "TCS")
                    self._id_to_short_symbol[sec_id] = symbol
                else:
                    missing_symbols.append(f"{symbol} (ISIN: {isin})")
            else:
                # Fallback to symbol-based lookup
                sec_id = await cache.get_security_id(symbol, exchange)
                if sec_id:
                    security_ids.append(sec_id)
                    found_symbols.append(symbol)
                    self._id_to_short_symbol[sec_id] = symbol
                else:
                    missing_symbols.append(symbol)
        
        if missing_symbols:
            logger.warning(f"No security IDs found for {len(missing_symbols)} symbols: {missing_symbols[:5]}...")
        
        if found_symbols:
            logger.info(f"✓ Found security IDs for {len(found_symbols)}/{len(symbols)} symbols via ISIN lookup")
        
        return security_ids
    
    async def _get_security_id(self, symbol: str, exchange: str) -> int:
        """Get security ID for a single symbol."""
        from src.data.dhan_instruments_cache import get_dhan_instruments_cache
        
        cache = get_dhan_instruments_cache()
        sec_id = await cache.get_security_id(symbol, exchange)
        return sec_id if sec_id else 0
    
    def _get_symbol_from_id(self, security_id: int, exchange: str) -> Optional[str]:
        """Get symbol name from security ID using reverse lookup.
        
        Returns our short symbol (e.g., "TCS") instead of Dhan's full name.
        
        Args:
            security_id: Dhan security ID
            exchange: Exchange segment (NSE_EQ, etc.)
            
        Returns:
            Our short symbol name (e.g., "TCS") or None if not found
        """
        # PRIORITY 1: Use our custom reverse mapping (security_id → short symbol)
        # This was built during _get_security_ids() and maps to our symbols (e.g., "TCS")
        if hasattr(self, '_id_to_short_symbol'):
            short_symbol = self._id_to_short_symbol.get(security_id)
            if short_symbol:
                return short_symbol
        
        # PRIORITY 2: Fallback to Dhan's cache (returns full name like "TATA CONSULTANCY SERV LT")
        # We'll try to map this back to our short symbol using ISIN
        from src.data.dhan_instruments_cache import get_dhan_instruments_cache
        from src.data.dhan_symbol_mapping import ISIN_TO_SYMBOL
        
        cache = get_dhan_instruments_cache()
        dhan_symbol = cache.get_symbol_from_id(int(security_id), exchange)
        
        if dhan_symbol:
            # Try to find our short symbol by checking if this security_id matches any ISIN
            # This is a fallback for symbols not in our mapping
            for isin, short_sym in ISIN_TO_SYMBOL.items():
                sec_id_for_isin = cache._isin_to_id.get(isin)
                if sec_id_for_isin == security_id:
                    return short_sym
            
            # Last resort: return Dhan's full name
            # (This shouldn't happen for symbols in our SYMBOL_TO_ISIN mapping)
            logger.warning(f"Using Dhan's full symbol name: {dhan_symbol} for security_id {security_id}")
            return dhan_symbol
        
        return None
    
    def _calculate_change_percent(self, close: float, last_price: float) -> float:
        """Calculate percentage change."""
        if close == 0:
            return 0
        return round(((last_price - close) / close) * 100, 2)


# Singleton instance
_dhan_client_instance: Optional[DhanClient] = None


def get_dhan_client() -> DhanClient:
    """Get singleton Dhan client instance."""
    global _dhan_client_instance
    if _dhan_client_instance is None:
        _dhan_client_instance = DhanClient()
    return _dhan_client_instance
