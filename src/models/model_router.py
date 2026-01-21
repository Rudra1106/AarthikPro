"""
Model router for intelligent model selection based on query complexity.
"""
from typing import Optional, Dict, Any
from enum import Enum

from src.config import settings


class ModelTier(str, Enum):
    """Model tier based on capability, speed, and cost."""
    INSTANT = "instant"   # GPT-4o-mini - <1s, $0.15/1M tokens
    FAST = "fast"         # GPT-4o - 1-2s, $2.5/1M tokens  
    SMART = "smart"       # GPT-4.5 - 3-5s, $5/1M tokens
    COMPLEX = "complex"   # Claude 3.5 Sonnet - 5-10s, $15/1M tokens


class ModelRouter:
    """
    Intelligent model selection based on query complexity and requirements.
    
    Strategy:
    - INSTANT: Simple price lookups, greetings
    - FAST: News summaries, basic analysis
    - SMART: Market overviews, comparisons
    - COMPLEX: Deep fundamental analysis, multi-stock comparisons
    """
    
    def __init__(self):
        self.model_config = {
            ModelTier.INSTANT: {
                "name": "openai/gpt-4o-mini",
                "cost_per_1k_tokens": 0.00015,
                "max_tokens": 128000,
                "avg_latency_ms": 800,
                "use_cases": ["simple_price", "greeting", "cache_hit"]
            },
            ModelTier.FAST: {
                "name": "openai/gpt-4o",
                "cost_per_1k_tokens": 0.0025,
                "max_tokens": 128000,
                "avg_latency_ms": 1500,
                "use_cases": ["news", "technical", "general"]
            },
            ModelTier.SMART: {
                "name": settings.default_model,  # gpt-5.1-chat
                "cost_per_1k_tokens": 0.005,
                "max_tokens": 200000,
                "avg_latency_ms": 4000,
                "use_cases": ["market_overview", "fundamental", "comparison"]
            },
            ModelTier.COMPLEX: {
                "name": settings.complex_model,  # claude-3.5-sonnet
                "cost_per_1k_tokens": 0.015,
                "max_tokens": 200000,
                "avg_latency_ms": 8000,
                "use_cases": ["multi", "deep_analysis", "complex_reasoning"]
            }
        }
    
    def select_model(
        self,
        intent: str,
        query_length: int,
        context_length: int = 0,
        requires_reasoning: bool = False,
        has_market_data: bool = False
    ) -> Dict[str, Any]:
        """
        Select optimal model based on query characteristics.
        
        Args:
            intent: Query intent (market_data, news, fundamental, etc.)
            query_length: Length of user query in characters
            context_length: Length of retrieved context in characters
            requires_reasoning: Whether query requires multi-step reasoning
            has_market_data: Whether we already have market data from Zerodha
            
        Returns:
            Model configuration dict
        """
        # INSTANT tier: Simple price lookups
        if intent == "market_data" and query_length < 50 and has_market_data:
            tier = ModelTier.INSTANT  # <1s response
        
        # FAST tier: News, basic queries
        elif intent in ["news", "general"] or query_length < 30:
            tier = ModelTier.FAST  # 1-2s response
        
        # COMPLEX tier: Deep analysis, multi-intent
        elif intent == "multi" or requires_reasoning or "compare" in intent.lower():
            tier = ModelTier.COMPLEX  # 5-10s but highest quality
        
        # SMART tier: Market overview, fundamental analysis
        elif intent in ["market_overview", "fundamental"] or context_length > 5000:
            tier = ModelTier.SMART  # 3-5s balanced
        
        # Default: FAST for most queries
        else:
            tier = ModelTier.FAST
        
        config = self.model_config[tier].copy()
        config["tier"] = tier
        return config
    
    def estimate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate cost for a model call.
        
        Args:
            model_name: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        # Find model config
        for tier_config in self.model_config.values():
            if tier_config["name"] == model_name:
                cost_per_1k = tier_config["cost_per_1k_tokens"]
                total_tokens = input_tokens + output_tokens
                return (total_tokens / 1000) * cost_per_1k
        
        # Default estimate if model not found
        return (input_tokens + output_tokens) / 1000 * 0.0002
    
    def get_fallback_model(self, current_model: str) -> Optional[str]:
        """
        Get fallback model if current model fails.
        
        Fallback chain: Complex → Default → Simple
        """
        if current_model == settings.complex_model:
            return settings.default_model
        elif current_model == settings.default_model:
            return settings.simple_model
        else:
            return None


# Singleton instance
_model_router_instance: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get singleton model router instance."""
    global _model_router_instance
    if _model_router_instance is None:
        _model_router_instance = ModelRouter()
    return _model_router_instance
