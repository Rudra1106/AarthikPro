"""
Search Router - Intelligent routing to optimal data layers.

Routes queries to the right data sources based on intent, minimizing
unnecessary API calls and optimizing for latency.
"""
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from src.intent_classifier import QueryIntent

logger = logging.getLogger(__name__)


class Layer(str, Enum):
    """Data layer types."""
    ZERODHA = "zerodha"        # Live market data
    MONGODB = "mongodb"        # Structured financial data
    PINECONE = "pinecone"      # Vector embeddings
    NSE = "nse"                # NSE official data
    PERPLEXITY = "perplexity"  # Web search


@dataclass
class SearchPlan:
    """Search execution plan."""
    layers: List[Layer]
    max_web_calls: int
    cache_ttl: int  # seconds
    priority_order: List[Layer]  # Order to execute
    
    def to_dict(self) -> dict:
        return {
            "layers": [layer.value for layer in self.layers],
            "max_web_calls": self.max_web_calls,
            "cache_ttl": self.cache_ttl,
            "priority_order": [layer.value for layer in self.priority_order]
        }


class SearchRouter:
    """
    Route queries to optimal data layers based on intent.
    
    Rules:
    - Price queries → Zerodha only (no web search)
    - Fundamental queries → MongoDB + Pinecone (we have all data)
    - News queries → Perplexity (but check cache first!)
    - Market overview → Zerodha + NSE + 1 web search max
    - Sector queries → Zerodha + MongoDB
    - Technical queries → Zerodha only
    
    Budget Constraints:
    - Max 1 web call per query (Perplexity)
    - Prefer structured data over web search
    - Always check cache first
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def plan_search(
        self,
        intent: QueryIntent,
        symbols: List[str] = None,
        has_cache: bool = False
    ) -> SearchPlan:
        """
        Create search plan based on intent and context.
        
        Args:
            intent: Query intent
            symbols: Stock symbols if any
            has_cache: Whether cache hit exists
            
        Returns:
            SearchPlan with layers, budgets, and priorities
        """
        symbols = symbols or []
        
        # MARKET_DATA: Live prices from Zerodha only
        if intent == QueryIntent.MARKET_DATA:
            return SearchPlan(
                layers=[Layer.ZERODHA],
                max_web_calls=0,
                cache_ttl=60,  # 1 minute for live prices
                priority_order=[Layer.ZERODHA]
            )
        
        # TECHNICAL: Zerodha for OHLC data
        elif intent == QueryIntent.TECHNICAL:
            return SearchPlan(
                layers=[Layer.ZERODHA],
                max_web_calls=0,
                cache_ttl=300,  # 5 minutes
                priority_order=[Layer.ZERODHA]
            )
        
        # PRICE_CHECK: Zerodha only, no web calls (NEW - optimized for simple price queries)
        elif intent == QueryIntent.PRICE_CHECK:
            return SearchPlan(
                layers=[Layer.ZERODHA],
                max_web_calls=0,  # NO web calls for simple price queries
                cache_ttl=60,  # 1 minute cache for live prices
                priority_order=[Layer.ZERODHA]
            )
        
        # FUNDAMENTAL: MongoDB + Pinecone (no web needed)
        elif intent == QueryIntent.FUNDAMENTAL:
            return SearchPlan(
                layers=[Layer.MONGODB, Layer.PINECONE],
                max_web_calls=0,
                cache_ttl=3600,  # 1 hour
                priority_order=[Layer.MONGODB, Layer.PINECONE]
            )
        
        # FINANCIAL_METRICS: MongoDB only
        elif intent == QueryIntent.FINANCIAL_METRICS:
            return SearchPlan(
                layers=[Layer.MONGODB],
                max_web_calls=0,
                cache_ttl=3600,
                priority_order=[Layer.MONGODB]
            )
        
        # CORPORATE_ACTIONS: MongoDB only
        elif intent == QueryIntent.CORPORATE_ACTIONS:
            return SearchPlan(
                layers=[Layer.MONGODB],
                max_web_calls=0,
                cache_ttl=86400,  # 24 hours
                priority_order=[Layer.MONGODB]
            )
        
        # TREND_ANALYSIS: MongoDB for historical data
        elif intent == QueryIntent.TREND_ANALYSIS:
            return SearchPlan(
                layers=[Layer.MONGODB],
                max_web_calls=0,
                cache_ttl=3600,
                priority_order=[Layer.MONGODB]
            )
        
        # SECTOR_PERFORMANCE: Zerodha + MongoDB
        elif intent == QueryIntent.SECTOR_PERFORMANCE:
            return SearchPlan(
                layers=[Layer.ZERODHA, Layer.MONGODB],
                max_web_calls=0,
                cache_ttl=300,
                priority_order=[Layer.ZERODHA, Layer.MONGODB]
            )
        
        # VERTICAL_ANALYSIS: MongoDB + Pinecone
        elif intent == QueryIntent.VERTICAL_ANALYSIS:
            return SearchPlan(
                layers=[Layer.MONGODB, Layer.PINECONE],
                max_web_calls=0,
                cache_ttl=3600,
                priority_order=[Layer.MONGODB, Layer.PINECONE]
            )
        
        # NEWS: Perplexity (1 web call allowed)
        elif intent == QueryIntent.NEWS:
            return SearchPlan(
                layers=[Layer.PERPLEXITY],
                max_web_calls=1,
                cache_ttl=300,  # 5 minutes
                priority_order=[Layer.PERPLEXITY]
            )
        
        # MARKET_OVERVIEW: Zerodha + NSE + limited web search
        elif intent == "market_overview":
            return SearchPlan(
                layers=[Layer.ZERODHA, Layer.NSE, Layer.PERPLEXITY],
                max_web_calls=1,  # Only for FII/DII or global cues
                cache_ttl=300,
                priority_order=[Layer.ZERODHA, Layer.NSE, Layer.PERPLEXITY]
            )
        
        # MULTI: Combination of sources
        elif intent == QueryIntent.MULTI:
            layers = [Layer.ZERODHA, Layer.MONGODB, Layer.PINECONE]
            if not has_cache:
                layers.append(Layer.PERPLEXITY)
            
            return SearchPlan(
                layers=layers,
                max_web_calls=1,
                cache_ttl=300,
                priority_order=[Layer.ZERODHA, Layer.MONGODB, Layer.PINECONE, Layer.PERPLEXITY]
            )
        
        # GENERAL: Pinecone + limited web
        elif intent == QueryIntent.GENERAL:
            return SearchPlan(
                layers=[Layer.PINECONE, Layer.PERPLEXITY],
                max_web_calls=1,
                cache_ttl=600,
                priority_order=[Layer.PINECONE, Layer.PERPLEXITY]
            )
        
        # Default: Conservative approach
        else:
            return SearchPlan(
                layers=[Layer.MONGODB, Layer.PINECONE],
                max_web_calls=0,
                cache_ttl=600,
                priority_order=[Layer.MONGODB, Layer.PINECONE]
            )
    
    def should_skip_layer(
        self,
        layer: Layer,
        data_collected: dict,
        intent: QueryIntent
    ) -> bool:
        """
        Determine if we can skip a layer based on data already collected.
        
        Args:
            layer: Layer to check
            data_collected: Data collected so far
            intent: Query intent
            
        Returns:
            True if layer can be skipped
        """
        # Skip Perplexity if we have sufficient structured data
        if layer == Layer.PERPLEXITY:
            if intent in [QueryIntent.FUNDAMENTAL, QueryIntent.TECHNICAL, QueryIntent.FINANCIAL_METRICS, QueryIntent.PRICE_CHECK]:
                # We have all this data locally - no need for web search
                return True
            
            if intent == QueryIntent.MARKET_DATA and data_collected.get("market_data"):
                # We have live prices, no need for web search
                return True
        
        # Skip Pinecone if we have structured data for metrics queries
        if layer == Layer.PINECONE:
            if intent in [QueryIntent.FINANCIAL_METRICS, QueryIntent.CORPORATE_ACTIONS]:
                # Structured data is sufficient
                return True
        
        # Skip NSE if we already have Zerodha data for simple queries
        if layer == Layer.NSE:
            if intent == QueryIntent.MARKET_DATA and data_collected.get("market_data"):
                return True
        
        return False
    
    def estimate_latency(self, plan: SearchPlan) -> dict:
        """
        Estimate latency for search plan.
        
        Args:
            plan: Search plan
            
        Returns:
            Dict with latency estimates
        """
        # Layer latency estimates (ms)
        layer_latency = {
            Layer.ZERODHA: 200,
            Layer.MONGODB: 50,
            Layer.PINECONE: 300,
            Layer.NSE: 500,
            Layer.PERPLEXITY: 2000
        }
        
        # Calculate total latency (assuming parallel execution where possible)
        # Structured layers can run in parallel
        structured_latency = max(
            [layer_latency.get(layer, 0) for layer in plan.layers 
             if layer in [Layer.ZERODHA, Layer.MONGODB, Layer.NSE]],
            default=0
        )
        
        # Vector search
        vector_latency = layer_latency[Layer.PINECONE] if Layer.PINECONE in plan.layers else 0
        
        # Web search (sequential after structured)
        web_latency = layer_latency[Layer.PERPLEXITY] if Layer.PERPLEXITY in plan.layers else 0
        
        # Total: structured (parallel) + vector + web (sequential)
        total_latency = structured_latency + vector_latency + web_latency
        
        return {
            "total_ms": total_latency,
            "structured_ms": structured_latency,
            "vector_ms": vector_latency,
            "web_ms": web_latency,
            "breakdown": {layer.value: layer_latency.get(layer, 0) for layer in plan.layers}
        }


# Singleton instance
_search_router: Optional[SearchRouter] = None


def get_search_router() -> SearchRouter:
    """Get singleton search router instance."""
    global _search_router
    if _search_router is None:
        _search_router = SearchRouter()
    return _search_router
