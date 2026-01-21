"""
Pattern-Based Intent Mapper.

Maps user queries to canonical intents using pattern matching.
Fast, deterministic, and no LLM calls needed for most queries.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.blueprints.canonical_intents import CanonicalIntent


@dataclass
class IntentClassification:
    """Result of intent classification."""
    intent: CanonicalIntent
    confidence: float
    reasoning: str
    matched_pattern: Optional[str] = None


class IntentMapper:
    """
    Pattern-based intent classifier.
    
    Uses regex patterns and keyword matching to classify queries
    into canonical intents. Fast and deterministic.
    """
    
    def __init__(self):
        """Initialize intent patterns."""
        self.patterns = self._build_patterns()
    
    def _build_patterns(self) -> Dict[CanonicalIntent, List[Tuple[str, float]]]:
        """
        Build regex patterns for each intent.
        
        Returns:
            Dict mapping intent to list of (pattern, confidence) tuples
        """
        return {
            # STOCK_OVERVIEW patterns
            CanonicalIntent.STOCK_OVERVIEW: [
                (r'\b(tell me about|what (is|does)|overview of|profile of|about)\b.*\b(company|stock|business)\b', 0.95),
                (r'\b(tell me about|what (is|does)|overview of|profile of)\b', 0.85),
                (r'\b(company profile|business model|what they do)\b', 0.90),
            ],
            
            # STOCK_DEEP_DIVE patterns
            CanonicalIntent.STOCK_DEEP_DIVE: [
                (r'\b(should i (buy|invest|purchase)|is .* (good|worth)|investment (thesis|case|analysis))\b', 0.95),
                (r'\b(bull case|bear case|bullish|bearish)\b', 0.90),
                (r'\b(buy or sell|hold or sell|investment recommendation)\b', 0.95),
                (r'\b(long term investment|worth investing)\b', 0.85),
            ],
            
            # STOCK_COMPARISON patterns
            CanonicalIntent.STOCK_COMPARISON: [
                (r'\b(vs|versus|or|compare)\b.*\b(vs|versus|or|compare)\b', 0.95),
                (r'\b(which is better|better than|comparison between)\b', 0.90),
                (r'\b(compare .* (and|with))\b', 0.90),
                (r'\b(.* or .*)\?', 0.80),  # "TCS or Infosys?"
            ],
            
            # STOCK_SCREENING patterns
            CanonicalIntent.STOCK_SCREENING: [
                (r'\b(best|top|good) .* (stocks|companies|picks)\b', 0.95),
                (r'\b(stock (recommendations|picks|ideas|suggestions))\b', 0.90),
                (r'\b(which stocks (to buy|should i))\b', 0.95),
                (r'\b(find .* stocks|stocks (in|for))\b', 0.85),
            ],
            
            # PRICE_ACTION patterns
            CanonicalIntent.PRICE_ACTION: [
                # Explicit price queries (highest priority)
                (r'\b(latest|current|today\'?s?|live) price (of|for)\b', 0.95),
                (r'\b(price of|price for)\b', 0.95),
                (r'\b(what\'?s? (the )?price|show (me )?(the )?price)\b', 0.95),
                (r'\b(how much is|quote (of|for))\b', 0.90),
                (r'^\s*[A-Z]{2,10}\s+(price|quote|ltp)\s*$', 0.95),  # "TCS price", "INFY quote"
                (r'^\s*price\s+(of|for)\s+[A-Z]{2,10}\s*$', 0.95),  # "price of TCS"
                # Technical analysis patterns
                (r'\b(technical analysis|chart analysis|price action)\b', 0.95),
                (r'\b(support|resistance|levels|breakout|breakdown)\b', 0.90),
                (r'\b(moving average|rsi|macd|indicators)\b', 0.95),
                (r'\b(trend|momentum|overbought|oversold)\b', 0.85),
            ],
            
            # SECTOR_OVERVIEW patterns
            CanonicalIntent.SECTOR_OVERVIEW: [
                (r'\b(sector (analysis|overview|performance|outlook))\b', 0.95),
                (r'\b(how is .* sector|what.*happening in .* sector)\b', 0.90),
                (r'\b(it sector|banking sector|auto sector|pharma sector)\b.*\b(performing|doing|analysis)\b', 0.85),
            ],
            
            # SECTOR_ROTATION patterns (includes market overview and news)
            CanonicalIntent.SECTOR_ROTATION: [
                (r'\b(sector rotation|rotating|outperforming sectors)\b', 0.95),
                (r'\b(which sectors (are|is)|sector momentum)\b', 0.90),
                (r'\b(sector (leaders|laggards|performance))\b', 0.85),
                (r'\b(which sector.*\b(growing|growth|best|performing|outperforming))\b', 0.90),
                (r'\b(sector.*\b(this year|this quarter|recently|now))\b', 0.85),
                (r'\b(growing sector|best sector|top sector)\b', 0.90),
                # Market news and overview patterns
                (r'\b(market (news|overview|update|summary))\b', 0.95),
                (r'\b(latest (market |global )?news)\b', 0.95),
                (r'\b(what.*happening (in|to) (the )?market)\b', 0.90),
                (r'\b(market (today|now|currently))\b', 0.85),
                (r'\b(top (gainers|losers|performers))\b', 0.90),
            ],
            
            # STOCK_DEEP_DIVE patterns
            CanonicalIntent.STOCK_DEEP_DIVE: [
                (r'\b(should i buy|should i invest in|is .* a good (investment|buy|stock))\b', 0.95),
                (r'\b(investment (analysis|verdict|opinion|view) (on|for))\b', 0.90),
                (r'\b(bull (and|&) bear case|bull case|bear case)\b', 0.95),
                (r'\b(what.*(your|the) (verdict|opinion|view|recommendation) on)\b', 0.90),
                (r'\b(worth (buying|investing)|good time to buy)\b', 0.85),
            ],
            
            # SECTOR_COMPARISON patterns
            CanonicalIntent.SECTOR_COMPARISON: [
                (r'\b(compare|comparison)\b.*\b(sector|industry)\b.*\b(and|vs|versus)\b.*\b(sector|industry)\b', 0.95),
                (r'\b(it|banking|auto|pharma|energy|fmcg)\b.*\b(vs|versus)\b.*\b(it|banking|auto|pharma|energy|fmcg)\b.*\bsector\b', 0.90),
                (r'\b(which|what) (is|are) better.*\b(sector|industry)\b', 0.85),
            ],
            
            # RISK_ANALYSIS patterns
            CanonicalIntent.RISK_ANALYSIS: [
                (r'\b(risk|risks|downside|what could go wrong)\b', 0.90),
                (r'\b(risk analysis|risk assessment|risk factors)\b', 0.95),
                (r'\b(concerns|worries|threats|challenges)\b', 0.80),
            ],
            
            # TRADE_IDEA patterns
            CanonicalIntent.TRADE_IDEA: [
                (r'\b(trade (idea|setup|recommendation)|trading (idea|setup))\b', 0.95),
                (r'\b(how to trade|entry (point|level)|exit (point|level))\b', 0.90),
                (r'\b(give me a trade|trade for)\b', 0.90),
                (r'\b(stop loss|target|take profit)\b', 0.85),
            ],
        }
    
    def classify(self, query: str, symbols: Optional[List[str]] = None) -> IntentClassification:
        """
        Classify query into canonical intent.
        
        Args:
            query: User query
            symbols: Detected stock symbols (optional)
        
        Returns:
            IntentClassification with intent, confidence, and reasoning
        """
        query_lower = query.lower().strip()
        
        # Track best match
        best_intent = None
        best_confidence = 0.0
        best_pattern = None
        
        # Try pattern matching for each intent
        for intent, patterns in self.patterns.items():
            for pattern, base_confidence in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    # Boost confidence if symbols are present and required
                    confidence = base_confidence
                    if symbols and self._requires_symbols(intent):
                        confidence = min(1.0, confidence + 0.05)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent
                        best_pattern = pattern
        
        # Fallback logic if no pattern matched
        if best_intent is None:
            best_intent, best_confidence = self._fallback_classification(query_lower, symbols)
            best_pattern = "fallback"
        
        # Build reasoning
        reasoning = f"Matched pattern: {best_pattern}" if best_pattern != "fallback" else "Fallback classification"
        if symbols:
            reasoning += f" | Symbols: {', '.join(symbols)}"
        
        return IntentClassification(
            intent=best_intent,
            confidence=best_confidence,
            reasoning=reasoning,
            matched_pattern=best_pattern
        )
    
    def _requires_symbols(self, intent: CanonicalIntent) -> bool:
        """Check if intent requires stock symbols."""
        from src.blueprints.canonical_intents import get_intent_requirements
        return get_intent_requirements(intent).get("requires_symbols", False)
    
    def _fallback_classification(self, query: str, symbols: Optional[List[str]]) -> Tuple[CanonicalIntent, float]:
        """
        Fallback classification when no pattern matches.
        
        Uses heuristics based on symbols and keywords.
        Priority: mutual_fund check > symbols > specific keywords > general fallback
        """
        # PRIORITY 0: Check for mutual fund keywords (should use legacy MUTUAL_FUND intent)
        mutual_fund_keywords = ['sip', 'mutual fund', 'mf', 'elss', 'nfo', 'fund', 'investment plan']
        if any(keyword in query for keyword in mutual_fund_keywords):
            # Return low confidence so legacy MUTUAL_FUND intent takes precedence
            return CanonicalIntent.STOCK_OVERVIEW, 0.30
        
        # PRIORITY 1: If symbols present, it's likely a stock query
        if symbols:
            # Check for comparison keywords
            if any(word in query for word in ['vs', 'versus', 'or', 'compare']):
                return CanonicalIntent.STOCK_COMPARISON, 0.70
            
            # Check for price/technical keywords (ENHANCED)
            price_keywords = ['price', 'quote', 'ltp', 'latest', 'current', 'today', 'live']
            if any(word in query for word in price_keywords):
                return CanonicalIntent.PRICE_ACTION, 0.90  # Increased confidence
            
            # Check for technical keywords
            if any(word in query for word in ['chart', 'technical', 'level', 'support', 'resistance']):
                return CanonicalIntent.PRICE_ACTION, 0.70
            
            # Check for performance/analysis keywords (stock-specific)
            if any(word in query for word in ['performance', 'analysis', 'doing', 'how is']):
                return CanonicalIntent.STOCK_OVERVIEW, 0.75
            
            # Default to overview for any query with symbols
            return CanonicalIntent.STOCK_OVERVIEW, 0.70
        
        # PRIORITY 2: Check for sector keywords (ONLY if no symbols)
        sector_keywords = ['sector', 'industry']  # Removed ambiguous keywords like 'it', 'banking'
        if any(word in query for word in sector_keywords):
            return CanonicalIntent.SECTOR_OVERVIEW, 0.65
        
        # PRIORITY 3: Check for screening keywords
        if any(word in query for word in ['best', 'top', 'find', 'which stocks']):
            return CanonicalIntent.STOCK_SCREENING, 0.65
        
        # Ultimate fallback: STOCK_OVERVIEW
        return CanonicalIntent.STOCK_OVERVIEW, 0.50


# Singleton instance
_intent_mapper: Optional[IntentMapper] = None


def get_intent_mapper() -> IntentMapper:
    """Get singleton intent mapper instance."""
    global _intent_mapper
    if _intent_mapper is None:
        _intent_mapper = IntentMapper()
    return _intent_mapper
