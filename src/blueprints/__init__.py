"""
Unified Blueprint System for Bloomberg-style Financial Intelligence.

This module implements:
- 9 canonical intents (covers >95% of finance queries)
- Fixed output blueprints (consistent structure)
- Evidence objects (traceable reasoning)
- Action-oriented responses
"""

from src.blueprints.canonical_intents import CanonicalIntent
from src.blueprints.intent_mapper import IntentMapper, get_intent_mapper
from src.blueprints.schemas import (
    StockOverviewBlueprint,
    StockDeepDiveBlueprint,
    StockComparisonBlueprint,
    StockScreeningBlueprint,
    PriceActionBlueprint,
    SectorOverviewBlueprint,
    SectorRotationBlueprint,
    RiskAnalysisBlueprint,
    TradeIdeaBlueprint,
)
from src.blueprints.evidence import EvidenceBuilder, get_evidence_builder

__all__ = [
    "CanonicalIntent",
    "IntentMapper",
    "get_intent_mapper",
    "StockOverviewBlueprint",
    "StockDeepDiveBlueprint",
    "StockComparisonBlueprint",
    "StockScreeningBlueprint",
    "PriceActionBlueprint",
    "SectorOverviewBlueprint",
    "SectorRotationBlueprint",
    "RiskAnalysisBlueprint",
    "TradeIdeaBlueprint",
    "EvidenceBuilder",
    "get_evidence_builder",
]
