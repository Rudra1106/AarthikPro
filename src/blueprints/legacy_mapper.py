"""
Legacy Intent Mapper.

Maps old QueryIntent enum values to new CanonicalIntent values
for backward compatibility.
"""

from typing import Dict
from src.blueprints.canonical_intents import CanonicalIntent


# Legacy intent mapping
LEGACY_TO_CANONICAL: Dict[str, CanonicalIntent] = {
    # Stock Analysis
    "FUNDAMENTAL": CanonicalIntent.STOCK_OVERVIEW,
    "FINANCIAL_METRICS": CanonicalIntent.STOCK_OVERVIEW,
    "TREND_ANALYSIS": CanonicalIntent.STOCK_DEEP_DIVE,
    "COMPARISON": CanonicalIntent.STOCK_COMPARISON,
    
    # Technical & Price
    "TECHNICAL": CanonicalIntent.PRICE_ACTION,
    "PRICE_CHECK": CanonicalIntent.PRICE_ACTION,
    "MARKET_DATA": CanonicalIntent.PRICE_ACTION,
    
    # Sector
    "SECTOR_PERFORMANCE": CanonicalIntent.SECTOR_OVERVIEW,
    "VERTICAL_ANALYSIS": CanonicalIntent.SECTOR_OVERVIEW,
    
    # Corporate Actions & Risk
    "CORPORATE_ACTIONS": CanonicalIntent.STOCK_OVERVIEW,
    "RISK": CanonicalIntent.RISK_ANALYSIS,
    
    # News & Market
    "NEWS": CanonicalIntent.STOCK_OVERVIEW,
    "MARKET_OVERVIEW": CanonicalIntent.SECTOR_ROTATION,
    
    # Multi & General
    "MULTI": CanonicalIntent.STOCK_DEEP_DIVE,
    "GENERAL": CanonicalIntent.STOCK_OVERVIEW,
    "PORTFOLIO": CanonicalIntent.STOCK_SCREENING,
}


def map_legacy_intent(legacy_intent: str) -> CanonicalIntent:
    """
    Map legacy intent to canonical intent.
    
    Args:
        legacy_intent: Old intent string (e.g., "FUNDAMENTAL")
    
    Returns:
        Canonical intent
    """
    # Handle enum values
    if hasattr(legacy_intent, 'value'):
        legacy_intent = legacy_intent.value
    
    # Convert to uppercase for matching
    legacy_intent_upper = str(legacy_intent).upper()
    
    # Try direct mapping
    if legacy_intent_upper in LEGACY_TO_CANONICAL:
        return LEGACY_TO_CANONICAL[legacy_intent_upper]
    
    # Fallback to STOCK_OVERVIEW
    return CanonicalIntent.STOCK_OVERVIEW


def get_canonical_intent_name(legacy_intent: str) -> str:
    """
    Get canonical intent name from legacy intent.
    
    Args:
        legacy_intent: Old intent string
    
    Returns:
        Canonical intent name (e.g., "stock_overview")
    """
    canonical = map_legacy_intent(legacy_intent)
    return canonical.value
