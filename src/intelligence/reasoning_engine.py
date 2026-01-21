"""
Reasoning Engine - Transform Raw Data into Intelligent Insights.

This module interprets financial data and provides context-aware analysis
instead of just dumping numbers.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValuationInsight:
    """Valuation interpretation result."""
    interpretation: str
    risk_level: str  # "low", "medium", "high"
    justification: str


@dataclass
class TrendInsight:
    """Trend analysis result."""
    direction: str  # "accelerating", "stable", "decelerating", "declining"
    interpretation: str
    confidence: float


class ReasoningEngine:
    """
    Transform raw financial data into intelligent insights.
    
    Components:
    - Valuation interpretation (P/E, P/B context)
    - Trend analysis (growth acceleration/deceleration)
    - Shareholding interpretation (FII/DII activity)
    - Risk assessment
    """
    
    def interpret_valuation(
        self,
        stock_data: Dict[str, Any],
        sector_avg: Optional[Dict[str, Any]] = None
    ) -> ValuationInsight:
        """
        Interpret valuation metrics with context.
        
        Args:
            stock_data: Stock metrics (pe_ratio, pb_ratio, growth_rate, etc.)
            sector_avg: Sector average metrics for comparison
            
        Returns:
            ValuationInsight with interpretation and risk level
            
        Example:
            Input: {pe: 78, growth_rate: 45}
            Output: "Trades at a premium (P/E 78), justified by strong growth (45% YoY)"
        """
        pe = stock_data.get("pe_ratio")
        pb = stock_data.get("pb_ratio")
        growth = stock_data.get("revenue_growth_yoy", 0)
        market_cap = stock_data.get("market_cap", 0)
        
        if not pe or pe <= 0:
            return ValuationInsight(
                interpretation="P/E ratio not available or negative (loss-making)",
                risk_level="high",
                justification="Company may be unprofitable or in turnaround phase"
            )
        
        # Get sector average for comparison
        sector_pe = sector_avg.get("pe_ratio", 20) if sector_avg else 20
        
        # Calculate premium/discount
        premium = ((pe - sector_pe) / sector_pe) * 100 if sector_pe > 0 else 0
        
        # Reasoning logic
        if pe > 100:  # Extremely high P/E
            if growth > 50:
                interpretation = f"Trades at an extremely high valuation (P/E {pe:.1f}), reflecting exceptional growth expectations ({growth:.1f}% YoY). Highly sensitive to any earnings miss."
                risk_level = "high"
                justification = "Premium justified by hypergrowth, but leaves little room for error"
            else:
                interpretation = f"Appears significantly overvalued (P/E {pe:.1f}) with modest growth ({growth:.1f}% YoY). Consider waiting for correction."
                risk_level = "very_high"
                justification = "Valuation not supported by growth fundamentals"
                
        elif pe > 40:  # High P/E
            if growth > 30:
                interpretation = f"Trades at a premium (P/E {pe:.1f} vs sector {sector_pe:.1f}), justified by strong growth ({growth:.1f}% YoY). Monitor execution closely."
                risk_level = "medium"
                justification = "Growth premium priced in, execution risk remains"
            else:
                interpretation = f"Trades at a premium (P/E {pe:.1f} vs sector {sector_pe:.1f}) with moderate growth ({growth:.1f}% YoY). Valuation appears stretched."
                risk_level = "high"
                justification = "Premium not fully justified by growth rate"
                
        elif pe > 20:  # Moderate P/E
            interpretation = f"Reasonably valued (P/E {pe:.1f} vs sector {sector_pe:.1f}), reflecting market expectations."
            risk_level = "low"
            justification = "Valuation in line with sector averages"
            
        elif pe > 10:  # Low P/E
            interpretation = f"Trades at a discount (P/E {pe:.1f} vs sector {sector_pe:.1f}), potential value opportunity or underlying concerns."
            risk_level = "medium"
            justification = "Discount may indicate value or hidden risks"
            
        else:  # Very low P/E
            interpretation = f"Trades at a significant discount (P/E {pe:.1f}), investigate for value trap or cyclical bottom."
            risk_level = "medium"
            justification = "Deep discount warrants investigation"
        
        return ValuationInsight(
            interpretation=interpretation,
            risk_level=risk_level,
            justification=justification
        )
    
    def analyze_trend(
        self,
        trend_data: List[Dict[str, Any]],
        metric_name: str = "revenue"
    ) -> TrendInsight:
        """
        Analyze revenue/profit trends to detect acceleration or deceleration.
        
        Args:
            trend_data: List of quarterly/annual data points with 'value' field
            metric_name: Name of metric being analyzed
            
        Returns:
            TrendInsight with direction and interpretation
        """
        if len(trend_data) < 4:
            return TrendInsight(
                direction="unknown",
                interpretation=f"Insufficient data for {metric_name} trend analysis (need 4+ periods).",
                confidence=0.0
            )
        
        # Calculate growth rates
        growth_rates = []
        for i in range(1, len(trend_data)):
            prev = trend_data[i-1].get("value", 0)
            curr = trend_data[i].get("value", 0)
            if prev > 0:
                growth = ((curr - prev) / prev) * 100
                growth_rates.append(growth)
        
        if not growth_rates:
            return TrendInsight(
                direction="unknown",
                interpretation=f"Unable to calculate {metric_name} growth rates.",
                confidence=0.0
            )
        
        # Detect acceleration/deceleration
        if len(growth_rates) >= 3:
            recent_avg = sum(growth_rates[-2:]) / 2
            older_avg = sum(growth_rates[:2]) / 2
            
            if recent_avg > older_avg + 5:
                return TrendInsight(
                    direction="accelerating",
                    interpretation=f"{metric_name.capitalize()} growth accelerating (recent: {recent_avg:.1f}% vs earlier: {older_avg:.1f}%), strong momentum.",
                    confidence=0.85
                )
            elif recent_avg < older_avg - 5:
                return TrendInsight(
                    direction="decelerating",
                    interpretation=f"{metric_name.capitalize()} growth decelerating (recent: {recent_avg:.1f}% vs earlier: {older_avg:.1f}%), momentum slowing.",
                    confidence=0.85
                )
        
        # Check if declining
        avg_growth = sum(growth_rates) / len(growth_rates)
        if avg_growth < -5:
            return TrendInsight(
                direction="declining",
                interpretation=f"{metric_name.capitalize()} declining (avg: {avg_growth:.1f}% per period), turnaround needed.",
                confidence=0.90
            )
        
        # Stable growth
        return TrendInsight(
            direction="stable",
            interpretation=f"{metric_name.capitalize()} growing consistently (avg: {avg_growth:.1f}% per period).",
            confidence=0.80
        )
    
    def interpret_shareholding(
        self,
        trends: Dict[str, Any]
    ) -> str:
        """
        Interpret FII/DII/Promoter shareholding activity.
        
        Args:
            trends: Dict with fii_direction, fii_change, dii_direction, etc.
            
        Returns:
            Human-readable interpretation
        """
        fii_direction = trends.get("fii_direction", "stable")
        fii_change = trends.get("fii_change", 0)
        dii_direction = trends.get("dii_direction", "stable")
        dii_change = trends.get("dii_change", 0)
        promoter_change = trends.get("promoter_change", 0)
        
        insights = []
        
        # FII activity
        if fii_direction == "increasing" and fii_change > 2:
            insights.append(f"Strong foreign institutional buying (FII +{fii_change:.1f}%), indicating global confidence.")
        elif fii_direction == "decreasing" and fii_change < -2:
            insights.append(f"Foreign institutional selling (FII {fii_change:.1f}%), may pressure stock near-term.")
        
        # DII activity
        if dii_direction == "increasing" and dii_change > 2:
            insights.append(f"Domestic institutional buying (DII +{dii_change:.1f}%), local confidence building.")
        elif dii_direction == "decreasing" and dii_change < -2:
            insights.append(f"Domestic institutional selling (DII {dii_change:.1f}%), watch for support levels.")
        
        # Promoter activity
        if promoter_change > 1:
            insights.append(f"Promoter stake increased (+{promoter_change:.1f}%), positive signal from management.")
        elif promoter_change < -1:
            insights.append(f"Promoter stake decreased ({promoter_change:.1f}%), investigate reasons.")
        
        if not insights:
            return "Stable institutional holding, no major changes in shareholding pattern."
        
        return " ".join(insights)
    
    def assess_risk(
        self,
        stock_data: Dict[str, Any],
        valuation_insight: ValuationInsight,
        trend_insight: TrendInsight
    ) -> Dict[str, Any]:
        """
        Generate comprehensive risk assessment.
        
        Returns:
            Dict with risk_score (1-10), risk_factors, and summary
        """
        risk_score = 5  # Start neutral
        risk_factors = []
        
        # Valuation risk
        if valuation_insight.risk_level == "very_high":
            risk_score += 3
            risk_factors.append("Extremely high valuation")
        elif valuation_insight.risk_level == "high":
            risk_score += 2
            risk_factors.append("Premium valuation")
        elif valuation_insight.risk_level == "low":
            risk_score -= 1
        
        # Trend risk
        if trend_insight.direction == "declining":
            risk_score += 2
            risk_factors.append("Declining revenue/profit trend")
        elif trend_insight.direction == "decelerating":
            risk_score += 1
            risk_factors.append("Growth momentum slowing")
        elif trend_insight.direction == "accelerating":
            risk_score -= 1
        
        # Debt risk
        debt_to_equity = stock_data.get("debt_to_equity", 0)
        if debt_to_equity > 2:
            risk_score += 2
            risk_factors.append(f"High debt (D/E: {debt_to_equity:.1f})")
        
        # Cap risk score
        risk_score = max(1, min(10, risk_score))
        
        # Generate summary
        if risk_score >= 8:
            summary = "High risk - Significant concerns with valuation, growth, or leverage"
        elif risk_score >= 6:
            summary = "Moderate-high risk - Some concerns to monitor"
        elif risk_score >= 4:
            summary = "Moderate risk - Balanced risk-reward profile"
        else:
            summary = "Low-moderate risk - Relatively stable fundamentals"
        
        return {
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "summary": summary
        }


# Singleton instance
_reasoning_engine: Optional[ReasoningEngine] = None


def get_reasoning_engine() -> ReasoningEngine:
    """Get singleton reasoning engine instance."""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = ReasoningEngine()
    return _reasoning_engine
