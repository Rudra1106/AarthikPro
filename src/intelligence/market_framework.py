"""
Market Thinking Framework - Institutional analyst mental model.

Every analysis must address:
1. What changed? (delta)
2. Why did it change? (drivers)
3. Is it confirmed? (breadth, volume, indicators)
4. What happens next? (scenarios)
5. Who should care? (trader vs investor)
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from src.analytics.deterministic_engine import get_analytics_engine, ComparisonResult

logger = logging.getLogger(__name__)


class UserType(str, Enum):
    """User type classification."""
    TRADER = "trader"          # Intraday/swing trader
    INVESTOR = "investor"      # Long-term investor
    ANALYST = "analyst"        # Detailed research


class TimeHorizon(str, Enum):
    """Time horizon classification."""
    INTRADAY = "intraday"      # Today's action
    SWING = "swing"            # 1-5 days
    SHORT_TERM = "short_term"  # 1-4 weeks
    LONG_TERM = "long_term"    # 3+ months


@dataclass
class DeltaAnalysis:
    """What changed analysis."""
    current_value: float
    previous_value: float
    delta: float
    percent_change: float
    direction: str
    magnitude: str
    context: str  # Human-readable context
    
    def to_dict(self) -> dict:
        return {
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "delta": self.delta,
            "percent_change": round(self.percent_change, 2),
            "direction": self.direction,
            "magnitude": self.magnitude,
            "context": self.context
        }


@dataclass
class DriverAnalysis:
    """Why it changed analysis."""
    primary_driver: str
    secondary_drivers: List[str]
    evidence: Dict[str, Any]
    confidence: float  # 0-1
    
    def to_dict(self) -> dict:
        return {
            "primary_driver": self.primary_driver,
            "secondary_drivers": self.secondary_drivers,
            "evidence": self.evidence,
            "confidence": self.confidence
        }


@dataclass
class ConfirmationAnalysis:
    """Is it confirmed analysis."""
    breadth: float  # % of stocks participating
    volume_status: str  # above_average, below_average, normal
    technical_confirmation: Dict[str, Any]  # RSI, MACD, etc.
    is_confirmed: bool
    confidence_level: str  # high, medium, low
    
    def to_dict(self) -> dict:
        return {
            "breadth": round(self.breadth, 2),
            "volume_status": self.volume_status,
            "technical_confirmation": self.technical_confirmation,
            "is_confirmed": self.is_confirmed,
            "confidence_level": self.confidence_level
        }


@dataclass
class ScenarioAnalysis:
    """What happens next analysis."""
    bullish_scenario: str
    bullish_probability: float
    bearish_scenario: str
    bearish_probability: float
    base_case: str
    base_case_probability: float
    key_levels: Dict[str, float]  # support, resistance
    
    def to_dict(self) -> dict:
        return {
            "bullish_scenario": self.bullish_scenario,
            "bullish_probability": self.bullish_probability,
            "bearish_scenario": self.bearish_scenario,
            "bearish_probability": self.bearish_probability,
            "base_case": self.base_case,
            "base_case_probability": self.base_case_probability,
            "key_levels": self.key_levels
        }


@dataclass
class AudienceView:
    """Who should care analysis."""
    trader_view: str  # 1-5 days action items
    investor_view: str  # 3-6 months action items
    risk_level: str  # low, medium, high
    
    def to_dict(self) -> dict:
        return {
            "trader_view": self.trader_view,
            "investor_view": self.investor_view,
            "risk_level": self.risk_level
        }


@dataclass
class AnalysisResult:
    """Complete market thinking framework analysis."""
    delta: DeltaAnalysis
    drivers: DriverAnalysis
    confirmation: ConfirmationAnalysis
    scenarios: ScenarioAnalysis
    audience_view: AudienceView
    
    def to_dict(self) -> dict:
        return {
            "delta": self.delta.to_dict(),
            "drivers": self.drivers.to_dict(),
            "confirmation": self.confirmation.to_dict(),
            "scenarios": self.scenarios.to_dict(),
            "audience_view": self.audience_view.to_dict()
        }


class MarketThinkingFramework:
    """
    Institutional analyst mental model for market analysis.
    
    Provides structured analysis framework that ensures consistency
    across all responses.
    """
    
    def __init__(self):
        self.analytics = get_analytics_engine()
        self.logger = logging.getLogger(__name__)
    
    def analyze(
        self,
        data: Dict[str, Any],
        query_context: Dict[str, Any]
    ) -> AnalysisResult:
        """
        Perform complete market thinking framework analysis.
        
        Args:
            data: Market data including current/previous values, technicals, etc.
            query_context: Context including user_type, time_horizon, etc.
            
        Returns:
            AnalysisResult with all 5 framework components
        """
        # 1. What changed?
        delta = self._analyze_delta(data)
        
        # 2. Why did it change?
        drivers = self._identify_drivers(data, delta)
        
        # 3. Is it confirmed?
        confirmation = self._check_confirmation(data)
        
        # 4. What happens next?
        scenarios = self._build_scenarios(data, delta, confirmation)
        
        # 5. Who should care?
        audience_view = self._tailor_to_audience(
            query_context.get("user_type", UserType.INVESTOR),
            query_context.get("time_horizon", TimeHorizon.SHORT_TERM),
            delta,
            scenarios
        )
        
        return AnalysisResult(
            delta=delta,
            drivers=drivers,
            confirmation=confirmation,
            scenarios=scenarios,
            audience_view=audience_view
        )
    
    def _analyze_delta(self, data: Dict[str, Any]) -> DeltaAnalysis:
        """Analyze what changed."""
        current = data.get("current_value", 0)
        previous = data.get("previous_value", current)
        
        comparison = self.analytics.compare_metrics(current, previous)
        
        # Create human-readable context
        symbol = data.get("symbol", "Asset")
        if comparison.direction == "up":
            context = f"{symbol} gained {abs(comparison.percent_change):.2f}%"
        elif comparison.direction == "down":
            context = f"{symbol} declined {abs(comparison.percent_change):.2f}%"
        else:
            context = f"{symbol} remained flat"
        
        return DeltaAnalysis(
            current_value=current,
            previous_value=previous,
            delta=comparison.delta,
            percent_change=comparison.percent_change,
            direction=comparison.direction,
            magnitude=comparison.magnitude.value,
            context=context
        )
    
    def _identify_drivers(
        self,
        data: Dict[str, Any],
        delta: DeltaAnalysis
    ) -> DriverAnalysis:
        """Identify why it changed."""
        # Extract potential drivers from data
        drivers = []
        evidence = {}
        
        # Check for sector performance
        if "sector_performance" in data:
            sector_data = data["sector_performance"]
            if sector_data.get("change_percent", 0) != 0:
                drivers.append(f"Sector momentum ({sector_data.get('name', 'sector')})")
                evidence["sector"] = sector_data
        
        # Check for market-wide movement
        if "market_change" in data:
            market_change = data["market_change"]
            if abs(market_change) > 1.0:
                drivers.append(f"Broad market movement ({market_change:+.2f}%)")
                evidence["market"] = market_change
        
        # Check for volume
        if "volume" in data:
            avg_volume = data.get("avg_volume", data["volume"])
            if data["volume"] > avg_volume * 1.5:
                drivers.append("Above-average volume")
                evidence["volume"] = {"current": data["volume"], "average": avg_volume}
        
        # Check for news/events
        if "news_events" in data and data["news_events"]:
            drivers.append("Recent news/events")
            evidence["news"] = data["news_events"]
        
        # Determine primary driver
        if drivers:
            primary_driver = drivers[0]
            secondary_drivers = drivers[1:]
            confidence = 0.8 if len(drivers) >= 2 else 0.6
        else:
            primary_driver = "Market dynamics"
            secondary_drivers = []
            confidence = 0.4
        
        return DriverAnalysis(
            primary_driver=primary_driver,
            secondary_drivers=secondary_drivers,
            evidence=evidence,
            confidence=confidence
        )
    
    def _check_confirmation(self, data: Dict[str, Any]) -> ConfirmationAnalysis:
        """Check if move is confirmed."""
        # Calculate breadth
        breadth = 50.0  # Default neutral
        if "breadth_data" in data:
            breadth_info = self.analytics.calculate_breadth(data["breadth_data"])
            breadth = breadth_info.get("advancing_pct", 50.0)
        
        # Check volume
        volume_status = "normal"
        if "volume" in data and "avg_volume" in data:
            vol_ratio = data["volume"] / data["avg_volume"]
            if vol_ratio > 1.5:
                volume_status = "above_average"
            elif vol_ratio < 0.7:
                volume_status = "below_average"
        
        # Technical confirmation
        technical_confirmation = {}
        
        if "rsi" in data:
            technical_confirmation["rsi"] = data["rsi"]
        
        if "macd" in data:
            technical_confirmation["macd"] = data["macd"]
        
        # Determine if confirmed
        confirmation_score = 0
        if breadth > 60:
            confirmation_score += 1
        if volume_status == "above_average":
            confirmation_score += 1
        if technical_confirmation:
            confirmation_score += 1
        
        is_confirmed = confirmation_score >= 2
        
        if confirmation_score >= 2:
            confidence_level = "high"
        elif confirmation_score == 1:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        return ConfirmationAnalysis(
            breadth=breadth,
            volume_status=volume_status,
            technical_confirmation=technical_confirmation,
            is_confirmed=is_confirmed,
            confidence_level=confidence_level
        )
    
    def _build_scenarios(
        self,
        data: Dict[str, Any],
        delta: DeltaAnalysis,
        confirmation: ConfirmationAnalysis
    ) -> ScenarioAnalysis:
        """Build scenario analysis."""
        current_price = data.get("current_value", 0)
        
        # Get support/resistance levels
        key_levels = data.get("key_levels", {})
        if not key_levels and "prices" in data:
            key_levels = self.analytics.identify_support_resistance(data["prices"])
        
        support = key_levels.get("support", [current_price * 0.95])[0] if key_levels.get("support") else current_price * 0.95
        resistance = key_levels.get("resistance", [current_price * 1.05])[0] if key_levels.get("resistance") else current_price * 1.05
        
        # Build scenarios based on current trend and confirmation
        if delta.direction == "up" and confirmation.is_confirmed:
            bullish_scenario = f"Break above ₹{resistance:,.2f} could target ₹{resistance * 1.05:,.2f}"
            bullish_probability = 0.6
            bearish_scenario = f"Failure to hold ₹{support:,.2f} could lead to ₹{support * 0.95:,.2f}"
            bearish_probability = 0.2
            base_case = f"Consolidation between ₹{support:,.2f} and ₹{resistance:,.2f}"
            base_case_probability = 0.2
        elif delta.direction == "down" and confirmation.is_confirmed:
            bullish_scenario = f"Recovery above ₹{resistance:,.2f} could signal reversal"
            bullish_probability = 0.2
            bearish_scenario = f"Break below ₹{support:,.2f} could extend to ₹{support * 0.95:,.2f}"
            bearish_probability = 0.6
            base_case = f"Range-bound between ₹{support:,.2f} and ₹{resistance:,.2f}"
            base_case_probability = 0.2
        else:
            bullish_scenario = f"Move above ₹{resistance:,.2f} with volume"
            bullish_probability = 0.3
            bearish_scenario = f"Break below ₹{support:,.2f} with volume"
            bearish_probability = 0.3
            base_case = f"Sideways movement between ₹{support:,.2f} and ₹{resistance:,.2f}"
            base_case_probability = 0.4
        
        return ScenarioAnalysis(
            bullish_scenario=bullish_scenario,
            bullish_probability=bullish_probability,
            bearish_scenario=bearish_scenario,
            bearish_probability=bearish_probability,
            base_case=base_case,
            base_case_probability=base_case_probability,
            key_levels={"support": support, "resistance": resistance}
        )
    
    def _tailor_to_audience(
        self,
        user_type: UserType,
        time_horizon: TimeHorizon,
        delta: DeltaAnalysis,
        scenarios: ScenarioAnalysis
    ) -> AudienceView:
        """Tailor analysis to audience."""
        # Determine risk level
        if delta.magnitude == "significant":
            risk_level = "high"
        elif delta.magnitude == "moderate":
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Trader view (1-5 days)
        if delta.direction == "up":
            trader_view = f"Watch for break above ₹{scenarios.key_levels['resistance']:,.2f}. "
            trader_view += f"Stop loss below ₹{scenarios.key_levels['support']:,.2f}."
        elif delta.direction == "down":
            trader_view = f"Avoid long positions. Watch for support at ₹{scenarios.key_levels['support']:,.2f}. "
            trader_view += f"Short-term resistance at ₹{scenarios.key_levels['resistance']:,.2f}."
        else:
            trader_view = f"Range-bound. Buy near ₹{scenarios.key_levels['support']:,.2f}, "
            trader_view += f"sell near ₹{scenarios.key_levels['resistance']:,.2f}."
        
        # Investor view (3-6 months)
        if delta.direction == "up" and delta.magnitude in ["significant", "moderate"]:
            investor_view = "Positive momentum. Consider accumulating on dips for long-term portfolio."
        elif delta.direction == "down" and delta.magnitude == "significant":
            investor_view = "Weakness observed. Wait for stabilization before fresh positions."
        else:
            investor_view = "Consolidation phase. Existing holders can maintain positions with long-term view."
        
        return AudienceView(
            trader_view=trader_view,
            investor_view=investor_view,
            risk_level=risk_level
        )


# Singleton instance
_market_framework: Optional[MarketThinkingFramework] = None


def get_market_framework() -> MarketThinkingFramework:
    """Get singleton market framework instance."""
    global _market_framework
    if _market_framework is None:
        _market_framework = MarketThinkingFramework()
    return _market_framework
