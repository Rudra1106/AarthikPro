"""
Indian API Client - Market news and data.

Provides access to Indian stock market news and data through the Indian API.
"""

import aiohttp
from typing import Dict, List, Any, Optional
from src.config import settings
import logging

logger = logging.getLogger(__name__)


class IndianAPIClient:
    """Client for Indian API market data and news."""
    
    def __init__(self):
        self.base_url = getattr(settings, 'indian_api_base_url', 'https://pro.indianapi.in')
        self.api_key = getattr(settings, 'indian_api_key', '')
        
        if not self.api_key:
            logger.warning("Indian API key not configured")
    
    async def get_market_news(self, page_no: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch latest market news from Indian API.
        
        Args:
            page_no: Page number (default: 1)
            limit: Number of news items to fetch (default: 20)
            
        Returns:
            List of news items with title, description, source, url, published_at
        """
        if not self.api_key:
            logger.error("Indian API key not configured")
            return []
        
        try:
            url = f"{self.base_url}/news?page_no={page_no}&size={limit}"
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Handle different response formats
                        if isinstance(data, dict):
                            news_items = data.get("news", data.get("data", []))
                        elif isinstance(data, list):
                            news_items = data
                        else:
                            logger.error(f"Unexpected response format: {type(data)}")
                            return []
                        
                        # Limit results
                        news_items = news_items[:limit]
                        
                        logger.info(f"✅ Fetched {len(news_items)} news items from Indian API")
                        return news_items
                    
                    elif response.status == 401:
                        logger.error("Indian API authentication failed - check API key")
                        return []
                    
                    elif response.status == 429:
                        logger.warning("Indian API rate limit exceeded")
                        return []
                    
                    else:
                        logger.error(f"Indian API error: {response.status}")
                        return []
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching news from Indian API: {e}")
            return []
        
        except Exception as e:
            logger.error(f"Failed to fetch news from Indian API: {e}")
            return []
    
    async def test_connection(self) -> bool:
        """
        Test connection to Indian API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            news = await self.get_market_news(limit=1)
            return len(news) > 0
        except Exception as e:
            logger.error(f"Indian API connection test failed: {e}")
            return False


# Singleton instance
_indian_api_client: Optional[IndianAPIClient] = None


def get_indian_api_client() -> IndianAPIClient:
    """Get singleton Indian API client instance."""
    global _indian_api_client
    if _indian_api_client is None:
        _indian_api_client = IndianAPIClient()
    return _indian_api_client
