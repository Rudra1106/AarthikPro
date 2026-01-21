"""
LLM-based symbol extractor with caching for unknown stocks.
Fallback when hardcoded aliases don't match.
"""
import json
import logging
from typing import List, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings

logger = logging.getLogger(__name__)


class LLMSymbolExtractor:
    """Extract stock symbols using LLM with Redis caching for speed."""
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "openai/gpt-4o-mini"  # Fast and cheap
        self.cache = None
        
        # Try to initialize Redis cache
        try:
            from src.data.redis_client import get_redis_client
            self.cache = get_redis_client()
        except Exception as e:
            logger.warning(f"Redis cache not available for symbol extraction: {e}")
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query."""
        return f"symbol_extract:{query.lower().strip()}"
    
    async def _get_cached_symbols(self, query: str) -> Optional[List[str]]:
        """Get cached symbols if available."""
        if not self.cache:
            return None
        
        try:
            cache_key = self._get_cache_key(query)
            cached = await self.cache.get(cache_key)
            if cached:
                logger.info(f"✅ Symbol cache hit for: {query}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    async def _cache_symbols(self, query: str, symbols: List[str]):
        """Cache extracted symbols."""
        if not self.cache:
            return
        
        try:
            cache_key = self._get_cache_key(query)
            # Cache for 7 days (symbols don't change often)
            await self.cache.setex(cache_key, 604800, json.dumps(symbols))
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
    async def extract_symbols(self, query: str) -> List[str]:
        """
        Extract NSE stock symbols from query using LLM.
        
        Returns empty list if no symbols found or on error.
        """
        # Check cache first
        cached = await self._get_cached_symbols(query)
        if cached is not None:
            return cached
        
        try:
            # Prepare prompt
            prompt = f"""Extract NSE stock symbols from this query: "{query}"

Rules:
- Return only valid NSE symbols (uppercase)
- For company names, return the NSE symbol (e.g., "nalco" → "NATIONALUM")
- Return empty list if no stocks mentioned
- Return JSON only, no explanation

Examples:
- "price of nalco" → {{"symbols": ["NATIONALUM"]}}
- "compare tcs and infosys" → {{"symbols": ["TCS", "INFY"]}}
- "market overview" → {{"symbols": []}}
- "zomato stock" → {{"symbols": ["ZOMATO"]}}

Query: "{query}"
Return JSON:"""

            # Call LLM
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0,
                        "max_tokens": 100
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"LLM symbol extraction failed: {response.status_code}")
                    return []
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Parse JSON response
                try:
                    # Extract JSON from response (handle markdown code blocks)
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    data = json.loads(content)
                    symbols = data.get("symbols", [])
                    
                    # Cache the result
                    await self._cache_symbols(query, symbols)
                    
                    logger.info(f"✅ LLM extracted symbols: {symbols} from '{query}'")
                    return symbols
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response: {content}")
                    return []
        
        except Exception as e:
            logger.error(f"LLM symbol extraction error: {e}")
            return []


# Singleton instance
_extractor_instance: Optional[LLMSymbolExtractor] = None


def get_llm_symbol_extractor() -> LLMSymbolExtractor:
    """Get singleton LLM symbol extractor instance."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = LLMSymbolExtractor()
    return _extractor_instance
