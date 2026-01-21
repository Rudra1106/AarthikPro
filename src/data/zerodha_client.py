"""
Zerodha Kite Connect - Async Client Wrapper for Chatbot Integration

Features:
- Async wrapper around KiteConnect SDK
- Instrument token caching
- Symbol to instrument_token mapping
- LTP, OHLC, and historical data fetching
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
import logging

from src.config import settings
from src.data.redis_client import get_redis_cache

logger = logging.getLogger(__name__)


class ZerodhaClient:
    """
    Async wrapper for Zerodha Kite Connect API.
    
    Optimized for chatbot integration with:
    - Instrument caching for fast symbol lookups
    - Async methods using asyncio.to_thread()
    - Automatic symbol normalization
    """
    
    def __init__(self):
        self.api_key = settings.zerodha_api_key
        self.api_secret = settings.zerodha_api_secret
        self.access_token = settings.zerodha_access_token
        self.refresh_token = settings.zerodha_refresh_token
        
        # Initialize KiteConnect
        self.kite: Optional[KiteConnect] = None
        if self.api_key:
            self.kite = KiteConnect(api_key=self.api_key)
            if self.access_token:
                self.kite.set_access_token(self.access_token)
            
            # Set session expiry hook for automatic token renewal
            self.kite.set_session_expiry_hook(self._on_session_expired)
        
        # Instrument cache
        self._instruments_cache: Dict[str, List[Dict]] = {}
        self._symbol_to_token: Dict[str, int] = {}
        self._cache_initialized = False
        
        # Token renewal tracking
        self._token_renewal_in_progress = False
    
    def _on_session_expired(self):
        """
        Callback when session expires.
        Attempts to renew access token using refresh token.
        """
        if self._token_renewal_in_progress:
            return
        
        if not self.refresh_token or not self.api_secret:
            logger.error("Cannot renew token: refresh_token or api_secret not configured")
            return
        
        try:
            self._token_renewal_in_progress = True
            logger.info("Access token expired, attempting renewal...")
            
            # Renew access token
            response = self.kite.renew_access_token(
                refresh_token=self.refresh_token,
                api_secret=self.api_secret
            )
            
            if "access_token" in response:
                self.access_token = response["access_token"]
                logger.info("Access token renewed successfully")
                
                # Optionally update refresh token if provided
                if "refresh_token" in response:
                    self.refresh_token = response["refresh_token"]
                    logger.info("Refresh token also updated")
            else:
                logger.error("Token renewal failed: no access_token in response")
                
        except Exception as e:
            logger.error(f"Error renewing access token: {e}")
        finally:
            self._token_renewal_in_progress = False
    
    async def renew_token_manually(self) -> bool:
        """
        Manually renew access token using refresh token.
        
        Returns:
            True if renewal successful, False otherwise
        """
        if not self.kite or not self.refresh_token or not self.api_secret:
            logger.error("Cannot renew token: missing credentials")
            return False
        
        try:
            response = await asyncio.to_thread(
                self.kite.renew_access_token,
                refresh_token=self.refresh_token,
                api_secret=self.api_secret
            )
            
            if "access_token" in response:
                self.access_token = response["access_token"]
                if "refresh_token" in response:
                    self.refresh_token = response["refresh_token"]
                
                logger.info("Token renewed successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error renewing token: {e}")
            return False
    
    async def _ensure_cache_initialized(self, exchange: str = "NSE"):
        """Initialize instrument cache if not already done."""
        if self._cache_initialized or not self.kite:
            return
        
        try:
            # Fetch instruments list
            instruments = await asyncio.to_thread(
                self.kite.instruments,
                exchange
            )
            
            self._instruments_cache[exchange] = instruments
            
            # Build symbol to token mapping
            for inst in instruments:
                symbol = inst["tradingsymbol"]
                token = inst["instrument_token"]
                key = f"{exchange}:{symbol}"
                self._symbol_to_token[key] = token
            
            self._cache_initialized = True
            logger.info(f"Initialized instrument cache for {exchange}: {len(instruments)} instruments")
            
        except Exception as e:
            logger.error(f"Error initializing instrument cache: {e}")
    
    async def _get_instrument_token(self, symbol: str, exchange: str = "NSE") -> Optional[int]:
        """Get instrument token for a symbol (with Redis caching)."""
        # Check cache first (24-hour TTL)
        cache = get_redis_cache()
        cache_key = f"instrument_token:{exchange}:{symbol.upper()}"
        cached_token = await cache.get(cache_key)
        
        if cached_token is not None:
            logger.debug(f"Cache hit for instrument token: {symbol}")
            return cached_token
        
        # Check in-memory cache
        key = f"{exchange}:{symbol.upper()}"
        token = self._symbol_to_token.get(key)
        
        if token:
            # Cache in Redis for 24 hours
            await cache.set(cache_key, token, ttl=86400)
        
        return token
    
    async def search_instrument(self, symbol: str, exchange: str = "NSE") -> Optional[Dict[str, Any]]:
        """
        Search for instrument by symbol.
        
        Args:
            symbol: Stock symbol (e.g., "INFY", "RELIANCE")
            exchange: Exchange (NSE, BSE)
            
        Returns:
            Instrument details or None
        """
        await self._ensure_cache_initialized(exchange)
        
        symbol_upper = symbol.upper()
        instruments = self._instruments_cache.get(exchange, [])
        
        # Exact match
        for inst in instruments:
            if inst["tradingsymbol"] == symbol_upper:
                return inst
        
        # Fuzzy match by name
        for inst in instruments:
            if symbol_upper in inst["name"].upper():
                return inst
        
        return None
    
    async def get_ltp(self, symbol: str, exchange: str = "NSE") -> Optional[float]:
        """
        Get Last Traded Price for a stock (with Redis caching).
        
        Args:
            symbol: Stock symbol
            exchange: Exchange (NSE, BSE)
            
        Returns:
            Last traded price or None
        """
        if not self.kite:
            logger.warning("Zerodha client not initialized")
            return None
        
        # Check cache first (1-min TTL for LTP)
        cache = get_redis_cache()
        cache_key = f"ltp:{exchange}:{symbol.upper()}"
        cached_ltp = await cache.get(cache_key)
        
        if cached_ltp is not None:
            logger.debug(f"Cache hit for LTP: {symbol}")
            return cached_ltp
        
        try:
            await self._ensure_cache_initialized(exchange)
            
            instrument_key = f"{exchange}:{symbol.upper()}"
            
            # Fetch LTP from API
            data = await asyncio.to_thread(
                self.kite.ltp,
                [instrument_key]
            )
            
            if instrument_key in data:
                ltp = data[instrument_key]["last_price"]
                
                # Cache for 1 minute (LTP changes frequently)
                await cache.set(cache_key, ltp, ttl=60)
                
                return ltp
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching LTP for {symbol}: {e}")
            return None
    
    async def get_ohlc(self, symbol: str, exchange: str = "NSE") -> Optional[Dict[str, Any]]:
        """
        Get OHLC data for a stock (with Redis caching).
        
        Args:
            symbol: Stock symbol
            exchange: Exchange (NSE, BSE)
            
        Returns:
            OHLC data with open, high, low, close, last_price
        """
        if not self.kite:
            logger.warning("Zerodha client not initialized")
            return None
        
        # Check cache first (5-min TTL for OHLC)
        cache = get_redis_cache()
        cache_key = f"ohlc:{exchange}:{symbol.upper()}"
        cached_ohlc = await cache.get(cache_key)
        
        if cached_ohlc is not None:
            logger.debug(f"Cache hit for OHLC: {symbol}")
            return cached_ohlc
        
        try:
            await self._ensure_cache_initialized(exchange)
            
            instrument_key = f"{exchange}:{symbol.upper()}"
            
            # Fetch OHLC from API
            data = await asyncio.to_thread(
                self.kite.ohlc,
                [instrument_key]
            )
            
            if instrument_key in data:
                info = data[instrument_key]
                ohlc = info["ohlc"]
                
                # Calculate change
                change = info["last_price"] - ohlc["close"]
                change_percent = (change / ohlc["close"]) * 100 if ohlc["close"] != 0 else 0
                
                result = {
                    "symbol": symbol.upper(),
                    "last_price": info["last_price"],
                    "open": ohlc["open"],
                    "high": ohlc["high"],
                    "low": ohlc["low"],
                    "close": ohlc["close"],  # Previous day close
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "volume": info.get("volume", 0)
                }
                
                # Cache with smart TTL (10 min for hot assets)
                await cache.set_smart(cache_key, result, symbol=symbol)
                
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching OHLC for {symbol}: {e}")
            return None
    
    async def get_quote(self, symbol: str, exchange: str = "NSE") -> Optional[Dict[str, Any]]:
        """
        Get full quote data for a stock.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange (NSE, BSE)
            
        Returns:
            Complete quote data
        """
        if not self.kite:
            logger.warning("Zerodha client not initialized")
            return None
        
        try:
            await self._ensure_cache_initialized(exchange)
            
            instrument_key = f"{exchange}:{symbol.upper()}"
            
            # Fetch quote
            data = await asyncio.to_thread(
                self.kite.quote,
                [instrument_key]
            )
            
            if instrument_key in data:
                return data[instrument_key]
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None
    
    async def get_historical(
        self,
        symbol: str,
        days: int = 30,
        interval: str = "day",
        exchange: str = "NSE"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical data for a stock.
        
        Args:
            symbol: Stock symbol
            days: Number of days of history
            interval: Candle interval (day, 60minute, 15minute, etc.)
            exchange: Exchange (NSE, BSE)
            
        Returns:
            List of historical candles
        """
        if not self.kite:
            logger.warning("Zerodha client not initialized")
            return None
        
        try:
            await self._ensure_cache_initialized(exchange)
            
            # Get instrument token (this is async)
            token = await self._get_instrument_token(symbol, exchange)
            if not token:
                logger.warning(f"Instrument token not found for {symbol} on {exchange}")
                return None
            
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            logger.info(f"Fetching historical data for {symbol} (token: {token}) from {from_date.date()} to {to_date.date()}")
            
            # Fetch historical data
            data = await asyncio.to_thread(
                self.kite.historical_data,
                instrument_token=token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            
            if data:
                logger.info(f"Successfully fetched {len(data)} candles for {symbol}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}", exc_info=True)
            return None
    
    async def get_multiple_ltp(self, symbols: List[str], exchange: str = "NSE") -> Dict[str, float]:
        """
        Get LTP for multiple stocks at once.
        
        Args:
            symbols: List of stock symbols
            exchange: Exchange (NSE, BSE)
            
        Returns:
            Dict mapping symbol to LTP
        """
        if not self.kite:
            logger.warning("Zerodha client not initialized")
            return {}
        
        try:
            await self._ensure_cache_initialized(exchange)
            
            instrument_keys = [f"{exchange}:{sym.upper()}" for sym in symbols]
            
            # Fetch LTP for all symbols
            data = await asyncio.to_thread(
                self.kite.ltp,
                instrument_keys
            )
            
            # Map back to symbols
            result = {}
            for key, value in data.items():
                symbol = key.split(":")[1]
                result[symbol] = value["last_price"]
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching multiple LTP: {e}")
            return {}
    
    async def get_multiple_ohlc(self, symbols: List[str], exchange: str = "NSE") -> Dict[str, Dict[str, Any]]:
        """
        Get OHLC data for multiple stocks at once (batch operation).
        
        Args:
            symbols: List of stock symbols
            exchange: Exchange (NSE, BSE)
            
        Returns:
            Dict mapping symbol to OHLC data
        """
        if not self.kite:
            logger.warning("Zerodha client not initialized")
            return {}
        
        try:
            await self._ensure_cache_initialized(exchange)
            
            instrument_keys = [f"{exchange}:{sym.upper()}" for sym in symbols]
            
            # Fetch OHLC for all symbols in one API call
            data = await asyncio.to_thread(
                self.kite.ohlc,
                instrument_keys
            )
            
            # Map back to symbols with calculated metrics
            result = {}
            for key, info in data.items():
                symbol = key.split(":")[1]
                ohlc = info["ohlc"]
                
                # Calculate change
                change = info["last_price"] - ohlc["close"]
                change_percent = (change / ohlc["close"]) * 100 if ohlc["close"] != 0 else 0
                
                result[symbol] = {
                    "symbol": symbol,
                    "last_price": info["last_price"],
                    "open": ohlc["open"],
                    "high": ohlc["high"],
                    "low": ohlc["low"],
                    "close": ohlc["close"],
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "volume": info.get("volume", 0)
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching multiple OHLC: {e}")
            return {}



# Singleton instance
_zerodha_client_instance: Optional[ZerodhaClient] = None


def get_zerodha_client() -> ZerodhaClient:
    """Get singleton Zerodha client instance."""
    global _zerodha_client_instance
    if _zerodha_client_instance is None:
        _zerodha_client_instance = ZerodhaClient()
    return _zerodha_client_instance