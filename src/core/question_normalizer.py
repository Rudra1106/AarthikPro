"""
Core reasoning engine - Layer 2: Question Normalization

SIMPLIFIED VERSION:
- Lightweight normalization (no heavy processing)
- Default assumptions for missing info
- Fast execution (<5ms)
"""
from dataclasses import dataclass
from typing import List, Optional
from src.core.canonical_intents import CanonicalIntent
import logging

logger = logging.getLogger(__name__)


@dataclass
class NormalizedQuestion:
    """
    Internal question representation (canonical form).
    
    Design principle: Same normalized object → same reasoning path.
    """
    intent: CanonicalIntent
    asset_type: str  # "stock" | "sector" | "index"
    entities: List[str]  # Stock symbols, sector names
    market: str  # "India" | "US"
    horizon: str  # "short" | "medium" | "long"
    
    # Defaults (stabilize answers)
    DEFAULT_HORIZON = "medium"
    DEFAULT_MARKET = "India"
    
    def to_dict(self) -> dict:
        """Convert to dict for logging."""
        return {
            "intent": self.intent.value,
            "asset_type": self.asset_type,
            "entities": self.entities,
            "market": self.market,
            "horizon": self.horizon
        }


class QuestionNormalizer:
    """
    Converts messy human input → clear internal question.
    
    OPTIMIZATION: Simple rules, no LLM calls, fast execution.
    
    Example:
        User: "sandur manganese and iron ore"
        
        Normalized:
        {
            "intent": "STOCK_OVERVIEW",
            "asset_type": "stock",
            "entities": ["SANDUMA"],
            "market": "India",
            "horizon": "medium"
        }
    """
    
    def normalize(
        self, 
        query: str, 
        intent: CanonicalIntent, 
        entities: List[str]
    ) -> NormalizedQuestion:
        """
        Normalize query to internal question format.
        
        Rules:
        - If horizon not specified → "medium"
        - If market not specified → "India" (for NSE symbols)
        - Asset type inferred from entities
        
        Args:
            query: User query
            intent: Canonical intent
            entities: Extracted entities (symbols, sectors)
            
        Returns:
            Normalized question object
        """
        # Detect asset type
        asset_type = self._detect_asset_type(entities)
        
        # Infer market (default India for NSE)
        market = NormalizedQuestion.DEFAULT_MARKET
        
        # Detect horizon
        horizon = self._detect_horizon(query)
        
        normalized = NormalizedQuestion(
            intent=intent,
            asset_type=asset_type,
            entities=entities,
            market=market,
            horizon=horizon
        )
        
        logger.info(f"Normalized question: {normalized.to_dict()}")
        
        return normalized
    
    def _detect_asset_type(self, entities: List[str]) -> str:
        """
        Detect asset type from entities.
        
        Fast heuristic:
        - NIFTY 50, SENSEX → "index"
        - Sector names → "sector"
        - Stock symbols → "stock"
        """
        if not entities:
            return "stock"  # Default
        
        # Check for indices
        index_symbols = ['NIFTY 50', 'NIFTY BANK', 'SENSEX']
        if any(idx in entities for idx in index_symbols):
            return "index"
        
        # Check for sector names
        sector_keywords = [
            'energy', 'it', 'pharma', 'auto', 'bank', 'banking',
            'financial', 'metal', 'fmcg', 'realty', 'infra'
        ]
        if any(any(kw in entity.lower() for kw in sector_keywords) for entity in entities):
            return "sector"
        
        # Default to stock
        return "stock"
    
    def _detect_horizon(self, query: str) -> str:
        """
        Detect time horizon from query.
        
        Fast keyword matching:
        - "today", "now" → "short"
        - "long term", "invest" → "long"
        - Default → "medium"
        """
        query_lower = query.lower()
        
        # Short-term keywords
        short_keywords = ['today', 'now', 'current', 'intraday', 'this week']
        if any(kw in query_lower for kw in short_keywords):
            return "short"
        
        # Long-term keywords
        long_keywords = ['long term', 'invest', 'hold', 'years', 'future']
        if any(kw in query_lower for kw in long_keywords):
            return "long"
        
        # Default to medium
        return NormalizedQuestion.DEFAULT_HORIZON


# Singleton instance
_normalizer_instance: Optional[QuestionNormalizer] = None


def get_question_normalizer() -> QuestionNormalizer:
    """Get singleton normalizer instance."""
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = QuestionNormalizer()
    return _normalizer_instance
