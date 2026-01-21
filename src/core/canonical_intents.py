"""
Core reasoning engine - Layer 1: Canonical Intent System

SIMPLIFIED VERSION:
- Reuses existing intent_classifier.py logic
- Maps to 9 canonical intents (reduced from 15+)
- Strict priority order
- Fast, no LLM calls
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CanonicalIntent(str, Enum):
    """
    Finite, strict intent taxonomy (9 intents max).
    
    Design principle: Fewer intents = more consistent responses.
    """
    STOCK_OVERVIEW = "stock_overview"          # "sandur manganese", "tell me about RELIANCE"
    STOCK_COMPARISON = "stock_comparison"      # "ONGC vs BPCL", "best energy stocks"
    STOCK_DEEP_DIVE = "stock_deep_dive"        # "is sandur a good investment?"
    SECTOR_ANALYSIS = "sector_analysis"        # "energy sector", "sector rotation"
    PRICE_CHECK = "price_check"                # "ONGC price", "current price"
    NEWS_QUERY = "news_query"                  # "latest news", "recent developments"
    FINANCIAL_QUERY = "financial_query"        # "revenue", "profit", "quarterly results"
    MARKET_OVERVIEW = "market_overview"        # "nifty", "market today"
    GENERAL = "general"                        # Greetings, help


@dataclass
class IntentClassification:
    """Strict JSON output from classifier."""
    intent: CanonicalIntent
    confidence: float  # 0.0 to 1.0
    entities: list  # Stock symbols, sectors
    
    def is_confident(self) -> bool:
        """Check if classification is confident enough."""
        return self.confidence >= 0.6


class CanonicalIntentMapper:
    """
    Maps existing QueryIntent to CanonicalIntent.
    
    OPTIMIZATION: Reuses existing intent_classifier.py (no new LLM calls).
    """
    
    # Mapping from old intents to canonical intents
    INTENT_MAPPING = {
        # Stock-related
        "news": CanonicalIntent.NEWS_QUERY,
        "market_data": CanonicalIntent.PRICE_CHECK,
        "fundamental": CanonicalIntent.STOCK_DEEP_DIVE,
        
        # Financial data
        "financial_metrics": CanonicalIntent.FINANCIAL_QUERY,
        "corporate_actions": CanonicalIntent.FINANCIAL_QUERY,
        "trend_analysis": CanonicalIntent.FINANCIAL_QUERY,
        
        # Sector & market
        "sector_performance": CanonicalIntent.SECTOR_ANALYSIS,
        "sector_rotation": CanonicalIntent.SECTOR_ANALYSIS,
        "vertical_analysis": CanonicalIntent.SECTOR_ANALYSIS,
        
        # Comparison
        "stock_comparison": CanonicalIntent.STOCK_COMPARISON,
        
        # General
        "general": CanonicalIntent.GENERAL,
        "multi": CanonicalIntent.STOCK_OVERVIEW,  # Default to overview
    }
    
    def map(self, old_intent: str, query: str, symbols: list) -> IntentClassification:
        """
        Map old intent to canonical intent with priority rules.
        
        Priority order (highest to lowest):
        1. PRICE_CHECK - explicit price queries
        2. STOCK_COMPARISON - sector-based stock queries
        3. FINANCIAL_QUERY - revenue/profit queries
        4. SECTOR_ANALYSIS - sector performance
        5. NEWS_QUERY - news queries
        6. STOCK_DEEP_DIVE - investment analysis
        7. STOCK_OVERVIEW - general stock info
        8. MARKET_OVERVIEW - market/index queries
        9. GENERAL - fallback
        """
        query_lower = query.lower()
        
        # PRIORITY 1: Price check (fast path, skip heavy processing)
        if self._is_price_check(query_lower, old_intent):
            return IntentClassification(
                intent=CanonicalIntent.PRICE_CHECK,
                confidence=0.9,
                entities=symbols
            )
        
        # PRIORITY 2: Stock comparison (sector-based)
        if old_intent == "stock_comparison":
            return IntentClassification(
                intent=CanonicalIntent.STOCK_COMPARISON,
                confidence=0.85,
                entities=symbols
            )
        
        # PRIORITY 3: Financial query
        if old_intent in ["financial_metrics", "corporate_actions", "trend_analysis"]:
            return IntentClassification(
                intent=CanonicalIntent.FINANCIAL_QUERY,
                confidence=0.85,
                entities=symbols
            )
        
        # PRIORITY 4: Sector analysis
        if old_intent in ["sector_performance", "sector_rotation", "vertical_analysis"]:
            return IntentClassification(
                intent=CanonicalIntent.SECTOR_ANALYSIS,
                confidence=0.85,
                entities=symbols
            )
        
        # PRIORITY 5: Market overview (indices)
        if self._is_market_overview(query_lower, symbols):
            return IntentClassification(
                intent=CanonicalIntent.MARKET_OVERVIEW,
                confidence=0.85,
                entities=symbols
            )
        
        # PRIORITY 6: News query
        if old_intent == "news":
            return IntentClassification(
                intent=CanonicalIntent.NEWS_QUERY,
                confidence=0.8,
                entities=symbols
            )
        
        # PRIORITY 7: Deep dive (investment analysis)
        if self._is_deep_dive(query_lower):
            return IntentClassification(
                intent=CanonicalIntent.STOCK_DEEP_DIVE,
                confidence=0.8,
                entities=symbols
            )
        
        # PRIORITY 8: Stock overview (default for stocks)
        if symbols:
            # If we have symbols but no specific intent, default to STOCK_OVERVIEW
            return IntentClassification(
                intent=CanonicalIntent.STOCK_OVERVIEW,
                confidence=0.75,
                entities=symbols
            )
        
        # PRIORITY 9: General (fallback)
        return IntentClassification(
            intent=CanonicalIntent.GENERAL,
            confidence=0.6,
            entities=[]
        )
    
    def _is_price_check(self, query_lower: str, old_intent: str) -> bool:
        """Check if query is a price check."""
        price_keywords = ['price', 'current', 'trading at', 'worth', 'quote', 'ltp']
        return (
            old_intent == "market_data" and
            any(kw in query_lower for kw in price_keywords)
        )
    
    def _is_market_overview(self, query_lower: str, symbols: list) -> bool:
        """Check if query is about market/index overview."""
        index_symbols = ['NIFTY 50', 'NIFTY BANK', 'SENSEX']
        market_keywords = ['market', 'nifty', 'sensex', 'index']
        return (
            any(idx in symbols for idx in index_symbols) or
            any(kw in query_lower for kw in market_keywords)
        )
    
    def _is_deep_dive(self, query_lower: str) -> bool:
        """Check if query requires deep investment analysis."""
        deep_dive_keywords = [
            'good investment', 'should i buy', 'should i invest',
            'worth buying', 'worth investing', 'is it good',
            'recommend', 'suggestion'
        ]
        return any(kw in query_lower for kw in deep_dive_keywords)


# Singleton instance
_mapper_instance: Optional[CanonicalIntentMapper] = None


def get_canonical_intent_mapper() -> CanonicalIntentMapper:
    """Get singleton mapper instance."""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = CanonicalIntentMapper()
    return _mapper_instance
