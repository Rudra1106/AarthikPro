"""
TL;DR Generator - Generate question-specific summaries.

Rule: TL;DR must ANSWER THE QUESTION, not describe the day.

BAD: "Nifty closed slightly lower..."
GOOD: "HDFC Bank (-0.29%) dragged Nifty while ICICI Bank supported Bank Nifty"
"""
from typing import Dict, Any, Optional
import logging

from src.intelligence.question_classifier import QuestionType
from src.intelligence.answer_blueprints import AnswerBlueprint, get_blueprint

logger = logging.getLogger(__name__)


class TLDRGenerator:
    """
    Generate question-specific TL;DR.
    
    The TL;DR should:
    1. Directly answer the question
    2. Be specific with numbers
    3. Not be a generic market description
    """
    
    def generate(
        self,
        question: str,
        question_type: QuestionType,
        data: Dict[str, Any]
    ) -> str:
        """
        Generate TL;DR for the specific question type.
        
        Args:
            question: Original user question
            question_type: Classified question type
            data: Available data for the answer
            
        Returns:
            Question-specific TL;DR string
        """
        generators = {
            QuestionType.INDEX_COMPARISON: self._index_comparison_tldr,
            QuestionType.VERTICAL_ANALYSIS: self._vertical_analysis_tldr,
            QuestionType.SECTOR_ROTATION: self._sector_rotation_tldr,
            QuestionType.SCENARIO_ANALYSIS: self._scenario_analysis_tldr,
            QuestionType.MACRO_VS_FUNDAMENTAL: self._macro_fundamental_tldr,
            QuestionType.STOCK_DEEP_DIVE: self._stock_deep_dive_tldr,
            QuestionType.MARKET_OVERVIEW: self._market_overview_tldr,
            QuestionType.PRICE_CHECK: self._price_check_tldr,
        }
        
        generator = generators.get(question_type, self._market_overview_tldr)
        
        try:
            return generator(question, data)
        except Exception as e:
            logger.error(f"Error generating TL;DR: {e}")
            return self._fallback_tldr(question, data)
    
    def _index_comparison_tldr(self, question: str, data: Dict[str, Any]) -> str:
        """TL;DR for index comparison questions."""
        # Extract attribution data
        attribution = data.get("attribution", {})
        top_positive = attribution.get("top_positive", [])
        top_negative = attribution.get("top_negative", [])
        
        index_a = data.get("index_a", "Nifty")
        index_b = data.get("index_b", "Bank Nifty")
        direction = data.get("relative_direction", "underperformed")
        
        # Build reason from top contributors
        reasons = []
        if top_negative:
            stock = top_negative[0]
            reasons.append(f"{stock.get('symbol', 'heavyweight')} ({stock.get('change', 0):+.2f}%) dragging")
        if top_positive:
            stock = top_positive[0]
            reasons.append(f"{stock.get('symbol', 'stock')} ({stock.get('change', 0):+.2f}%) supporting")
        
        reason_text = " while ".join(reasons) if reasons else "mixed heavyweight performance"
        
        return f"{index_a} {direction} {index_b} because {reason_text}"
    
    def _vertical_analysis_tldr(self, question: str, data: Dict[str, Any]) -> str:
        """TL;DR for vertical/segment analysis questions."""
        company = data.get("company", "Company")
        verticals = data.get("verticals", [])
        
        if verticals:
            top_vertical = verticals[0]
            vertical_name = top_vertical.get("name", "primary vertical")
            growth = top_vertical.get("growth_pct", 0)
            contribution = top_vertical.get("contribution_pct", 0)
            
            sustainability = self._assess_sustainability(top_vertical)
            
            return f"{company}'s {vertical_name} ({contribution:.0f}% of revenue) is growing at {growth:.1f}% QoQ, {sustainability}"
        else:
            return f"{company}'s segment data not available for detailed vertical analysis"
    
    def _assess_sustainability(self, vertical: Dict[str, Any]) -> str:
        """Assess sustainability of vertical growth."""
        growth = vertical.get("growth_pct", 0)
        margin = vertical.get("margin_pct", 0)
        
        if growth > 10 and margin > 15:
            return "likely sustainable for 2+ quarters"
        elif growth > 5:
            return "moderately sustainable with margin watch"
        else:
            return "sustainability uncertain, needs monitoring"
    
    def _sector_rotation_tldr(self, question: str, data: Dict[str, Any]) -> str:
        """
        TL;DR for sector rotation questions - Bloomberg-grade.
        
        Must include:
        - Conviction level
        - Breadth context
        - Relative vs absolute clarity
        """
        sectors = data.get("sectors", [])
        nifty_change = data.get("nifty_change", 0)
        conviction = data.get("market_conviction", "Low")
        
        if not sectors:
            return "Sector performance data not available for rotation analysis"
        
        top_sector = sectors[0]
        sector_name = top_sector.get("name", "Top sector")
        sector_change = top_sector.get("change_pct", 0)
        
        # Get breadth data (now a dict)
        breadth_data = top_sector.get("breadth", {})
        if isinstance(breadth_data, dict):
            breadth_pct = breadth_data.get("pct_positive", 0)
            breadth_count = f"{breadth_data.get('advancing', 0)}/{breadth_data.get('total', 0)}"
        else:
            # Fallback for old format
            breadth_pct = breadth_data * 100 if breadth_data else 0
            breadth_count = f"{breadth_pct:.0f}%"
        
        relative = sector_change - nifty_change
        relative_str = f"+{relative:.2f}%" if relative > 0 else f"{relative:.2f}%"
        
        # Bloomberg-grade language based on conviction
        if breadth_pct < 30 and abs(sector_change) < 0.5:
            # Low conviction, flat market
            return (f"{sector_name} is the only sector marginally outperforming Nifty "
                   f"({relative_str} relative), but leadership is narrow ({breadth_count} stocks advancing, "
                   f"{breadth_pct:.0f}% breadth) and low-conviction. "
                   f"Most sectors correcting suggests cautious positioning, not aggressive rotation.")
        elif breadth_pct < 40:
            # Narrow leadership
            return (f"{sector_name} leads with {sector_change:+.2f}% ({relative_str} vs Nifty), "
                   f"but breadth is narrow ({breadth_count}, {breadth_pct:.0f}%) - "
                   f"gains are stock-specific, not sector-wide")
        elif breadth_pct > 70:
            # Strong, broad-based
            return (f"{sector_name} shows strong leadership: {sector_change:+.2f}% ({relative_str} vs Nifty) "
                   f"with broad participation ({breadth_count}, {breadth_pct:.0f}% breadth)")
        else:
            # Mixed
            return (f"{sector_name} is relative outperformer at {sector_change:+.2f}% ({relative_str} vs Nifty), "
                   f"with mixed breadth ({breadth_count}, {breadth_pct:.0f}%)")
    
    def _scenario_analysis_tldr(self, question: str, data: Dict[str, Any]) -> str:
        """TL;DR for scenario analysis questions."""
        condition = data.get("condition", "current conditions")
        base_case = data.get("base_case", {})
        
        outcome = base_case.get("outcome", "range-bound movement")
        probability = base_case.get("probability", 50)
        
        return f"With {condition}, most likely outcome is {outcome} ({probability}% probability)"
    
    def _macro_fundamental_tldr(self, question: str, data: Dict[str, Any]) -> str:
        """TL;DR for macro vs fundamental questions."""
        entity = data.get("entity", "Asset")
        fundamental_weight = data.get("fundamental_weight", 50)
        macro_weight = data.get("macro_weight", 50)
        
        if fundamental_weight > macro_weight:
            driver = "fundamentally"
            reason = data.get("fundamental_reason", "earnings momentum")
        else:
            driver = "macro"
            reason = data.get("macro_reason", "currency and global sentiment")
        
        return f"{entity} strength is {driver}-driven ({fundamental_weight}% fundamental, {macro_weight}% macro) due to {reason}"
    
    def _stock_deep_dive_tldr(self, question: str, data: Dict[str, Any]) -> str:
        """TL;DR for stock deep dive questions."""
        stock = data.get("stock", "Stock")
        price = data.get("price", 0)
        valuation = data.get("valuation_view", "fairly valued")
        growth = data.get("growth_view", "moderate growth")
        risk = data.get("risk_level", "medium")
        
        return f"{stock} is {valuation} at ₹{price:,.2f}, showing {growth} with {risk} risk profile"
    
    def _market_overview_tldr(self, question: str, data: Dict[str, Any]) -> str:
        """TL;DR for market overview questions."""
        nifty = data.get("nifty", {})
        price = nifty.get("price", 0)
        change = nifty.get("change_pct", 0)
        
        sectors = data.get("sectors", [])
        top_sector = sectors[0].get("name", "IT") if sectors else "N/A"
        
        # Determine sentiment
        if change > 0.5:
            sentiment = "bullish"
        elif change < -0.5:
            sentiment = "bearish"
        else:
            sentiment = "range-bound"
        
        return f"Markets are {sentiment} with Nifty at ₹{price:,.2f} ({change:+.2f}%), led by {top_sector}"
    
    def _price_check_tldr(self, question: str, data: Dict[str, Any]) -> str:
        """TL;DR for simple price check questions."""
        stock = data.get("stock", "Stock")
        price = data.get("price", 0)
        change = data.get("change_pct", 0)
        
        return f"{stock} is trading at ₹{price:,.2f} ({change:+.2f}%)"
    
    def _fallback_tldr(self, question: str, data: Dict[str, Any]) -> str:
        """Fallback TL;DR when specific generator fails."""
        nifty = data.get("nifty", {})
        if nifty:
            return f"Market overview: Nifty at ₹{nifty.get('price', 0):,.2f}"
        return "Analysis based on available data"


# Singleton
_tldr_generator: Optional[TLDRGenerator] = None


def get_tldr_generator() -> TLDRGenerator:
    """Get singleton TL;DR generator."""
    global _tldr_generator
    if _tldr_generator is None:
        _tldr_generator = TLDRGenerator()
    return _tldr_generator
