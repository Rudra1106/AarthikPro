"""
Perplexity API client for real-time news and web search.
"""
import asyncio
from typing import List, Dict, Any, Optional
import httpx

from src.config import settings


class PerplexityClient:
    """
    Perplexity API client for news and web search.
    
    Optimizations:
    - Only use for time-sensitive queries (news, events)
    - Cache results to minimize API costs
    - Fallback to vector DB for older news
    """
    
    def __init__(self):
        self.api_key = settings.perplexity_api_key
        self.base_url = "https://api.perplexity.ai"
        
        # Sonar models for different use cases
        self.news_model = "sonar"  # For news queries
        self.search_model = "sonar-pro"  # For deep research
    
    async def search_news(
        self,
        query: str,
        recency_filter: str = "week",
        max_results: int = 5,
        enable_search_classifier: bool = True
    ) -> Dict[str, Any]:
        """
        Search for recent news using Perplexity Sonar.
        
        Uses search classifier to intelligently decide when to search the web.
        
        Args:
            query: Search query
            recency_filter: Time filter (day, week, month, year)
            max_results: Maximum number of results
            enable_search_classifier: Let AI decide if web search is needed
            
        Returns:
            Search results with citations
        """
        if not self.api_key:
            return {"answer": "", "citations": [], "error": "Perplexity API key not configured"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.news_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a financial news analyst. Provide concise, factual summaries with sources."
                            },
                            {
                                "role": "user",
                                "content": query
                            }
                        ],
                        "max_tokens": 500,
                        "temperature": 0.2,
                        "search_recency_filter": recency_filter,
                        "return_citations": True,
                        "return_images": False,
                        "enable_search_classifier": enable_search_classifier  # NEW: Intelligent search control
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "answer": data["choices"][0]["message"]["content"],
                    "citations": data.get("citations", []),
                    "model": data.get("model", self.news_model)
                }
            
            except httpx.HTTPError as e:
                return {
                    "answer": "",
                    "citations": [],
                    "error": f"Perplexity API error: {str(e)}"
                }
    
    async def deep_research(
        self,
        query: str,
        focus_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Deep research using Perplexity Sonar Pro.
        
        Args:
            query: Research query
            focus_domains: Optional list of domains to focus on
            
        Returns:
            Comprehensive research results
        """
        if not self.api_key:
            return {"answer": "", "citations": [], "error": "Perplexity API key not configured"}
        
        # Add domain focus to query if provided
        enhanced_query = query
        if focus_domains:
            domain_str = ", ".join(focus_domains)
            enhanced_query = f"{query} (focus on sources from: {domain_str})"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.search_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a financial research analyst. Provide comprehensive, well-sourced analysis."
                            },
                            {
                                "role": "user",
                                "content": enhanced_query
                            }
                        ],
                        "max_tokens": 1000,
                        "temperature": 0.3,
                        "return_citations": True
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "answer": data["choices"][0]["message"]["content"],
                    "citations": data.get("citations", []),
                    "model": data.get("model", self.search_model)
                }
            
            except httpx.HTTPError as e:
                return {
                    "answer": "",
                    "citations": [],
                    "error": f"Perplexity API error: {str(e)}"
                }
    
    async def search_indian_stock(
        self,
        symbol: str,
        query_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Search for Indian stock with NSE/BSE context.
        
        Args:
            symbol: Stock symbol (e.g., "TMPV", "RELIANCE")
            query_type: Type of query (comprehensive, price, fundamentals, news)
            
        Returns:
            Search results with Indian market context
        """
        # Build India-specific query
        if query_type == "comprehensive":
            query = f"""
Provide comprehensive information about {symbol} stock on Indian stock exchanges (NSE/BSE):

1. Current stock price and 52-week range
2. Market capitalization in crores (₹)
3. P/E ratio and dividend yield
4. Recent quarterly financial results
5. Latest news and developments
6. Sector and industry classification
7. Company overview

Focus on Indian exchanges (NSE/BSE). Use Indian number formatting (lakhs/crores). Include recent data from December 2024.
"""
        elif query_type == "price":
            query = f"Current stock price of {symbol} on NSE/BSE India, 52-week high/low, market cap in crores, December 2024"
        elif query_type == "fundamentals":
            query = f"Financial fundamentals of {symbol} stock India: P/E ratio, revenue, profit, debt-to-equity, ROE, latest quarterly results"
        else:  # news
            query = f"Latest news and developments about {symbol} stock India in last 7 days, December 2024"
        
        # Use deep research with focus on Indian sources
        return await self.deep_research(
            query,
            focus_domains=[
                "nseindia.com",
                "bseindia.com",
                "moneycontrol.com",
                "economictimes.indiatimes.com",
                "livemint.com",
                "business-standard.com"
            ]
        )
    
    async def get_company_news(
        self,
        company: str,
        days: int = 7,
        enable_search_classifier: bool = True
    ) -> Dict[str, Any]:
        """
        Get recent news for a specific company.
        
        Args:
            company: Company name or symbol
            days: Number of days to look back
            enable_search_classifier: Let AI decide if web search is needed
            
        Returns:
            Recent news summary
        """
        recency = "week" if days <= 7 else "month"
        query = f"Latest news and updates about {company} stock India NSE BSE"
        
        return await self.search_news(
            query,
            recency_filter=recency,
            enable_search_classifier=enable_search_classifier
        )
    
    async def web_search(
        self,
        query: str,
        country: str = "IN",
        domain_filter: List[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Perform web search using Perplexity Search API.
        
        Returns structured results with title, url, snippet, date.
        Optimized for India-specific financial data.
        
        Args:
            query: Search query
            country: ISO country code (default: IN for India)
            domain_filter: List of domains to prioritize
            max_results: Maximum number of results
            
        Returns:
            Dict with results list and query_id
        """
        if not self.api_key:
            return {"results": [], "error": "Perplexity API key not configured"}
        
        # Default to India-specific financial domains
        if not domain_filter:
            domain_filter = [
                "nseindia.com",
                "bseindia.com",
                "moneycontrol.com",
                "economictimes.indiatimes.com",
                "livemint.com",
                "business-standard.com"
            ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/search",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": query,
                        "country": country,
                        "search_domain_filter": domain_filter,
                        "max_results": max_results
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                return {
                    "results": data.get("results", []),
                    "query_id": data.get("id"),
                    "query": query
                }
                
            except httpx.HTTPStatusError as e:
                return {
                    "results": [],
                    "error": f"HTTP {e.response.status_code}: {e.response.text}",
                    "query": query
                }
            except Exception as e:
                return {
                    "results": [],
                    "error": str(e),
                    "query": query
                }
    
    @staticmethod
    def build_market_news_query(date_str: str = "today", focus: str = "general") -> str:
        """
        Build targeted news query for Indian markets.
        
        Args:
            date_str: Time reference (today, yesterday, this week)
            focus: Focus area (general, fii_dii, sectors, indices)
            
        Returns:
            Optimized query string for Perplexity
        """
        base_sites = "site:moneycontrol.com OR site:economictimes.com OR site:livemint.com"
        
        if focus == "fii_dii":
            return f"FII DII institutional flows Indian stock market {date_str} {base_sites}"
        elif focus == "sectors":
            return f"Sector performance Indian stock market {date_str} IT banking auto pharma {base_sites}"
        elif focus == "indices":
            return f"Nifty Sensex Bank Nifty index performance {date_str} {base_sites}"
        else:  # general
            return f"Top Indian stock market headlines {date_str} Nifty Sensex FII DII {base_sites}"


# Singleton instance
_perplexity_client_instance: Optional[PerplexityClient] = None


def get_perplexity_client() -> PerplexityClient:
    """Get singleton Perplexity client instance."""
    global _perplexity_client_instance
    if _perplexity_client_instance is None:
        _perplexity_client_instance = PerplexityClient()
    return _perplexity_client_instance
