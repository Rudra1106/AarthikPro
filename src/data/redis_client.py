"""
Redis cache client for AarthikAI chatbot.

Provides async caching for:
- OHLC data (5-min TTL)
- LTP data (1-min TTL)
- Instrument tokens (24-hour TTL)
- Market overview (5-min TTL)
"""

import redis.asyncio as redis
import json
import logging
from typing import Optional, Any, List
from src.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Async Redis cache client.
    
    Features:
    - JSON serialization
    - TTL support
    - Automatic connection management
    - Graceful fallback on errors
    """
    
    def __init__(self):
        self.redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
        self._redis: Optional[redis.Redis] = None
        self._connected = False
    
    async def _ensure_connected(self):
        """Ensure Redis connection is established."""
        if self._redis is None:
            try:
                self._redis = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=10,  # Increased for cloud Redis
                    socket_timeout=10,          # Increased for cloud Redis
                    max_connections=10,  # Optimized for production (reduced from 20)
                )
                # Test connection
                await self._redis.ping()
                self._connected = True
                logger.info("Redis connection established (pool size: 10)")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Cache disabled.")
                self._connected = False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self._connected:
            await self._ensure_connected()
        
        if not self._connected:
            return None
        
        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 5 min)
        """
        if not self._connected:
            await self._ensure_connected()
        
        if not self._connected:
            return
        
        try:
            await self._redis.setex(
                key,
                ttl,
                json.dumps(value, default=str)  # Handle datetime, etc.
            )
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
    
    async def set_smart(self, key: str, value: Any, symbol: str = None):
        """
        Set value with smart TTL based on asset popularity.
        
        Hot assets (Nifty 50 stocks) get longer cache (10 min).
        Regular stocks get 5 min cache.
        LTP gets 1 min cache.
        
        Args:
            key: Cache key
            value: Value to cache
            symbol: Stock symbol (for hot asset detection)
        """
        # Hot assets list (Nifty 50 top stocks)
        HOT_ASSETS = [
            "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
            "BHARTIARTL", "ITC", "SBIN", "HINDUNILVR", "LT",
            "KOTAKBANK", "AXISBANK", "WIPRO", "ASIANPAINT", "MARUTI",
            "TITAN", "ULTRACEMCO", "SUNPHARMA", "NESTLEIND", "BAJFINANCE",
            "NIFTY 50", "SENSEX", "NIFTY BANK"
        ]
        
        # Determine TTL
        if symbol and symbol.upper() in HOT_ASSETS:
            ttl = 600  # 10 minutes for hot assets
        elif "ohlc:" in key:
            ttl = 300  # 5 minutes for OHLC
        elif "ltp:" in key:
            ttl = 60   # 1 minute for LTP
        elif "instrument_token:" in key:
            ttl = 86400  # 24 hours for instrument tokens
        else:
            ttl = 300  # Default 5 minutes
        
        await self.set(key, value, ttl=ttl)
    
    async def delete(self, key: str):
        """Delete key from cache."""
        if not self._connected:
            return
        
        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._connected:
            return False
        
        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "ohlc:*")
            
        Returns:
            Number of keys deleted
        """
        if not self._connected:
            return 0
        
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Redis DELETE_PATTERN error for {pattern}: {e}")
            return 0
    
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self._connected:
            return {"connected": False}
        
        try:
            info = await self._redis.info("stats")
            return {
                "connected": True,
                "total_keys": await self._redis.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0) / max(
                    info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1
                )
            }
        except Exception as e:
            logger.error(f"Redis STATS error: {e}")
            return {"connected": False, "error": str(e)}
    
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._connected = False


# Singleton instance
_redis_cache_instance: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """Get singleton Redis cache instance."""
    global _redis_cache_instance
    if _redis_cache_instance is None:
        _redis_cache_instance = RedisCache()
    return _redis_cache_instance
