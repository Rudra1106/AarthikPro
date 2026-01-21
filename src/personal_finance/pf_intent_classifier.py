"""
Personal Finance Intent Classifier

Classifies PF queries into 5 intent types using the 3-bucket approach:
- Generic advice (PF_EDUCATION)
- Semi-personal advice (PF_EVALUATION, PF_MARKET_CONTEXT)
- Fully personal (PF_ACTION, PF_GOAL_PLANNING)

Design: Intent-first, not form-first. Progressive disclosure.
"""
import re
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass


class PFIntent(str, Enum):
    """Personal Finance intent categories."""
    PF_EDUCATION = "pf_education"              # Generic: "What is SIP?" - No questions
    PF_EVALUATION = "pf_evaluation"            # Semi-personal: "Is SIP good?" - Optional context
    PF_ACTION = "pf_action"                    # Fully personal: "How much to invest?" - Gated
    PF_GOAL_PLANNING = "pf_goal_planning"      # Fully personal: "Save 10L in 5 years?" - Gated
    PF_MARKET_CONTEXT = "pf_market_context"    # Semi-personal: "Markets falling, stop SIP?" - Light context


@dataclass
class PFIntentClassification:
    """Result of PF intent classification."""
    intent: PFIntent
    confidence: float
    personalization_level: str  # "none", "optional", "required"
    matched_patterns: List[str]
    
    def needs_user_data(self) -> bool:
        """Check if this intent requires user data."""
        return self.personalization_level == "required"
    
    def allows_optional_personalization(self) -> bool:
        """Check if this intent allows optional personalization."""
        return self.personalization_level == "optional"


