"""
Answer Blueprints - Define what to show AND what NOT to show.

Each blueprint specifies:
- Required sections (must include)
- Optional sections (include if data available)
- Forbidden sections (NEVER include)
- TL;DR template
- Data sources needed
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.intelligence.question_classifier import QuestionType


@dataclass
class AnswerBlueprint:
    """Blueprint for structuring an answer."""
    question_type: QuestionType
    required_sections: List[str]
    optional_sections: List[str]
    forbidden_sections: List[str]
    tldr_template: str
    data_needed: List[str]
    prompt_focus: str  # What the LLM should focus on
    
    def to_dict(self) -> dict:
        return {
            "question_type": self.question_type.value,
            "required_sections": self.required_sections,
            "optional_sections": self.optional_sections,
            "forbidden_sections": self.forbidden_sections,
            "tldr_template": self.tldr_template,
            "data_needed": self.data_needed,
            "prompt_focus": self.prompt_focus
        }


# Section names used across blueprints
class Section(str, Enum):
    # Index/Market sections
    INDEX_SNAPSHOT = "index_snapshot"
    BANK_NIFTY = "bank_nifty"
    MARKET_BREADTH = "market_breadth"
    
    # Attribution sections
    STOCK_ATTRIBUTION = "stock_attribution"
    WEIGHT_ANALYSIS = "weight_analysis"
    
    # Sector sections
    SECTOR_RANKING = "sector_ranking"
    SECTOR_BREADTH = "sector_breadth"
    SECTOR_RELATIVE_STRENGTH = "sector_relative_strength"
    
    # Technical sections
    RSI_MACD = "rsi_macd"
    SUPPORT_RESISTANCE = "support_resistance"
    DMA_ANALYSIS = "dma_analysis"
    
    # Fundamental sections
    VALUATION_PE_PB = "valuation_pe_pb"
    EARNINGS_DATA = "earnings_data"
    GROWTH_METRICS = "growth_metrics"
    
    # Vertical/Segment sections
    VERTICAL_BREAKDOWN = "vertical_breakdown"
    SEGMENT_GROWTH = "segment_growth"
    CONCALL_COMMENTARY = "concall_commentary"
    
    # Flow sections
    FII_DII = "fii_dii"
    GLOBAL_CUES = "global_cues"
    
    # Volatility sections
    VIX_ANALYSIS = "vix_analysis"
    VOLATILITY_REGIME = "volatility_regime"
    
    # Scenario sections
    SCENARIO_PROBABILITIES = "scenario_probabilities"
    HISTORICAL_ANALOG = "historical_analog"
    
    # Macro sections
    CURRENCY_IMPACT = "currency_impact"
    MACRO_FACTORS = "macro_factors"
    
    # Conclusion sections
    VERDICT = "verdict"
    KEY_RISKS = "key_risks"
    ACTION_ITEMS = "action_items"


# ============================================
# BLUEPRINT DEFINITIONS
# ============================================

BLUEPRINT_INDEX_COMPARISON = AnswerBlueprint(
    question_type=QuestionType.INDEX_COMPARISON,
    required_sections=[
        Section.STOCK_ATTRIBUTION,      # Which stocks caused divergence
        Section.WEIGHT_ANALYSIS,        # Heavy weights impact
        Section.VERDICT,                # Direct answer
    ],
    optional_sections=[
        Section.SECTOR_RANKING,         # If sector divergence explains it
    ],
    forbidden_sections=[
        Section.RSI_MACD,               # NOT relevant
        Section.VALUATION_PE_PB,        # NOT relevant
        Section.SUPPORT_RESISTANCE,     # NOT relevant
        Section.VIX_ANALYSIS,           # NOT relevant unless asked
        Section.FII_DII,                # NOT relevant unless driving
        Section.VERTICAL_BREAKDOWN,     # NOT relevant
        Section.CONCALL_COMMENTARY,     # NOT relevant
        Section.SCENARIO_PROBABILITIES, # NOT relevant
        Section.DMA_ANALYSIS,           # NOT relevant
    ],
    tldr_template="{index_a} {direction} {index_b} because {primary_reason}",
    data_needed=["index_data", "constituent_attribution", "sector_performance"],
    prompt_focus="EXPLAIN the divergence between indices using stock attribution. Quantify impact (weight × move)."
)


BLUEPRINT_VERTICAL_ANALYSIS = AnswerBlueprint(
    question_type=QuestionType.VERTICAL_ANALYSIS,
    required_sections=[
        Section.VERTICAL_BREAKDOWN,     # Segment-wise data
        Section.SEGMENT_GROWTH,         # Which vertical growing fastest
        Section.VERDICT,                # Sustainability outlook
    ],
    optional_sections=[
        Section.CONCALL_COMMENTARY,     # Management guidance
        Section.EARNINGS_DATA,          # Recent quarter performance
    ],
    forbidden_sections=[
        Section.INDEX_SNAPSHOT,         # NOT relevant
        Section.BANK_NIFTY,             # NOT relevant
        Section.RSI_MACD,               # NOT relevant
        Section.SUPPORT_RESISTANCE,     # NOT relevant
        Section.VIX_ANALYSIS,           # NOT relevant
        Section.MARKET_BREADTH,         # NOT relevant
        Section.SECTOR_RANKING,         # NOT relevant (this is about company)
        Section.FII_DII,                # NOT relevant
        Section.SCENARIO_PROBABILITIES, # NOT relevant
        Section.DMA_ANALYSIS,           # NOT relevant
    ],
    tldr_template="{company}'s {top_vertical} vertical is driving {growth_pct}% of growth, {sustainability_view}",
    data_needed=["vertical_data", "concall_data", "quarterly_financials"],
    prompt_focus="FOCUS only on business segment performance. Identify growth driver and assess 2-quarter sustainability."
)


BLUEPRINT_SECTOR_ROTATION = AnswerBlueprint(
    question_type=QuestionType.SECTOR_ROTATION,
    required_sections=[
        Section.SECTOR_RANKING,         # Which sectors up/down
        Section.SECTOR_RELATIVE_STRENGTH, # Sector vs Nifty
        Section.SECTOR_BREADTH,         # How many stocks participating
    ],
    optional_sections=[
        Section.FII_DII,                # If flow preference visible
        Section.GLOBAL_CUES,            # If global sector trends relevant
    ],
    forbidden_sections=[
        Section.STOCK_ATTRIBUTION,      # NOT the focus
        Section.RSI_MACD,               # NOT relevant at sector level
        Section.VALUATION_PE_PB,        # NOT relevant
        Section.SCENARIO_PROBABILITIES, # NOT the question
        Section.VERTICAL_BREAKDOWN,     # NOT relevant
        Section.SUPPORT_RESISTANCE,     # NOT relevant
        Section.CONCALL_COMMENTARY,     # NOT relevant
    ],
    tldr_template="{top_sector} is leading with {sector_change}% vs Nifty's {nifty_change}%, with {breadth}% breadth",
    data_needed=["sector_performance", "sector_breadth", "relative_strength"],
    prompt_focus="RANK sectors by performance. Show relative strength vs Nifty. Indicate breadth within each sector."
)


BLUEPRINT_SCENARIO_ANALYSIS = AnswerBlueprint(
    question_type=QuestionType.SCENARIO_ANALYSIS,
    required_sections=[
        Section.VOLATILITY_REGIME,      # Where are we now?
        Section.SCENARIO_PROBABILITIES, # Bullish/Bearish/Base
        Section.HISTORICAL_ANALOG,      # What happened before
        Section.VERDICT,                # Most likely outcome
    ],
    optional_sections=[
        Section.SUPPORT_RESISTANCE,     # Only if price-based scenario
        Section.VIX_ANALYSIS,           # If VIX mentioned
    ],
    forbidden_sections=[
        Section.INDEX_SNAPSHOT,         # NOT the question
        Section.SECTOR_RANKING,         # NOT relevant
        Section.STOCK_ATTRIBUTION,      # NOT relevant
        Section.EARNINGS_DATA,          # NOT relevant
        Section.VERTICAL_BREAKDOWN,     # NOT relevant
        Section.CONCALL_COMMENTARY,     # NOT relevant
        Section.VALUATION_PE_PB,        # NOT relevant
        Section.RSI_MACD,               # NOT relevant
    ],
    tldr_template="With {condition}, the most likely behavior is {outcome} with {probability}% probability",
    data_needed=["vix_data", "historical_patterns", "key_levels"],
    prompt_focus="ANALYZE the scenario. Provide probability-weighted outcomes. Use historical analogs for context."
)


BLUEPRINT_MACRO_VS_FUNDAMENTAL = AnswerBlueprint(
    question_type=QuestionType.MACRO_VS_FUNDAMENTAL,
    required_sections=[
        Section.EARNINGS_DATA,          # Fundamental signals
        Section.MACRO_FACTORS,          # Macro signals
        Section.CURRENCY_IMPACT,        # USD/INR if relevant
        Section.VERDICT,                # Weighted conclusion
    ],
    optional_sections=[
        Section.GLOBAL_CUES,            # Global tech sentiment
        Section.GROWTH_METRICS,         # Revenue/profit trends
    ],
    forbidden_sections=[
        Section.INDEX_SNAPSHOT,         # NOT the question
        Section.SUPPORT_RESISTANCE,     # NOT relevant
        Section.VIX_ANALYSIS,           # NOT relevant
        Section.SECTOR_RANKING,         # NOT relevant
        Section.VERTICAL_BREAKDOWN,     # NOT relevant
        Section.RSI_MACD,               # NOT relevant
        Section.SCENARIO_PROBABILITIES, # NOT relevant
        Section.MARKET_BREADTH,         # NOT relevant
    ],
    tldr_template="{entity} strength is {fundamental_weight}% fundamental, {macro_weight}% macro-driven because {reason}",
    data_needed=["earnings_data", "currency_data", "global_cues", "growth_metrics"],
    prompt_focus="COMPARE fundamental vs macro drivers. Quantify the weight of each. Provide a clear conclusion."
)


BLUEPRINT_STOCK_DEEP_DIVE = AnswerBlueprint(
    question_type=QuestionType.STOCK_DEEP_DIVE,
    required_sections=[
        Section.EARNINGS_DATA,          # Current price, change
        Section.VALUATION_PE_PB,        # P/E, P/B vs historical
        Section.GROWTH_METRICS,         # Revenue, profit growth
        Section.KEY_RISKS,              # What could go wrong
        Section.VERDICT,                # Buy/Hold/Sell signal
    ],
    optional_sections=[
        Section.RSI_MACD,               # Only for trading view
        Section.SUPPORT_RESISTANCE,     # Price levels
        Section.CONCALL_COMMENTARY,     # Management view
    ],
    forbidden_sections=[
        Section.INDEX_SNAPSHOT,         # NOT the focus
        Section.BANK_NIFTY,             # NOT relevant
        Section.SECTOR_RANKING,         # NOT the focus
        Section.VIX_ANALYSIS,           # NOT relevant
        Section.SCENARIO_PROBABILITIES, # NOT relevant
        Section.MARKET_BREADTH,         # NOT relevant
    ],
    tldr_template="{stock} is {valuation_view} at ₹{price}, with {growth_view} growth and {risk_level} risk",
    data_needed=["stock_price", "financials", "valuation_metrics", "vector_context"],
    prompt_focus="ANALYZE the stock comprehensively. Focus on valuation, growth, and risks. Give a clear verdict."
)


BLUEPRINT_MARKET_OVERVIEW = AnswerBlueprint(
    question_type=QuestionType.MARKET_OVERVIEW,
    required_sections=[
        Section.INDEX_SNAPSHOT,         # Nifty, Sensex, Bank Nifty
        Section.SECTOR_RANKING,         # Top/bottom sectors
        Section.VIX_ANALYSIS,           # Volatility context
        Section.VERDICT,                # One-line sentiment
    ],
    optional_sections=[
        Section.FII_DII,                # If significant
        Section.GLOBAL_CUES,            # If impactful
        Section.DMA_ANALYSIS,           # Brief technical health
        Section.MARKET_BREADTH,         # Advance/Decline
    ],
    forbidden_sections=[
        Section.VERTICAL_BREAKDOWN,     # NOT the question
        Section.EARNINGS_DATA,          # NOT relevant for overview
        Section.CONCALL_COMMENTARY,     # NOT relevant
        Section.HISTORICAL_ANALOG,      # NOT relevant
        Section.CURRENCY_IMPACT,        # NOT the focus
    ],
    tldr_template="Market is {sentiment} with Nifty at ₹{price} ({change}%), led by {top_sector}",
    data_needed=["index_data", "sector_data", "vix_data", "breadth_data"],
    prompt_focus="SUMMARIZE the market. Focus on key movers, sentiment, and notable sectors."
)


BLUEPRINT_PRICE_CHECK = AnswerBlueprint(
    question_type=QuestionType.PRICE_CHECK,
    required_sections=[
        Section.VERDICT,                # Direct price answer
    ],
    optional_sections=[
        Section.EARNINGS_DATA,          # Day's change
    ],
    forbidden_sections=[
        Section.INDEX_SNAPSHOT,         # NOT needed
        Section.SECTOR_RANKING,         # NOT needed
        Section.RSI_MACD,               # NOT needed
        Section.SUPPORT_RESISTANCE,     # NOT asked
        Section.VIX_ANALYSIS,           # NOT needed
        Section.VERTICAL_BREAKDOWN,     # NOT needed
        Section.CONCALL_COMMENTARY,     # NOT needed
        Section.SCENARIO_PROBABILITIES, # NOT needed
        Section.VALUATION_PE_PB,        # NOT asked
        Section.FII_DII,                # NOT needed
        Section.MARKET_BREADTH,         # NOT needed
    ],
    tldr_template="{stock} is trading at ₹{price} ({change}%)",
    data_needed=["stock_price"],
    prompt_focus="GIVE the price directly. Be concise. No extra analysis unless asked."
)


# Blueprint registry
BLUEPRINTS: Dict[QuestionType, AnswerBlueprint] = {
    QuestionType.INDEX_COMPARISON: BLUEPRINT_INDEX_COMPARISON,
    QuestionType.VERTICAL_ANALYSIS: BLUEPRINT_VERTICAL_ANALYSIS,
    QuestionType.SECTOR_ROTATION: BLUEPRINT_SECTOR_ROTATION,
    QuestionType.SCENARIO_ANALYSIS: BLUEPRINT_SCENARIO_ANALYSIS,
    QuestionType.MACRO_VS_FUNDAMENTAL: BLUEPRINT_MACRO_VS_FUNDAMENTAL,
    QuestionType.STOCK_DEEP_DIVE: BLUEPRINT_STOCK_DEEP_DIVE,
    QuestionType.MARKET_OVERVIEW: BLUEPRINT_MARKET_OVERVIEW,
    QuestionType.PRICE_CHECK: BLUEPRINT_PRICE_CHECK,
}


def get_blueprint(question_type: QuestionType) -> AnswerBlueprint:
    """Get answer blueprint for question type."""
    return BLUEPRINTS.get(question_type, BLUEPRINT_MARKET_OVERVIEW)


def is_section_allowed(section: str, blueprint: AnswerBlueprint) -> bool:
    """Check if section is allowed in blueprint."""
    # Forbidden -> never show
    if section in blueprint.forbidden_sections:
        return False
    
    # Required or Optional -> allowed
    if section in blueprint.required_sections or section in blueprint.optional_sections:
        return True
    
    # Not mentioned -> default to not showing (conservative)
    return False


def get_required_data_sources(blueprint: AnswerBlueprint) -> List[str]:
    """Get list of data sources needed for blueprint."""
    return blueprint.data_needed
