"""
Indian Stock News Client - Fetch and cache daily news from IndianAPI.

This client:
1. Fetches news from https://stock.indianapi.in/news
2. Caches in Redis with 1-hour TTL (refreshes throughout the day)
3. Provides stock-specific news filtering
4. Gives the chatbot instant access to daily news context
"""
import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib

from src.config import settings

logger = logging.getLogger(__name__)

# API Configuration
INDIAN_API_URL = "https://stock.indianapi.in/news"
INDIAN_API_KEY = "sk-live-09fw82v2akFa2gd78cTwMJFrj92IaojE8EOmPRQu"  # From user request

# Cache configuration
NEWS_CACHE_KEY = "daily_news:all"
NEWS_CACHE_TTL = 3600  # 1 hour - refreshes throughout the day
STOCK_NEWS_PREFIX = "daily_news:stock:"


class IndianNewsClient:
    """
    Client to fetch and cache Indian stock market news.
    
    Features:
    - Fetches from IndianAPI.in
    - Caches in Redis for fast access
    - Filters news by stock symbol
    - Provides topic-based filtering
    """
    
    def __init__(self):
        self._redis = None
        self._last_fetch: Optional[datetime] = None
        self._news_cache: List[Dict[str, Any]] = []
    
    async def _get_redis(self):
        """Get Redis connection lazily."""
        if self._redis is None:
            try:
                from src.data.redis_client import get_redis_cache
                self._redis = get_redis_cache()
                # Ensure connected
                await self._redis._ensure_connected()
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
        return self._redis
    
    async def fetch_news(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch news from IndianAPI, with Redis caching.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            List of news items
        """
        # Try cache first
        if not force_refresh:
            cached = await self._get_cached_news()
            if cached:
                return cached
        
        # Fetch from API
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"X-Api-Key": INDIAN_API_KEY}
                async with session.get(INDIAN_API_URL, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        news = await response.json()
                        
                        # Process and enrich news items
                        processed_news = self._process_news(news)
                        
                        # Cache the news
                        await self._cache_news(processed_news)
                        
                        logger.info(f"Fetched {len(processed_news)} news items from IndianAPI")
                        return processed_news
                    else:
                        logger.error(f"IndianAPI returned status {response.status}")
                        return self._news_cache if self._news_cache else []
                        
        except Exception as e:
            logger.error(f"Error fetching news from IndianAPI: {e}")
            return self._news_cache if self._news_cache else []
    
    def _process_news(self, news: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and enrich news items.
        
        - Extract stock symbols mentioned
        - Normalize topics
        - Add metadata
        """
        processed = []
        
        # Common stock name to symbol mapping
        stock_mapping = {
            "tcs": "TCS", "tata consultancy": "TCS",
            "infosys": "INFY", "infy": "INFY",
            "reliance": "RELIANCE", "ril": "RELIANCE",
            "hdfc bank": "HDFCBANK", "hdfc": "HDFCBANK",
            "icici bank": "ICICIBANK", "icici": "ICICIBANK",
            "sbi": "SBIN", "state bank": "SBIN",
            "bharti airtel": "BHARTIARTL", "airtel": "BHARTIARTL",
            "tata power": "TATAPOWER",
            "tata motors": "TATAMOTORS",
            "mahindra": "M&M",
            "lupin": "LUPIN",
            "paytm": "PAYTM",
            "nestle": "NESTLEIND",
            "britannia": "BRITANNIA",
            "indusind": "INDUSINDBK",
            "kotak": "KOTAKBANK",
            "bajaj finance": "BAJFINANCE",
            "bajaj": "BAJFINANCE",
            "wipro": "WIPRO",
            "hcl tech": "HCLTECH", "hcl": "HCLTECH",
            "lt": "LT", "larsen": "LT",
            "asian paints": "ASIANPAINT",
            "maruti": "MARUTI",
            "sun pharma": "SUNPHARMA",
            "axis bank": "AXISBANK",
            "adani": "ADANIENT",
            "ioc": "IOC", "indian oil": "IOC",
            "ongc": "ONGC",
            "ntpc": "NTPC",
            "powergrid": "POWERGRID",
        }
        
        for item in news:
            # Extract stock symbols from title and summary
            text = (item.get("title", "") + " " + item.get("summary", "")).lower()
            
            mentioned_stocks = []
            for name, symbol in stock_mapping.items():
                if name in text:
                    if symbol not in mentioned_stocks:
                        mentioned_stocks.append(symbol)
            
            processed_item = {
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "url": item.get("url", ""),
                "source": item.get("source", "Unknown"),
                "pub_date": item.get("pub_date", ""),
                "topics": item.get("topics", []),
                "mentioned_stocks": mentioned_stocks,
                "image_url": item.get("image_url", ""),
            }
            processed.append(processed_item)
        
        return processed
    
    async def _get_cached_news(self) -> Optional[List[Dict[str, Any]]]:
        """Get news from Redis cache."""
        redis = await self._get_redis()
        if redis:
            try:
                cached = await redis.get(NEWS_CACHE_KEY)
                if cached:
                    # Redis client already deserializes JSON
                    self._news_cache = cached  # Update memory cache
                    logger.debug(f"Retrieved {len(cached)} news items from cache")
                    return cached
            except Exception as e:
                logger.warning(f"Error reading news cache: {e}")
        
        return None
    
    async def _cache_news(self, news: List[Dict[str, Any]]):
        """Cache news in Redis."""
        redis = await self._get_redis()
        if redis:
            try:
                await redis.set(NEWS_CACHE_KEY, news, NEWS_CACHE_TTL)
                
                # Also index by stock symbol for fast lookup
                stock_news_index: Dict[str, List[int]] = {}
                for idx, item in enumerate(news):
                    for stock in item.get("mentioned_stocks", []):
                        if stock not in stock_news_index:
                            stock_news_index[stock] = []
                        stock_news_index[stock].append(idx)
                
                # Cache stock indices
                for stock, indices in stock_news_index.items():
                    key = f"{STOCK_NEWS_PREFIX}{stock}"
                    await redis.set(key, indices, NEWS_CACHE_TTL)
                
                logger.debug(f"Cached news with {len(stock_news_index)} stock indices")
                
            except Exception as e:
                logger.warning(f"Error caching news: {e}")
        
        # Always update memory cache
        self._news_cache = news
        self._last_fetch = datetime.now()
    
    async def get_news_for_stock(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get news specifically mentioning a stock.
        
        Args:
            symbol: Stock symbol (e.g., "TCS", "INFY")
            
        Returns:
            List of relevant news items
        """
        # Ensure we have news
        all_news = await self.fetch_news()
        
        if not all_news:
            return []
        
        # Filter by symbol
        symbol_upper = symbol.upper()
        relevant = [
            item for item in all_news
            if symbol_upper in item.get("mentioned_stocks", [])
        ]
        
        # If no exact match, try fuzzy match in title/summary
        if not relevant:
            relevant = [
                item for item in all_news
                if symbol_upper.lower() in item.get("title", "").lower()
                or symbol_upper.lower() in item.get("summary", "").lower()
            ]
        
        return relevant[:5]  # Return top 5 most relevant
    
    async def get_news_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """
        Get news by topic.
        
        Topics include: Financial Results, ESG, Hiring, Business Expansion, 
        Emerging Tech, Procurement and Sales
        """
        all_news = await self.fetch_news()
        
        topic_lower = topic.lower()
        return [
            item for item in all_news
            if any(topic_lower in t.lower() for t in item.get("topics", []))
        ][:10]
    
    async def get_market_summary(self) -> str:
        """
        Get a quick market news summary for chatbot context.
        
        Returns a formatted string suitable for inclusion in LLM context.
        """
        news = await self.fetch_news()
        
        if not news:
            return "No recent market news available."
        
        # Get top 5 most relevant items
        top_news = news[:5]
        
        summary_parts = ["📰 **Today's Market News:**\n"]
        
        for item in top_news:
            title = item.get("title", "")[:80]
            source = item.get("source", "Unknown")
            stocks = ", ".join(item.get("mentioned_stocks", []))
            
            summary_parts.append(f"• **{title}** ({source})")
            if stocks:
                summary_parts.append(f"  *Stocks: {stocks}*")
        
        return "\n".join(summary_parts)
    
    async def get_context_for_query(self, query: str, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Get relevant news context for a user query.
        
        Args:
            query: User's question
            symbols: Stock symbols mentioned in query
            
        Returns:
            Dict with relevant news and formatted context
        """
        all_news = await self.fetch_news()
        relevant_news = []
        
        # If specific symbols, get their news
        if symbols:
            for symbol in symbols[:3]:  # Limit to 3 symbols
                stock_news = await self.get_news_for_stock(symbol)
                relevant_news.extend(stock_news)
        
        # Deduplicate
        seen_urls = set()
        unique_news = []
        for item in relevant_news:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                unique_news.append(item)
        
        # Format for LLM context
        if unique_news:
            context = "## Relevant Recent News\n\n"
            for item in unique_news[:5]:
                context += f"**{item['title']}** ({item['source']})\n"
                context += f"{item['summary']}\n\n"
        else:
            context = ""
        
        return {
            "news_items": unique_news[:5],
            "formatted_context": context,
            "total_available": len(all_news)
        }


# Singleton
_news_client: Optional[IndianNewsClient] = None


def get_indian_news_client() -> IndianNewsClient:
    """Get singleton news client."""
    global _news_client
    if _news_client is None:
        _news_client = IndianNewsClient()
    return _news_client


async def refresh_daily_news():
    """
    Refresh daily news cache.
    
    Call this on app startup and periodically.
    """
    client = get_indian_news_client()
    news = await client.fetch_news(force_refresh=True)
    logger.info(f"Refreshed daily news: {len(news)} items")
    return news