class PFIntentClassifier:
    """
    Fast, rule-based PF intent classifier.
    
    3-Bucket Classification:
    1. Generic (no questions) → PF_EDUCATION
    2. Semi-personal (optional context) → PF_EVALUATION, PF_MARKET_CONTEXT
    3. Fully personal (gated) → PF_ACTION, PF_GOAL_PLANNING
    """
    
    def __init__(self):
        # PF_EDUCATION: Concepts, definitions, explanations
        self.education_patterns = [
            r'\b(what is|what are|explain|define|meaning of|tell me about)\b',
            r'\b(how does|how do|how to understand)\b.*\b(work|function)',
            r'\b(emergency fund|sip|mutual fund|elss|nps|ppf|fd|equity|debt)\b.*\b(concept|basics?|definition)',
            r'\b(difference between|compare)\b.*\b(sip|mutual fund|equity|debt|fd)',
            r'\b(types? of)\b.*\b(mutual funds?|investments?|insurance)',
        ]
        
        # PF_EVALUATION: "Is X good?" - Semi-personal
        self.evaluation_patterns = [
            r'\b(is|are)\b.*\b(good|safe|risky|suitable|worth|advisable|recommended)\b',
            r'\b(should i|can i|is it good to)\b.*\b(invest|start|buy|consider)\b',
            r'\b(pros and cons|advantages|disadvantages|benefits|risks)\b.*\b(of|for)',
            r'\b(sip|mutual fund|equity|debt|fd|nps|ppf)\b.*\b(good|safe|risky|suitable)\b',
            r'\b(better|best)\b.*\b(option|choice|investment)\b',
        ]
        
        # PF_ACTION: "How much should I invest?" - Fully personal (GATED)
        self.action_patterns = [
            r'\b(how much|what amount)\b.*\b(should i|can i|to)\b.*\b(invest|save|allocate)\b',
            r'\b(how much)\b.*\b(monthly|per month|every month)\b',
            r'\b(calculate|suggest|recommend)\b.*\b(investment|savings|allocation)\b',
            r'\b(portfolio|asset)\b.*\b(allocation|distribution|split)\b',
            r'\b(where|how)\b.*\b(should i|can i)\b.*\b(invest|put|allocate)\b.*\b(money|savings|income)\b',
        ]
        
        # PF_GOAL_PLANNING: Goal-based calculations - Fully personal (GATED)
        self.goal_planning_patterns = [
            r'\b(save|accumulate|build|reach)\b.*\b(\d+\s*(lakh|crore|thousand|k|L|cr)|target|goal)\b',
            r'\b(goal|target|plan)\b.*\b(for|to)\b.*\b(retirement|house|car|education|wedding)\b',
            r'\b(how (can|do) i|help me)\b.*\b(save|reach|achieve)\b.*\b(in \d+|within)',
            r'\b(retirement|education|house|car)\b.*\b(planning|fund|corpus)',
            r'\b(need|want|planning)\b.*\b(\d+\s*(lakh|crore|L|cr))\b.*\b(in \d+|by \d{4})',
        ]
        
        # PF_MARKET_CONTEXT: Market conditions + personal impact - Semi-personal
        self.market_context_patterns = [
            r'\b(market|markets?)\b.*\b(falling|crashing|down|volatile|correction)\b',
            r'\b(should i|can i)\b.*\b(stop|pause|continue|increase)\b.*\b(sip|investment)\b',
            r'\b(market|nifty|sensex)\b.*\b(impact|affect|effect)\b.*\b(my|portfolio)',
            r'\b(good time|right time|when)\b.*\b(to|for)\b.*\b(invest|enter|buy)\b',
            r'\b(inflation|recession|rate hike)\b.*\b(impact|affect|should i)\b',
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = {
            PFIntent.PF_EDUCATION: [re.compile(p, re.IGNORECASE) for p in self.education_patterns],
            PFIntent.PF_EVALUATION: [re.compile(p, re.IGNORECASE) for p in self.evaluation_patterns],
            PFIntent.PF_ACTION: [re.compile(p, re.IGNORECASE) for p in self.action_patterns],
            PFIntent.PF_GOAL_PLANNING: [re.compile(p, re.IGNORECASE) for p in self.goal_planning_patterns],
            PFIntent.PF_MARKET_CONTEXT: [re.compile(p, re.IGNORECASE) for p in self.market_context_patterns],
        }
        
        # Personalization level mapping
        self.personalization_map = {
            PFIntent.PF_EDUCATION: "none",           # Generic
            PFIntent.PF_EVALUATION: "optional",      # Semi-personal
            PFIntent.PF_MARKET_CONTEXT: "optional",  # Semi-personal
            PFIntent.PF_ACTION: "required",          # Fully personal
            PFIntent.PF_GOAL_PLANNING: "required",   # Fully personal
        }
    
    def classify(self, query: str) -> PFIntentClassification:
        """
        Classify PF query intent.
        
        Priority order (highest to lowest):
        1. PF_ACTION (gated advice)
        2. PF_GOAL_PLANNING (goal calculations)
        3. PF_MARKET_CONTEXT (market + personal)
        4. PF_EVALUATION (semi-personal)
        5. PF_EDUCATION (generic)
        
        Args:
            query: User's query string
            
        Returns:
            PFIntentClassification with intent and personalization level
        """
        query_lower = query.lower()
        
        # Score each intent
        intent_scores = {}
        matched_patterns = {}
        
        for intent, patterns in self.compiled_patterns.items():
            matches = []
            for pattern in patterns:
                if pattern.search(query_lower):
                    matches.append(pattern.pattern)
            
            if matches:
                matched_patterns[intent] = matches
                # Score based on number of matches
                intent_scores[intent] = len(matches) / len(patterns)
        
        # No matches - default to EDUCATION
        if not intent_scores:
            return PFIntentClassification(
                intent=PFIntent.PF_EDUCATION,
                confidence=0.5,
                personalization_level="none",
                matched_patterns=[]
            )
        
        # Sort by score
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        primary_intent, primary_score = sorted_intents[0]
        
        # PRIORITY BOOST: Gated intents (ACTION, GOAL_PLANNING) take precedence
        # This ensures we don't accidentally give personalized advice without data
        gated_intents = [PFIntent.PF_ACTION, PFIntent.PF_GOAL_PLANNING]
        for gated_intent in gated_intents:
            if gated_intent in intent_scores and intent_scores[gated_intent] > 0:
                # If gated intent scored, boost it
                if gated_intent == primary_intent or intent_scores[gated_intent] >= primary_score * 0.6:
                    return PFIntentClassification(
                        intent=gated_intent,
                        confidence=min(intent_scores[gated_intent] * 1.5, 0.95),
                        personalization_level=self.personalization_map[gated_intent],
                        matched_patterns=matched_patterns.get(gated_intent, [])
                    )
        
        # Return primary intent
        return PFIntentClassification(
            intent=primary_intent,
            confidence=min(primary_score * 1.3, 1.0),
            personalization_level=self.personalization_map[primary_intent],
            matched_patterns=matched_patterns.get(primary_intent, [])
        )


# Singleton instance
_pf_classifier_instance: Optional[PFIntentClassifier] = None


def get_pf_intent_classifier() -> PFIntentClassifier:
    """Get singleton PF intent classifier instance."""
    global _pf_classifier_instance
    if _pf_classifier_instance is None:
        _pf_classifier_instance = PFIntentClassifier()
    return _pf_classifier_instance
