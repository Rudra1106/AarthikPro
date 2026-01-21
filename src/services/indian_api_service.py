"""
Indian API Service - News caching layer

Focused on NEWS ONLY:
- Market news (6-hour cache)
- Company news (6-hour cache)
- On-demand fetching for market overview queries
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class IndianAPIService:
    """Service layer with Redis caching for Indian API news."""
    
    def __init__(self):
        from src.data.redis_client import get_redis_cache
        from src.data.indian_api_client import get_indian_api_client
        
        self.redis = get_redis_cache()
        self.api = get_indian_api_client()
    
    async def get_market_news(self, limit: int = 20, force_refresh: bool = False) -> List[Dict]:
        """
        Get market news with 6-hour Redis cache.
        
        Args:
            limit: Number of news items (default: 20)
            force_refresh: Bypass cache and fetch fresh
        
        Returns:
            List of news items with title, description, source, url, published_at
        """
        cache_key = f"indian_api:news:market:{limit}"
        
        # Try cache first (unless force refresh)
        if not force_refresh:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    logger.info(f"✅ Cache HIT: Market news ({len(cached)} items)")
                    return cached
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
        
        # Fetch from API
        logger.info(f"📡 Fetching market news from Indian API (limit: {limit})...")
        news = await self.api.get_market_news(page_no=1, limit=limit)
        
        if news:
            # Cache for 6 hours (21600 seconds)
            try:
                await self.redis.set(cache_key, news, ttl=21600)
                logger.info(f"📦 Cached market news: {len(news)} items (TTL: 6 hours)")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
        else:
            logger.warning("No news fetched from Indian API")
        
        return news
    
    async def get_company_news(self, symbol: str, limit: int = 10, force_refresh: bool = False) -> List[Dict]:
        """
        Get company-specific news with 6-hour Redis cache.
        
        Args:
            symbol: Stock symbol (e.g., "TCS")
            limit: Number of news items
            force_refresh: Bypass cache
        
        Returns:
            List of company-specific news items
        """
        cache_key = f"indian_api:news:company:{symbol}:{limit}"
        
        # Try cache first
        if not force_refresh:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    logger.info(f"✅ Cache HIT: {symbol} news ({len(cached)} items)")
                    return cached
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
        
        # TODO: Implement company news endpoint when available
        # For now, return empty list
        logger.info(f"Company news endpoint not yet implemented for {symbol}")
        news = []
        
        if news:
            try:
                await self.redis.set(cache_key, news, ttl=21600)
                logger.info(f"📦 Cached {symbol} news: {len(news)} items")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
        
        return news
    
    async def clear_news_cache(self):
        """Clear all news cache."""
        try:
            keys = await self.redis.keys("indian_api:news:*")
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"🗑️ Cleared {len(keys)} news cache keys")
            else:
                logger.info("No news cache to clear")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            market_news_key = "indian_api:news:market:20"
            ttl = await self.redis.ttl(market_news_key)
            
            return {
                "market_news_cached": ttl > 0,
                "market_news_ttl_seconds": ttl if ttl > 0 else 0,
                "market_news_ttl_minutes": round(ttl / 60, 1) if ttl > 0 else 0,
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}


# Singleton instance
_service: Optional[IndianAPIService] = None


def get_indian_api_service() -> IndianAPIService:
    """Get singleton Indian API service instance."""
    global _service
    if _service is None:
        _service = IndianAPIService()
    return _service
