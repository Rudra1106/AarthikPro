"""
Question Type Classifier - Classify questions into reasoning paths.

Instead of dumping a generic market report for every question,
we classify questions into specific types that require different
answer structures.

7 Question Types:
1. INDEX_COMPARISON - "Why did Nifty underperform Bank Nifty?"
2. VERTICAL_ANALYSIS - "Which vertical is driving TCS?"
3. SECTOR_ROTATION - "Which sectors are leading?"
4. SCENARIO_ANALYSIS - "If VIX stays below 10..."
5. MACRO_VS_FUNDAMENTAL - "Is IT strength fundamental or macro?"
6. STOCK_DEEP_DIVE - "Detailed analysis of Reliance"
7. MARKET_OVERVIEW - "How is the market today?"
"""
import re
from enum import Enum
from typing import Optional, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class QuestionType(str, Enum):
    """Question types for answer blueprint selection."""
    INDEX_COMPARISON = "index_comparison"
    VERTICAL_ANALYSIS = "vertical_analysis"
    SECTOR_ROTATION = "sector_rotation"
    SCENARIO_ANALYSIS = "scenario_analysis"
    MACRO_VS_FUNDAMENTAL = "macro_vs_fundamental"
    STOCK_DEEP_DIVE = "stock_deep_dive"
    MARKET_OVERVIEW = "market_overview"
    PRICE_CHECK = "price_check"  # Simple price queries


@dataclass
class QuestionClassification:
    """Result of question classification."""
    question_type: QuestionType
    confidence: float
    matched_signals: List[str]
    extracted_entities: dict  # stocks, sectors, indices mentioned
    
    def to_dict(self) -> dict:
        return {
            "question_type": self.question_type.value,
            "confidence": self.confidence,
            "matched_signals": self.matched_signals,
            "extracted_entities": self.extracted_entities
        }


