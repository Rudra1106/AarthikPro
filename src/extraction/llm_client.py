"""
OpenRouter LLM Client with Cost Optimization
Provides selective LLM usage with caching and cost tracking.
"""

import os
import hashlib
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import openai
from dotenv import load_dotenv

load_dotenv()


class LLMCostTracker:
    """Track LLM usage and costs."""
    
    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0.0
        self.calls_made = 0
        self.cache_hits = 0
        
        # Model pricing (per 1M tokens) - Updated for OpenRouter
        self.pricing = {
            "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
        }
    
    def log_call(self, model: str, input_tokens: int, output_tokens: int):
        """Log an LLM call."""
        self.calls_made += 1
        self.total_tokens += input_tokens + output_tokens
        
        # Calculate cost
        pricing = self.pricing.get(model, {"input": 0.10, "output": 0.40})
        cost = (input_tokens / 1_000_000 * pricing["input"] + 
                output_tokens / 1_000_000 * pricing["output"])
        self.total_cost += cost
    
    def log_cache_hit(self):
        """Log a cache hit."""
        self.cache_hits += 1
    
    def summary(self) -> str:
        """Get cost summary."""
        cache_rate = (self.cache_hits / (self.calls_made + self.cache_hits) * 100 
                     if (self.calls_made + self.cache_hits) > 0 else 0)
        
        return f"""
LLM Cost Summary:
  Total Calls: {self.calls_made}
  Cache Hits: {self.cache_hits} ({cache_rate:.1f}% cache rate)
  Total Tokens: {self.total_tokens:,}
  Total Cost: ${self.total_cost:.4f}
  Avg Cost/Call: ${self.total_cost/self.calls_made:.4f} if self.calls_made > 0 else $0
"""


class OpenRouterClient:
    """
    Cost-optimized OpenRouter client with caching.
    """
    
    def __init__(self, cache_dir: str = "data/llm_cache"):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")
        
        # Configure OpenAI client for OpenRouter
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        
        # Setup cache
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cost tracker
        self.cost_tracker = LLMCostTracker()
        
        # Default model (OpenRouter)
        self.default_model = "openai/gpt-4o-mini"
    
    def _get_cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key from prompt and model."""
        content = f"{model}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """Get response from cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                data = json.load(f)
                self.cost_tracker.log_cache_hit()
                return data['response']
        return None
    
    def _save_to_cache(self, cache_key: str, response: str):
        """Save response to cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        with open(cache_file, 'w') as f:
            json.dump({'response': response}, f)
    
    def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.1,
        use_cache: bool = True
    ) -> str:
        """
        Get LLM completion with caching.
        
        Args:
            prompt: The prompt to send
            model: Model to use (default: gemini-flash-1.5)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            use_cache: Whether to use caching
            
        Returns:
            LLM response text
        """
        model = model or self.default_model
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(prompt, model)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                return cached_response
        
        # Make API call
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract response
            result = response.choices[0].message.content
            
            # Log cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            self.cost_tracker.log_call(model, input_tokens, output_tokens)
            
            # Cache response
            if use_cache:
                self._save_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            print(f"LLM API Error: {e}")
            return ""
    
    def normalize_table(self, table_text: str, confidence: float = 0.0) -> Optional[str]:
        """
        Normalize table text using LLM (only if needed).
        
        Args:
            table_text: Raw table text
            confidence: Confidence in rule-based extraction (0-1)
            
        Returns:
            Normalized table text or None if not needed
        """
        # Only use LLM if confidence is low
        if confidence > 0.7:
            return None
        
        prompt = f"""Convert this financial table into a clear, normalized sentence format.

Table:
{table_text}

Instructions:
- Extract key metrics (revenue, growth, margins, etc.)
- Format as: "In FY[year], [metric] was [value], [metric] was [value]..."
- Keep all numbers and percentages
- Be concise and factual

Normalized text:"""
        
        return self.complete(prompt, max_tokens=500)
    
    def enhance_vertical(self, text: str, confidence: float = 0.0) -> Optional[Dict[str, Any]]:
        """
        Enhance vertical/segment detection using LLM (only if needed).
        
        Args:
            text: Text chunk
            confidence: Confidence in rule-based detection (0-1)
            
        Returns:
            Enhanced vertical info or None if not needed
        """
        # Only use LLM if confidence is low
        if confidence > 0.7:
            return None
        
        prompt = f"""Analyze this text for business segment/vertical information.

Text:
{text}

Instructions:
- Identify mentioned business segments (BFSI, Manufacturing, IT, Retail, etc.)
- Extract performance metrics (growth %, revenue, etc.)
- Return JSON format: {{"segments": [{{"name": "...", "metrics": "..."}}]}}

JSON response:"""
        
        response = self.complete(prompt, max_tokens=300)
        
        try:
            return json.loads(response)
        except:
            return None
    
    def classify_section(self, text: str) -> str:
        """
        Classify document section using LLM.
        
        Args:
            text: Text to classify
            
        Returns:
            Section name
        """
        prompt = f"""Classify this text into one of these sections:
- CEO Letter
- Chairman Letter
- Business Overview
- Financial Highlights
- Risk Factors
- Governance
- Other

Text (first 500 chars):
{text[:500]}

Section name (one word):"""
        
        return self.complete(prompt, max_tokens=50).strip()
    
    def get_cost_summary(self) -> str:
        """Get cost tracking summary."""
        return self.cost_tracker.summary()


# Global instance
_llm_client = None

def get_llm_client() -> OpenRouterClient:
    """Get global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenRouterClient()
    return _llm_client
