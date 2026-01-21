"""
Vertical/Segment Detector
Detects business verticals using rule-based approach with optional LLM enhancement.
"""

import re
from typing import List, Dict, Any, Optional
from ..vertical_config import VERTICAL_KEYWORDS, GROWTH_TERMS


class VerticalDetector:
    """Detect business verticals/segments in text."""
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.vertical_keywords = VERTICAL_KEYWORDS
        self.growth_terms = GROWTH_TERMS
        
    def detect(self, narrative_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect vertical-related chunks from narrative text.
        
        Args:
            narrative_chunks: List of narrative text chunks
            
        Returns:
            List of vertical chunks with metadata
        """
        vertical_chunks = []
        
        for chunk in narrative_chunks:
            text = chunk["text"]
            text_lower = text.lower()
            
            # Detect verticals using rules
            detected = self._rule_based_detection(text, text_lower)
            
            if detected:
                vertical_chunks.append(detected)
        
        return vertical_chunks
    
    def _rule_based_detection(self, text: str, text_lower: str) -> Optional[Dict[str, Any]]:
        """
        Rule-based vertical detection.
        
        Args:
            text: Original text
            text_lower: Lowercase text for matching
            
        Returns:
            Vertical chunk dict or None
        """
        # Check for vertical keywords
        detected_verticals = []
        
        for vertical, keywords in self.vertical_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_verticals.append(vertical)
        
        # Must have at least one vertical
        if not detected_verticals:
            return None
        
        # Must have growth/performance terms
        has_growth_terms = any(term in text_lower for term in self.growth_terms)
        if not has_growth_terms:
            return None
        
        # Must have numbers
        has_numbers = bool(re.search(r'\d', text))
        if not has_numbers:
            return None
        
        # Calculate confidence
        confidence = self._calculate_confidence(text_lower, detected_verticals)
        
        # Enhance with LLM if confidence is low
        enhanced_data = None
        if confidence < 0.7 and self.use_llm:
            from ..llm_client import get_llm_client
            llm_client = get_llm_client()
            enhanced_data = llm_client.enhance_vertical(text, confidence)
        
        return {
            "type": "vertical",
            "verticals": detected_verticals,
            "primary_vertical": detected_verticals[0],
            "text": text,
            "confidence": confidence,
            "enhanced_data": enhanced_data
        }
    
    def _calculate_confidence(self, text_lower: str, detected_verticals: List[str]) -> float:
        """
        Calculate confidence score for vertical detection.
        
        Args:
            text_lower: Lowercase text
            detected_verticals: List of detected verticals
            
        Returns:
            Confidence score (0-1)
        """
        score = 0.0
        
        # Base score for having verticals
        score += 0.3
        
        # Bonus for multiple verticals
        if len(detected_verticals) > 1:
            score += 0.1
        
        # Bonus for growth terms
        growth_count = sum(1 for term in self.growth_terms if term in text_lower)
        score += min(growth_count * 0.1, 0.3)
        
        # Bonus for percentages
        percentage_count = len(re.findall(r'\d+\.?\d*%', text_lower))
        score += min(percentage_count * 0.1, 0.3)
        
        return min(score, 1.0)