class QuestionClassifier:
    """
    Classify questions into reasoning paths.
    
    Each question type leads to a different answer structure.
    This is the key to intelligent, focused responses.
    """
    
    def __init__(self):
        # INDEX_COMPARISON patterns
        self.index_comparison_patterns = [
            r'\b(why|how come)\b.*(underperform|outperform|vs|versus|compared to)\b',
            r'\b(nifty|sensex|bank nifty)\b.*(vs|versus|compared|relative)\b',
            r'\b(underperform|outperform)\b.*(nifty|sensex|bank nifty)\b',
            r'\brelative (performance|strength)\b.*(index|nifty|sensex)\b',
            r'\bdivergence\b.*(nifty|bank nifty|sensex)\b',
            r'\bcompare\b.*(nifty|sensex|bank nifty)\b',  # NEW: "compare Nifty and Sensex"
            r'\b(nifty|sensex|bank nifty)\b.*(and|&)\b.*(nifty|sensex|bank nifty)\b.*(performance|compare)\b',  # NEW
        ]
        
        # VERTICAL_ANALYSIS patterns
        self.vertical_analysis_patterns = [
            r'\b(vertical|segment|business unit|division)\b',
            r'\b(which|what).*(vertical|segment|business).*(driving|contributing|growing)\b',
            r'\b(earnings|revenue|growth)\b.*(driver|source|contributor)\b',
            r'\b(bfsi|retail|manufacturing|telecom|healthcare)\b.*(segment|vertical|business)\b',
            r'\bsegment-?wise\b',
            r'\bvertical-?wise\b',
            r'\b(sustainable|sustainability)\b.*(quarters?|growth)\b',
        ]
        
        # SECTOR_ROTATION patterns
        self.sector_rotation_patterns = [
            r'\b(which|what)\b.*\bsectors?\b.*(leading|lagging|performing|outperforming)\b',
            r'\bsector (rotation|performance|trend)\b',
            r'\b(top|best|worst|leading|lagging)\b.*\bsectors?\b',
            r'\bsectors?\b.*(outperforming|underperforming|beating)\b',
            r'\b(cyclical|defensive)\b.*(sector|rotation)\b',
            r'\b(outperform|underperform).*\bnifty\b',  # NEW: "IT outperforming Nifty?"
            r'\b(it|banking|auto|pharma|fmcg|metal|energy)\b.*(outperform|underperform|vs)\b.*(nifty|market)\b',  # NEW
            r'\bsectors?\b.*(watch|rotation|shift)\b',  # NEW: "sectors to watch for rotation"
        ]
        
        # SCENARIO_ANALYSIS patterns
        self.scenario_analysis_patterns = [
            r'\bif\b.*(stays?|remains?|continues?|breaks?)\b',
            r'\bwhat (happens|would happen|if)\b',
            r'\bscenario\b',
            r'\blikely (behavior|outcome|movement)\b',
            r'\bprobability\b.*(bull|bear|up|down)\b',
            r'\b(next few|coming)\b.*(sessions?|days?|weeks?)\b',
        ]
        
        # MACRO_VS_FUNDAMENTAL patterns
        self.macro_vs_fundamental_patterns = [
            r'\b(driven|caused)\b.*(fundamental|macro|currency|usd|rates?)\b',
            r'\b(fundamental|macro)\b.*(driven|factors?|impact)\b',
            r'\b(why is|why are)\b.*(up|down|strong|weak)\b',
            r'\b(usd|inr|dollar|rupee)\b.*(impact|effect|correlation)\b',
            r'\bglobal (tech|cues?|sentiment)\b',
            r'\b(earnings|revenue)\b.*(vs|versus|or)\b.*(macro|currency)\b',
        ]
        
        # STOCK_DEEP_DIVE patterns
        self.stock_deep_dive_patterns = [
            r'\b(detailed|comprehensive|deep|in-?depth|thorough)\b.*(analysis|view|look)\b',
            r'\b(analysis|view|assessment)\b.*(of|on|for)\b.*\b[A-Z]{2,10}\b',
            r'\b(should i|worth|good time)\b.*(buy|invest|sell)\b',
            r'\b(long term|investment|portfolio)\b.*(add|view|perspective)\b',
            r'\b(fundamental|technical)\b.*(analysis|view)\b',
        ]
        
        # MARKET_OVERVIEW patterns
        self.market_overview_patterns = [
            r'\b(market|markets?)\b.*(today|now|overview|summary|status)\b',
            r'\bhow (is|are|was)\b.*(market|nifty|sensex)\b',
            r'\bmarket (update|snapshot|wrap)\b',
            r'\b(what|how)\b.*\bmarket\b.*(doing|performing)\b',
            r'\btoday\'?s? market\b',
            r'\b(latest|recent)\b.*(news|update|market)\b',  # NEW: "latest news"
            r'\bwhat.*latest\b.*(on|about)\b',  # NEW: "what's the latest on"
        ]
        
        # PRICE_CHECK patterns (simple queries - must be specific to avoid matching financials)
        self.price_check_patterns = [
            r'\b(what|what\'?s)\s+(is\s+)?(the\s+)?(price|trading|current|ltp|quote)\b',  # "what is price", "what's the price"
            r'\b(show|get|give)\s+(me\s+)?(the\s+)?(price|ltp|quote)\b',  # "show me the price"
            r'\b(price|ltp|quote)\s+(of|for)\s+\b[A-Z]{2,10}\b',  # "price of TCS"
            r'^[A-Z]{2,10}\s*(price|ltp|current|quote)?$',  # "TCS price" or just "TCS"
            r'\b(current|live|latest)\s+(price|quote|trading)\b',  # "current price"
            r'\b(trading\s+at|priced\s+at)\b',  # "trading at"
            r'\bhow\s+much\s+is\b.*\b(worth|trading|priced)\b',  # "how much is X worth"
        ]
        
        # Compile all patterns
        self.compiled_patterns = {
            QuestionType.INDEX_COMPARISON: [re.compile(p, re.IGNORECASE) for p in self.index_comparison_patterns],
            QuestionType.VERTICAL_ANALYSIS: [re.compile(p, re.IGNORECASE) for p in self.vertical_analysis_patterns],
            QuestionType.SECTOR_ROTATION: [re.compile(p, re.IGNORECASE) for p in self.sector_rotation_patterns],
            QuestionType.SCENARIO_ANALYSIS: [re.compile(p, re.IGNORECASE) for p in self.scenario_analysis_patterns],
            QuestionType.MACRO_VS_FUNDAMENTAL: [re.compile(p, re.IGNORECASE) for p in self.macro_vs_fundamental_patterns],
            QuestionType.STOCK_DEEP_DIVE: [re.compile(p, re.IGNORECASE) for p in self.stock_deep_dive_patterns],
            QuestionType.MARKET_OVERVIEW: [re.compile(p, re.IGNORECASE) for p in self.market_overview_patterns],
            QuestionType.PRICE_CHECK: [re.compile(p, re.IGNORECASE) for p in self.price_check_patterns],
        }
    
    def classify(self, question: str) -> QuestionClassification:
        """
        Classify question into a reasoning path.
        
        Args:
            question: User's question
            
        Returns:
            QuestionClassification with type, confidence, and entities
        """
        scores = {}
        matched_signals = {}
        
        for qtype, patterns in self.compiled_patterns.items():
            matches = []
            for pattern in patterns:
                if pattern.search(question):
                    matches.append(pattern.pattern)
            
            if matches:
                scores[qtype] = len(matches) / len(patterns)
                matched_signals[qtype] = matches
        
        # Extract entities (stocks, sectors, indices)
        entities = self._extract_entities(question)
        
        # If no patterns matched, use entity-based fallback
        if not scores:
            return self._fallback_classification(question, entities)
        
        # Get highest scoring type
        best_type = max(scores, key=scores.get)
        base_confidence = scores[best_type]
        
        # Boost confidence with entity detection
        confidence = base_confidence
        if entities["stocks"]:
            confidence += 0.15  # Stock symbols detected
        if entities["sectors"]:
            confidence += 0.10  # Sector keywords detected
        if len(matched_signals.get(best_type, [])) > 1:
            confidence += 0.10  # Multiple patterns matched
        
        # PRODUCTION FIX: Boost confidence for strong matches
        if best_type == QuestionType.SECTOR_ROTATION and base_confidence > 0.15:
            confidence += 0.30  # Strong sector rotation signal
        elif best_type == QuestionType.MARKET_OVERVIEW and base_confidence > 0.10:
            confidence += 0.25  # Strong market overview signal
        
        # Scale and cap confidence
        confidence = min(confidence * 1.5, 1.0)
        
        return QuestionClassification(
            question_type=best_type,
            confidence=confidence,
            matched_signals=matched_signals.get(best_type, []),
            extracted_entities=entities
        )
    
    def _extract_entities(self, question: str) -> dict:
        """Extract stocks, sectors, and indices from question."""
        entities = {
            "stocks": [],
            "sectors": [],
            "indices": []
        }
        
        # Stock symbols (uppercase 2-10 letters)
        stock_pattern = r'\b([A-Z]{2,10})\b'
        potential_stocks = re.findall(stock_pattern, question)
        
        # Filter out common non-stock words
        non_stocks = {'THE', 'AND', 'FOR', 'WHY', 'HOW', 'WHAT', 'WHICH', 'VIX', 
                      'RSI', 'MACD', 'EMA', 'SMA', 'DMA', 'YOY', 'QOQ', 'IT', 'USD', 'INR'}
        entities["stocks"] = [s for s in potential_stocks if s not in non_stocks]
        
        # Indices
        index_pattern = r'\b(nifty\s*50|nifty|sensex|bank\s*nifty|nifty\s*bank)\b'
        indices = re.findall(index_pattern, question, re.IGNORECASE)
        entities["indices"] = [i.upper().strip() for i in indices]
        
        # Sectors
        sector_keywords = ['it', 'banking', 'auto', 'pharma', 'fmcg', 'metal', 
                          'energy', 'realty', 'infra', 'telecom', 'media']
        question_lower = question.lower()
        entities["sectors"] = [s for s in sector_keywords if s in question_lower]
        
        return entities
    
    def _fallback_classification(self, question: str, entities: dict) -> QuestionClassification:
        """Fallback classification when no patterns match."""
        
        question_lower = question.lower()
        
        # Priority 1: Check for financial/fundamental keywords FIRST
        financial_keywords = ['revenue', 'profit', 'earnings', 'sales', 'margin', 'eps', 
                             'ebitda', 'income', 'expenses', 'financials', 'results']
        valuation_keywords = ['pe', 'p/e', 'pb', 'p/b', 'roe', 'roce', 'ratio', 'valuation']
        corporate_keywords = ['dividend', 'split', 'bonus', 'rights', 'payout']
        
        # If financial keywords detected, classify as STOCK_DEEP_DIVE
        if any(kw in question_lower for kw in financial_keywords + valuation_keywords + corporate_keywords):
            return QuestionClassification(
                question_type=QuestionType.STOCK_DEEP_DIVE,
                confidence=0.65,
                matched_signals=["financial_keywords_detected"],
                extracted_entities=entities
            )
        
        # Priority 2: If asking about specific stock with detail keywords
        if entities["stocks"]:
            detail_keywords = ['analysis', 'view', 'outlook', 'opinion', 'about', 'tell me']
            if any(kw in question_lower for kw in detail_keywords):
                return QuestionClassification(
                    question_type=QuestionType.STOCK_DEEP_DIVE,
                    confidence=0.5,
                    matched_signals=["stock_with_detail_request"],
                    extracted_entities=entities
                )
            else:
                # Simple stock query -> price check or news
                return QuestionClassification(
                    question_type=QuestionType.PRICE_CHECK,
                    confidence=0.5,
                    matched_signals=["stock_symbol_detected"],
                    extracted_entities=entities
                )
        
        # If asking about indices
        if entities["indices"]:
            return QuestionClassification(
                question_type=QuestionType.MARKET_OVERVIEW,
                confidence=0.5,
                matched_signals=["index_detected"],
                extracted_entities=entities
            )
        
        # If asking about sectors
        if entities["sectors"]:
            return QuestionClassification(
                question_type=QuestionType.SECTOR_ROTATION,
                confidence=0.5,
                matched_signals=["sector_detected"],
                extracted_entities=entities
            )
        
        # Default to market overview
        return QuestionClassification(
            question_type=QuestionType.MARKET_OVERVIEW,
            confidence=0.3,
            matched_signals=["default_fallback"],
            extracted_entities=entities
        )


# Singleton
_question_classifier: Optional[QuestionClassifier] = None


def get_question_classifier() -> QuestionClassifier:
    """Get singleton question classifier."""
    global _question_classifier
    if _question_classifier is None:
        _question_classifier = QuestionClassifier()
    return _question_classifier
