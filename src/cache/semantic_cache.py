"""
Semantic Cache - Cache similar queries using embeddings.

Example:
- "What's TCS price?"
- "TCS current price"
- "Price of TCS"

All map to same cache entry using semantic similarity.
"""
import hashlib
import json
from typing import Optional, Dict, Any
import logging

from src.data.redis_client import get_redis_cache

logger = logging.getLogger(__name__)


class SemanticCache:
    """
    Semantic caching using query normalization and Redis.
    
    For MVP, we use simple query normalization instead of embeddings
    to avoid additional API calls. Can be upgraded to embedding-based
    similarity search later.
    
    Normalization rules:
    - Remove common words (what, is, the, etc.)
    - Lowercase
    - Sort remaining words
    - Hash for cache key
    """
    
    def __init__(self):
        self.redis = get_redis_cache()
        self.logger = logging.getLogger(__name__)
        
        # Common words to remove for normalization
        self.stop_words = {
            'what', 'is', 'the', 'a', 'an', 'of', 'for', 'in', 'on', 'at',
            'to', 'from', 'with', 'by', 'about', 'as', 'into', 'through',
            'me', 'show', 'tell', 'give', 'get', 'current', 'latest', 'recent'
        }
    
    async def get(self, query: str, intent: str = None) -> Optional[Dict[str, Any]]:
        """
        Get cached result for semantically similar query.
        
        Args:
            query: User query
            intent: Query intent (for better cache key)
            
        Returns:
            Cached result or None
        """
        # Normalize query to cache key
        cache_key = self._normalize_query_to_key(query, intent)
        
        # Try to get from Redis
        cached_result = await self.redis.get(cache_key)
        
        if cached_result:
            self.logger.info(f"Semantic cache HIT for query: {query[:50]}...")
            return cached_result
        
        self.logger.debug(f"Semantic cache MISS for query: {query[:50]}...")
        return None
    
    async def set(
        self,
        query: str,
        result: Dict[str, Any],
        intent: str = None,
        ttl: int = 300
    ):
        """
        Cache result with semantic indexing.
        
        Args:
            query: User query
            result: Result to cache
            intent: Query intent
            ttl: Time to live in seconds
        """
        # Normalize query to cache key
        cache_key = self._normalize_query_to_key(query, intent)
        
        # Store in Redis
        await self.redis.set(cache_key, result, ttl=ttl)
        
        self.logger.info(f"Cached result for query: {query[:50]}...")
    
    def _normalize_query_to_key(self, query: str, intent: str = None) -> str:
        """
        Normalize query to cache key.
        
        Args:
            query: User query
            intent: Query intent
            
        Returns:
            Cache key
        """
        # Lowercase
        normalized = query.lower()
        
        # Remove punctuation
        normalized = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in normalized)
        
        # Split into words
        words = normalized.split()
        
        # Remove stop words
        filtered_words = [w for w in words if w not in self.stop_words]
        
        # Sort words for consistency
        sorted_words = sorted(filtered_words)
        
        # Create base key
        base_key = '_'.join(sorted_words)
        
        # Add intent prefix if available
        if intent:
            base_key = f"{intent}:{base_key}"
        
        # Hash for fixed-length key
        key_hash = hashlib.md5(base_key.encode()).hexdigest()
        
        return f"semantic_cache:{key_hash}"
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Pattern to match (e.g., "semantic_cache:*")
            
        Returns:
            Number of keys deleted
        """
        return await self.redis.delete_pattern(pattern)
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        redis_stats = await self.redis.get_stats()
        
        return {
            "redis_connected": redis_stats.get("connected", False),
            "total_keys": redis_stats.get("total_keys", 0),
            "hit_rate": redis_stats.get("hit_rate", 0.0)
        }


# Singleton instance
_semantic_cache: Optional[SemanticCache] = None


def get_semantic_cache() -> SemanticCache:
    """Get singleton semantic cache instance."""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    return _semantic_cache
