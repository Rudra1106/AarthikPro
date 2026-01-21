"""
Query Normalizer - Convert casual queries into structured financial queries.

Uses OpenRouter GPT-4o-mini to rewrite ambiguous or casual queries
into specific, actionable financial queries that work better with
the intent classifier.

Examples:
    "How's it doing?" → "What is the current stock performance of TCS?"
    "Is it good?" → "Provide fundamental and technical analysis for RELIANCE"
    "Show me banks" → "List top performing banking sector stocks on NSE"
"""

import asyncio
import logging
import httpx
from typing import Optional, Dict, Any
from src.config import settings

logger = logging.getLogger(__name__)


class QueryNormalizer:
    """
    Normalize casual user queries into structured financial queries.
    
    Uses LLM (GPT-4o-mini via OpenRouter) for intelligent query rewriting.
    """
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = "openai/gpt-4o-mini"
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def is_ambiguous_or_casual(self, query: str) -> bool:
        """
        Check if query needs normalization.
        
        Args:
            query: User's query string
            
        Returns:
            True if query is ambiguous/casual and needs normalization
        """
        query_lower = query.lower().strip()
        
        # Has pronouns without clear context
        pronouns = ["it", "this", "that", "them", "they", "these", "those"]
        if any(word in query_lower.split() for word in pronouns):
            return True
        
        # Too short and vague (less than 3 words, no stock symbol)
        words = query_lower.split()
        if len(words) < 3:
            # Check if it has a stock symbol pattern (uppercase letters)
            import re
            if not re.search(r'\b[A-Z]{2,10}\b', query):
                return True
        
        # Vague question patterns
        vague_patterns = [
            "how's", "what's good", "show me", "any", "some",
            "is it", "are they", "should i", "can i",
            "tell me about", "what about"
        ]
        if any(pattern in query_lower for pattern in vague_patterns):
            return True
        
        # Just a single word (too vague)
        if len(words) == 1:
            return True
        
        return False
    
    async def normalize(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Normalize a casual query into a structured financial query.
        
        Args:
            query: User's original query
            context: Conversation context (last_stocks, last_intent, etc.)
            
        Returns:
            Normalized query string
        """
        # Skip normalization for clear queries
        if not self.is_ambiguous_or_casual(query):
            logger.info(f"Query is clear, skipping normalization: '{query}'")
            return query
        
        # Build context string
        context = context or {}
        context_str = ""
        
        if context.get("last_stocks"):
            context_str += f"\nLast mentioned stocks: {', '.join(context['last_stocks'][:3])}"
        
        if context.get("last_intent"):
            context_str += f"\nLast query type: {context['last_intent']}"
        
        # Build prompt
        prompt = f"""You are a financial query assistant. Rewrite the user's casual query into a specific, actionable financial query.

Rules:
1. If pronouns (it, this, that) are used, replace with the last mentioned stock or "Nifty 50" if no context
2. If no stock is mentioned, assume Indian stock market or Nifty 50
3. If no timeframe is mentioned, assume "current" or "today"
4. Add specific metrics when relevant (price, fundamentals, news, performance)
5. Keep it concise (one sentence, max 15 words)
6. Use proper stock symbols (TCS, RELIANCE, HDFCBANK)

Context:{context_str}

User Query: "{query}"

Rewritten Query (one line, specific, actionable):"""

        try:
            # Call OpenRouter API
            normalized = await self._call_llm(prompt)
            
            logger.info(f"Normalized: '{query}' → '{normalized}'")
            return normalized.strip()
            
        except Exception as e:
            logger.error(f"Query normalization failed: {e}")
            # Fallback to original query
            return query
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Call OpenRouter API with GPT-4o-mini.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            LLM response text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://aarthikai.com",  # Optional
            "X-Title": "AarthikAI"  # Optional
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a financial query rewriting assistant. Rewrite queries to be specific and actionable."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 50,  # Keep it short
            "temperature": 0.3,  # Low temperature for consistency
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]


# Singleton instance
_query_normalizer: Optional[QueryNormalizer] = None


def get_query_normalizer() -> QueryNormalizer:
    """Get singleton query normalizer instance."""
    global _query_normalizer
    if _query_normalizer is None:
        _query_normalizer = QueryNormalizer()
    return _query_normalizer
