"""
Intelligence module for thought pipelines and market analysis frameworks.
"""
from src.intelligence.market_framework import MarketThinkingFramework, get_market_framework
from src.intelligence.search_router import SearchRouter, SearchPlan, Layer, get_search_router
from src.intelligence.question_classifier import (
    QuestionClassifier, 
    QuestionType, 
    QuestionClassification,
    get_question_classifier
)
from src.intelligence.answer_blueprints import (
    AnswerBlueprint,
    Section,
    get_blueprint,
    is_section_allowed,
    BLUEPRINTS
)
from src.intelligence.tldr_generator import TLDRGenerator, get_tldr_generator
from src.intelligence.relevance_filter import RelevanceFilter, get_relevance_filter
from src.intelligence.reasoning_engine import (
    ReasoningEngine,
    get_reasoning_engine,
    ValuationInsight,
    TrendInsight,
)
from src.intelligence.sector_intelligence import (
    SectorIntelligence,
    get_sector_intelligence,
    SectorProfile,
)

__all__ = [
    # Market Framework
    "MarketThinkingFramework",
    "get_market_framework",
    # Search Router
    "SearchRouter",
    "SearchPlan",
    "Layer",
    "get_search_router",
    # Question Classifier
    "QuestionClassifier",
    "QuestionType",
    "QuestionClassification",
    "get_question_classifier",
    # Answer Blueprints
    "AnswerBlueprint",
    "Section",
    "get_blueprint",
    "is_section_allowed",
    "BLUEPRINTS",
    # TL;DR Generator
    "TLDRGenerator",
    "get_tldr_generator",
    # Relevance Filter
    "RelevanceFilter",
    "get_relevance_filter",
    # Reasoning Engine (Phase 2)
    "ReasoningEngine",
    "get_reasoning_engine",
    "ValuationInsight",
    "TrendInsight",
    # Sector Intelligence (NEW)
    "SectorIntelligence",
    "get_sector_intelligence",
    "SectorProfile",
]
