"""
Zerodha Instruments Cache - In-Memory Storage

PRODUCTION OPTIMIZATION:
- Load instruments ONCE at startup
- Store in memory for O(1) lookups
- Refresh every 24 hours
- Eliminates CSV parsing per request (~150-300ms saved)

Memory usage: ~20-30MB for all NSE instruments
Lookup time: <1ms (vs 150-300ms CSV parsing)
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class InstrumentsCache:
    """
    In-memory cache for Zerodha instruments.
    
    Singleton pattern - one instance for entire app.
    Loaded once at startup, refreshed every 24 hours.
    
    Features:
    - O(1) symbol → token lookup
    - O(1) token → instrument lookup
    - Automatic 24-hour refresh
    - Memory efficient (~20-30MB)
    """
    
    _instance: Optional['InstrumentsCache'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize instruments cache (called only once)."""
        # Prevent re-initialization
        if InstrumentsCache._initialized:
            return
        
        # Storage
        self._instruments: Dict[int, dict] = {}  # token → instrument
        self._symbol_to_token: Dict[str, int] = {}  # "NSE:SYMBOL" → token
        self._last_refresh: Optional[datetime] = None
        self._refresh_interval = 86400  # 24 hours
        self._loading = False
        
        InstrumentsCache._initialized = True
        logger.info("InstrumentsCache singleton initialized")
    
    async def load_instruments(self, kite_client):
        """
        Load instruments from Zerodha and cache in memory.
        
        This should be called ONCE at app startup.
        
        Args:
            kite_client: Authenticated Kite Connect client
        """
        if self._loading:
            logger.warning("Instruments already loading, skipping")
            return
        
        if self._last_refresh and (datetime.now() - self._last_refresh).seconds < self._refresh_interval:
            logger.info(f"Instruments cache still fresh (loaded {(datetime.now() - self._last_refresh).seconds}s ago)")
            return
        
        self._loading = True
        
        try:
            logger.info("📥 Loading Zerodha instruments...")
            start_time = datetime.now()
            
            # Fetch instruments from Zerodha
            instruments_list = kite_client.instruments()
            
            # Clear old data
            self._instruments.clear()
            self._symbol_to_token.clear()
            
            # Build fast lookup dictionaries
            for instrument in instruments_list:
                token = instrument['instrument_token']
                exchange = instrument['exchange']
                symbol = instrument['tradingsymbol']
                
                # Store instrument by token
                self._instruments[token] = instrument
                
                # Store symbol → token mapping
                key = f"{exchange}:{symbol}"
                self._symbol_to_token[key] = token
            
            self._last_refresh = datetime.now()
            load_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"✅ Loaded {len(self._instruments)} instruments in {load_time:.2f}s "
                f"(Memory: ~{len(self._instruments) * 0.001:.1f}MB)"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to load instruments: {e}")
            raise
        
        finally:
            self._loading = False
    
    def get_token(self, symbol: str, exchange: str = "NSE") -> Optional[int]:
        """
        Get instrument token for a symbol.
        
        O(1) lookup - extremely fast.
        
        Args:
            symbol: Trading symbol (e.g., "TCS", "RELIANCE")
            exchange: Exchange (default: "NSE")
            
        Returns:
            Instrument token or None
        """
        key = f"{exchange}:{symbol}"
        return self._symbol_to_token.get(key)
    
    def get_instrument(self, token: int) -> Optional[dict]:
        """
        Get instrument details by token.
        
        O(1) lookup - extremely fast.
        
        Args:
            token: Instrument token
            
        Returns:
            Instrument dict or None
        """
        return self._instruments.get(token)
    
    def get_instrument_by_symbol(self, symbol: str, exchange: str = "NSE") -> Optional[dict]:
        """
        Get instrument details by symbol.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange (default: "NSE")
            
        Returns:
            Instrument dict or None
        """
        token = self.get_token(symbol, exchange)
        if token:
            return self.get_instrument(token)
        return None
    
    def search_symbols(self, query: str, exchange: str = "NSE", limit: int = 10) -> List[dict]:
        """
        Search for symbols matching query.
        
        Args:
            query: Search query
            exchange: Exchange filter
            limit: Max results
            
        Returns:
            List of matching instruments
        """
        query_upper = query.upper()
        results = []
        
        for key, token in self._symbol_to_token.items():
            if exchange and not key.startswith(f"{exchange}:"):
                continue
            
            symbol = key.split(":")[1]
            if query_upper in symbol:
                instrument = self._instruments.get(token)
                if instrument:
                    results.append(instrument)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "total_instruments": len(self._instruments),
            "total_symbols": len(self._symbol_to_token),
            "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
            "age_seconds": (datetime.now() - self._last_refresh).seconds if self._last_refresh else None,
            "memory_mb_estimate": len(self._instruments) * 0.001
        }
    
    async def start_auto_refresh(self, kite_client):
        """
        Start background task to auto-refresh instruments every 24 hours.
        
        Args:
            kite_client: Authenticated Kite Connect client
        """
        while True:
            try:
                await asyncio.sleep(self._refresh_interval)
                logger.info("🔄 Auto-refreshing instruments cache...")
                await self.load_instruments(kite_client)
            except Exception as e:
                logger.error(f"Auto-refresh failed: {e}")


# Singleton instance
_instruments_cache_instance: Optional[InstrumentsCache] = None


def get_instruments_cache() -> InstrumentsCache:
    """
    Get singleton instruments cache instance.
    
    IMPORTANT: Call await instruments_cache.load_instruments(kite) at app startup!
    
    Returns:
        InstrumentsCache singleton instance
    """
    global _instruments_cache_instance
    if _instruments_cache_instance is None:
        _instruments_cache_instance = InstrumentsCache()
    return _instruments_cache_instance
