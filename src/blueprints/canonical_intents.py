"""
Canonical Intent Taxonomy - 9 Production-Ready Intents.

These 9 intents cover >95% of finance queries and enforce
strict output contracts for Bloomberg-style responses.
"""

from enum import Enum
from typing import Dict, List


class CanonicalIntent(Enum):
    """
    9 canonical intents for financial queries.
    
    Each intent maps to a specific blueprint (output contract).
    """
    
    # Stock Analysis Intents
    STOCK_OVERVIEW = "stock_overview"
    """Quick company snapshot - TL;DR, business model, position, risks"""
    
    STOCK_DEEP_DIVE = "stock_deep_dive"
    """Bull/Bear analysis - verdict, cases, triggers, investor fit"""
    
    STOCK_COMPARISON = "stock_comparison"
    """A vs B decision - winner, table, scenarios, takeaway"""
    
    STOCK_SCREENING = "stock_screening"
    """Find best stocks - context, ranked picks, themes, actionable"""
    
    # Price & Technical Intents
    PRICE_ACTION = "price_action"
    """Technical analysis - price, momentum, levels, signals"""
    
    # Sector Intents
    SECTOR_OVERVIEW = "sector_overview"
    """Sector snapshot - drivers, leaders/laggards, breadth, takeaway"""
    
    SECTOR_ROTATION = "sector_rotation"
    """Sector momentum - rotation, performance, breadth, why, tactical"""
    
    SECTOR_COMPARISON = "sector_comparison"
    """Sector A vs B - business models, comparison table, risks, suitability"""
    
    # Risk & Trading Intents
    RISK_ANALYSIS = "risk_analysis"
    """Risk assessment - exposures, scenarios, hedges, monitoring"""
    
    TRADE_IDEA = "trade_idea"
    """Actionable trade - setup, entry, exit, risk, rationale"""


# Intent Metadata
INTENT_METADATA: Dict[CanonicalIntent, Dict] = {
    CanonicalIntent.STOCK_OVERVIEW: {
        "description": "Quick company snapshot with business model and positioning",
        "typical_queries": [
            "Tell me about {company}",
            "What does {company} do?",
            "Give me an overview of {company}",
            "{company} company profile",
        ],
        "requires_symbols": True,
        "requires_fundamentals": True,
        "output_blueprint": "StockOverviewBlueprint",
    },
    
    CanonicalIntent.STOCK_DEEP_DIVE: {
        "description": "Bull/Bear analysis with investment verdict",
        "typical_queries": [
            "Should I buy {company}?",
            "Is {company} a good investment?",
            "Bull case for {company}",
            "Investment thesis for {company}",
        ],
        "requires_symbols": True,
        "requires_fundamentals": True,
        "requires_price_data": True,
        "output_blueprint": "StockDeepDiveBlueprint",
    },
    
    CanonicalIntent.STOCK_COMPARISON: {
        "description": "Side-by-side comparison with decision guidance",
        "typical_queries": [
            "{company1} vs {company2}",
            "Compare {company1} and {company2}",
            "Which is better: {company1} or {company2}?",
            "{company1} or {company2} for investment?",
        ],
        "requires_symbols": True,
        "requires_fundamentals": True,
        "requires_price_data": True,
        "output_blueprint": "StockComparisonBlueprint",
    },
    
    CanonicalIntent.STOCK_SCREENING: {
        "description": "Find and rank best stocks with actionable picks",
        "typical_queries": [
            "Best {sector} stocks to buy",
            "Top stocks in {sector}",
            "Which stocks should I buy now?",
            "Stock recommendations for {theme}",
        ],
        "requires_symbols": False,
        "requires_market_data": True,
        "requires_screening": True,
        "output_blueprint": "StockScreeningBlueprint",
    },
    
    CanonicalIntent.PRICE_ACTION: {
        "description": "Technical analysis with price levels and signals",
        "typical_queries": [
            "{company} technical analysis",
            "{company} chart analysis",
            "Price action for {company}",
            "{company} support and resistance",
        ],
        "requires_symbols": True,
        "requires_price_data": True,
        "requires_technical": True,
        "output_blueprint": "PriceActionBlueprint",
    },
    
    CanonicalIntent.SECTOR_OVERVIEW: {
        "description": "Sector snapshot with drivers and positioning",
        "typical_queries": [
            "How is {sector} sector performing?",
            "{sector} sector analysis",
            "What's happening in {sector}?",
            "{sector} sector outlook",
        ],
        "requires_symbols": False,
        "requires_sector_data": True,
        "output_blueprint": "SectorOverviewBlueprint",
    },
    
    CanonicalIntent.SECTOR_ROTATION: {
        "description": "Sector momentum and rotation analysis",
        "typical_queries": [
            "Which sectors are rotating?",
            "Sector rotation analysis",
            "What sectors are outperforming?",
            "Sector momentum",
        ],
        "requires_symbols": False,
        "requires_sector_data": True,
        "requires_market_data": True,
        "output_blueprint": "SectorRotationBlueprint",
    },
    
    CanonicalIntent.STOCK_DEEP_DIVE: {
        "description": "Investment verdict with bull/bear analysis",
        "typical_queries": [
            "Should I buy {company}?",
            "Is {company} a good investment?",
            "Investment analysis for {company}",
            "Bull and bear case for {company}",
            "What's your verdict on {company}?",
        ],
        "requires_symbols": True,
        "requires_fundamentals": True,
        "requires_price_data": True,
        "requires_news": True,
        "output_blueprint": "StockDeepDiveBlueprint",
    },
    
    CanonicalIntent.SECTOR_COMPARISON: {
        "description": "Sector vs sector comparison with investment guidance",
        "typical_queries": [
            "Compare {sector1} and {sector2}",
            "{sector1} vs {sector2} sector",
            "IT sector vs Energy sector",
            "Which is better: {sector1} or {sector2}?",
        ],
        "requires_symbols": False,
        "requires_sector_data": True,
        "output_blueprint": "SectorComparisonBlueprint",
    },
    
    CanonicalIntent.RISK_ANALYSIS: {
        "description": "Risk assessment with scenarios and hedges",
        "typical_queries": [
            "What are the risks in {company}?",
            "Risk analysis for {sector}",
            "Downside risks for {company}",
            "What could go wrong with {company}?",
        ],
        "requires_symbols": True,
        "requires_fundamentals": True,
        "requires_news": True,
        "output_blueprint": "RiskAnalysisBlueprint",
    },
    
    CanonicalIntent.TRADE_IDEA: {
        "description": "Actionable trade setup with entry/exit/risk",
        "typical_queries": [
            "Give me a trade idea for {company}",
            "Trading setup for {company}",
            "How to trade {company}?",
            "Trade recommendation for {sector}",
        ],
        "requires_symbols": True,
        "requires_price_data": True,
        "requires_technical": True,
        "output_blueprint": "TradeIdeaBlueprint",
    },
}


def get_intent_requirements(intent: CanonicalIntent) -> Dict:
    """Get data requirements for an intent."""
    return INTENT_METADATA.get(intent, {})


def get_intent_description(intent: CanonicalIntent) -> str:
    """Get human-readable description of an intent."""
    return INTENT_METADATA.get(intent, {}).get("description", "")


def get_typical_queries(intent: CanonicalIntent) -> List[str]:
    """Get typical query patterns for an intent."""
    return INTENT_METADATA.get(intent, {}).get("typical_queries", [])
