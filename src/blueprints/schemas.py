"""
Blueprint Schemas - Strict Output Contracts.

Each blueprint defines the exact structure of responses for each intent.
Uses Pydantic for validation and type safety.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


# ============================================================================
# STOCK_OVERVIEW Blueprint
# ============================================================================

class StockOverviewBlueprint(BaseModel):
    """
    Bloomberg-style company snapshot.
    
    Quick overview with business model, positioning, and risks.
    """
    tldr: str = Field(
        ...,
        description="1-2 sentence executive summary",
        min_length=20,
        max_length=300
    )
    
    business_model: str = Field(
        ...,
        description="What the company does and how it makes money",
        min_length=50
    )
    
    key_earnings_drivers: List[str] = Field(
        ...,
        description="Top 3-5 revenue/profit drivers",
        min_items=3,
        max_items=5
    )
    
    relative_position: str = Field(
        ...,
        description="Position vs peers and market",
        min_length=30
    )
    
    key_risks: List[str] = Field(
        ...,
        description="Top 3 risks to watch",
        min_items=2,
        max_items=3
    )
    
    investor_fit: str = Field(
        ...,
        description="Who should own this stock",
        min_length=30
    )


# ============================================================================
# STOCK_DEEP_DIVE Blueprint
# ============================================================================

class StockDeepDiveBlueprint(BaseModel):
    """
    Bull/Bear investment analysis.
    
    Provides verdict with supporting cases and triggers.
    """
    verdict: str = Field(
        ...,
        description="Bull / Neutral / Bear",
        pattern="^(Bull|Neutral|Bear)$"
    )
    
    bull_case: List[str] = Field(
        ...,
        description="3-5 bullish arguments",
        min_items=3,
        max_items=5
    )
    
    bear_case: List[str] = Field(
        ...,
        description="3-5 bearish arguments",
        min_items=3,
        max_items=5
    )
    
    triggers: Dict[str, List[str]] = Field(
        ...,
        description="Upside and downside catalysts",
    )
    
    who_should_own: str = Field(
        ...,
        description="Investor profile and time horizon",
        min_length=30
    )


# ============================================================================
# STOCK_COMPARISON Blueprint
# ============================================================================

class StockComparisonBlueprint(BaseModel):
    """
    Side-by-side stock comparison.
    
    Decision-first with contextual winner and scenarios.
    """
    winner: str = Field(
        ...,
        description="Contextual winner (or 'Depends')",
        min_length=10
    )
    
    comparison_table: Dict[str, Dict[str, str]] = Field(
        ...,
        description="Side-by-side metrics comparison"
    )
    
    when_a_wins: str = Field(
        ...,
        description="Scenarios where stock A is better",
        min_length=30
    )
    
    when_b_wins: str = Field(
        ...,
        description="Scenarios where stock B is better",
        min_length=30
    )
    
    final_takeaway: str = Field(
        ...,
        description="Decision guidance",
        min_length=30
    )


# ============================================================================
# STOCK_SCREENING Blueprint
# ============================================================================

class RankedPick(BaseModel):
    """Individual stock pick with ranking."""
    rank: int = Field(..., ge=1, le=10)
    symbol: str
    name: str
    reason: str = Field(..., min_length=20)
    key_metric: Optional[str] = None


class StockScreeningBlueprint(BaseModel):
    """
    Stock screening with ranked picks.
    
    What users REALLY want - actionable picks with context.
    """
    market_context: str = Field(
        ...,
        description="Current market environment",
        min_length=50
    )
    
    ranked_picks: List[RankedPick] = Field(
        ...,
        description="Top 5 picks with reasons",
        min_items=3,
        max_items=5
    )
    
    whats_working: str = Field(
        ...,
        description="Themes and factors working now",
        min_length=30
    )
    
    whats_not_working: str = Field(
        ...,
        description="What to avoid",
        min_length=30
    )
    
    actionable_takeaway: str = Field(
        ...,
        description="Next steps for investor",
        min_length=30
    )


# ============================================================================
# PRICE_ACTION Blueprint
# ============================================================================

class PriceActionBlueprint(BaseModel):
    """
    Technical analysis with levels and signals.
    
    Price-first with momentum, levels, and trading signals.
    """
    current_price: str = Field(..., description="Current price with change")
    
    trend: str = Field(
        ...,
        description="Uptrend / Downtrend / Sideways",
        pattern="^(Uptrend|Downtrend|Sideways)$"
    )
    
    momentum: str = Field(
        ...,
        description="Strong / Moderate / Weak",
        pattern="^(Strong|Moderate|Weak)$"
    )
    
    key_levels: Dict[str, str] = Field(
        ...,
        description="Support and resistance levels"
    )
    
    indicators: Dict[str, str] = Field(
        ...,
        description="Technical indicators (RSI, MACD, etc.)"
    )
    
    signals: List[str] = Field(
        ...,
        description="Trading signals and patterns",
        min_items=2
    )
    
    outlook: str = Field(
        ...,
        description="Short-term technical outlook",
        min_length=30
    )


# ============================================================================
# SECTOR_OVERVIEW Blueprint
# ============================================================================

class SectorOverviewBlueprint(BaseModel):
    """
    Sector snapshot with drivers and positioning.
    
    Institutional-style sector analysis.
    """
    sector_snapshot: str = Field(
        ...,
        description="Current sector state",
        min_length=50
    )
    
    drivers_and_headwinds: Dict[str, List[str]] = Field(
        ...,
        description="Positive and negative factors"
    )
    
    leaders_vs_laggards: Dict[str, List[str]] = Field(
        ...,
        description="Performance split"
    )
    
    breadth_interpretation: str = Field(
        ...,
        description="Market participation analysis",
        min_length=30
    )
    
    investor_takeaway: str = Field(
        ...,
        description="Actionable sector view",
        min_length=30
    )


# ============================================================================
# SECTOR_ROTATION Blueprint
# ============================================================================

class SectorRotationBlueprint(BaseModel):
    """
    Sector momentum and rotation analysis.
    
    Institutional-style rotation tracking.
    """
    rotation_summary: str = Field(
        ...,
        description="What's rotating and why",
        min_length=50
    )
    
    relative_performance: Dict[str, str] = Field(
        ...,
        description="Sector rankings with performance"
    )
    
    breadth_and_participation: str = Field(
        ...,
        description="Market health indicators",
        min_length=30
    )
    
    why_this_is_happening: str = Field(
        ...,
        description="Macro and fundamental drivers",
        min_length=50
    )
    
    tactical_takeaway: str = Field(
        ...,
        description="Trading implications",
        min_length=30
    )


# ============================================================================
# RISK_ANALYSIS Blueprint
# ============================================================================

class RiskAnalysisBlueprint(BaseModel):
    """
    Risk assessment with scenarios and hedges.
    
    Comprehensive risk framework.
    """
    risk_summary: str = Field(
        ...,
        description="Overall risk assessment",
        min_length=50
    )
    
    key_exposures: List[str] = Field(
        ...,
        description="Top 3-5 risk exposures",
        min_items=3,
        max_items=5
    )
    
    scenarios: Dict[str, str] = Field(
        ...,
        description="Bull/Base/Bear scenarios"
    )
    
    hedging_strategies: List[str] = Field(
        ...,
        description="Risk mitigation approaches",
        min_items=2
    )
    
    monitoring_metrics: List[str] = Field(
        ...,
        description="What to watch",
        min_items=3
    )


# ============================================================================
# TRADE_IDEA Blueprint
# ============================================================================

class TradeIdeaBlueprint(BaseModel):
    """
    Actionable trade setup.
    
    Entry/exit/risk with clear rationale.
    """
    trade_setup: str = Field(
        ...,
        description="Trade thesis and setup",
        min_length=50
    )
    
    direction: str = Field(
        ...,
        description="Long / Short / Neutral",
        pattern="^(Long|Short|Neutral)$"
    )
    
    entry_zone: str = Field(
        ...,
        description="Entry price range"
    )
    
    targets: List[str] = Field(
        ...,
        description="Profit targets",
        min_items=1,
        max_items=3
    )
    
    stop_loss: str = Field(
        ...,
        description="Risk management level"
    )
    
    risk_reward: str = Field(
        ...,
        description="Risk/reward ratio"
    )
    
    time_horizon: str = Field(
        ...,
        description="Expected holding period"
    )
    
    rationale: str = Field(
        ...,
        description="Why this trade works",
        min_length=50
    )


# ============================================================================
# Blueprint Registry
# ============================================================================

BLUEPRINT_REGISTRY = {
    "stock_overview": StockOverviewBlueprint,
    "stock_deep_dive": StockDeepDiveBlueprint,
    "stock_comparison": StockComparisonBlueprint,
    "stock_screening": StockScreeningBlueprint,
    "price_action": PriceActionBlueprint,
    "sector_overview": SectorOverviewBlueprint,
    "sector_rotation": SectorRotationBlueprint,
    "risk_analysis": RiskAnalysisBlueprint,
    "trade_idea": TradeIdeaBlueprint,
}


def get_blueprint(intent_name: str) -> type[BaseModel]:
    """Get blueprint class for an intent."""
    return BLUEPRINT_REGISTRY.get(intent_name)


def validate_response(intent_name: str, response_data: dict) -> BaseModel:
    """
    Validate response against blueprint.
    
    Args:
        intent_name: Canonical intent name
        response_data: Response data to validate
    
    Returns:
        Validated blueprint instance
    
    Raises:
        ValidationError if response doesn't match blueprint
    """
    blueprint_class = get_blueprint(intent_name)
    if not blueprint_class:
        raise ValueError(f"No blueprint found for intent: {intent_name}")
    
    return blueprint_class(**response_data)
