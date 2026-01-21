"""
Goal Planning Calculator Module

Deterministic math engine for financial goal planning.

CORE PRINCIPLE: Convert human goals → clear math → safe recommendation

Rules:
- Math is deterministic, not probabilistic
- LLM explains trade-offs, calculator provides numbers
- Always label return assumptions as illustrative
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
import math

from .pf_assumptions import (
    ASSUMPTIONS,
    get_time_horizon_bucket,
    get_suitable_buckets,
    get_return_assumption,
    TimeHorizon,
    InvestmentBucket
)


@dataclass
class GoalInput:
    """Input for goal planning."""
    goal_name: str
    target_amount: Optional[float] = None
    time_horizon_months: int = 12
    monthly_saving: Optional[float] = None
    risk_tolerance: str = "low"  # low, medium, high
    current_savings: float = 0.0


@dataclass
class GoalOutput:
    """Output from goal planning calculator."""
    # Input summary
    goal_name: str
    target_amount: float
    time_horizon_months: int
    time_horizon_label: str
    
    # Calculations
    required_monthly: float
    current_monthly: float
    gap: float
    feasible: bool
    
    # Recommendations
    recommended_bucket: str
    recommended_bucket_label: str
    assumed_return_rate: float
    assumed_return_label: str
    
    # Explanation
    reason: str
    alternative_scenarios: list[Dict[str, Any]]
    warnings: list[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "goal_name": self.goal_name,
            "target_amount": self.target_amount,
            "time_horizon_months": self.time_horizon_months,
            "time_horizon_label": self.time_horizon_label,
            "required_monthly": self.required_monthly,
            "current_monthly": self.current_monthly,
            "gap": self.gap,
            "feasible": self.feasible,
            "recommended_bucket": self.recommended_bucket,
            "recommended_bucket_label": self.recommended_bucket_label,
            "assumed_return_rate": self.assumed_return_rate,
            "assumed_return_label": self.assumed_return_label,
            "reason": self.reason,
            "alternative_scenarios": self.alternative_scenarios,
            "warnings": self.warnings
        }


class GoalPlanningCalculator:
    """
    Deterministic goal planning calculator.
    
    Converts goals into clear math with safe recommendations.
    """
    
    def calculate_sip_corpus(
        self,
        monthly_amount: float,
        months: int,
        annual_return_rate: float
    ) -> float:
        """
        Calculate SIP corpus using future value formula.
        
        FV = P × [(1 + r)^n - 1] / r × (1 + r)
        
        Where:
        - P = monthly investment
        - r = monthly return rate
        - n = number of months
        """
        if monthly_amount <= 0 or months <= 0:
            return 0.0
        
        monthly_rate = annual_return_rate / 12 / 100
        
        if monthly_rate == 0:
            # No returns, just sum
            return monthly_amount * months
        
        fv = monthly_amount * (
            ((1 + monthly_rate) ** months - 1) / monthly_rate
        ) * (1 + monthly_rate)
        
        return fv
    
    def calculate_required_monthly_sip(
        self,
        target_amount: float,
        months: int,
        annual_return_rate: float
    ) -> float:
        """
        Calculate required monthly SIP to reach target.
        
        Inverse of SIP corpus formula.
        """
        if target_amount <= 0 or months <= 0:
            return 0.0
        
        monthly_rate = annual_return_rate / 12 / 100
        
        if monthly_rate == 0:
            # No returns, simple division
            return target_amount / months
        
        required_monthly = target_amount / (
            ((1 + monthly_rate) ** months - 1) / monthly_rate * (1 + monthly_rate)
        )
        
        return required_monthly
    
    def calculate_lumpsum_corpus(
        self,
        principal: float,
        months: int,
        annual_return_rate: float
    ) -> float:
        """
        Calculate lumpsum corpus.
        
        FV = P × (1 + r)^n
        """
        if principal <= 0 or months <= 0:
            return principal
        
        monthly_rate = annual_return_rate / 12 / 100
        fv = principal * ((1 + monthly_rate) ** months)
        
        return fv
    
    def plan_goal(self, goal_input: GoalInput) -> GoalOutput:
        """
        Plan a financial goal with deterministic math.
        
        Args:
            goal_input: Goal input parameters
            
        Returns:
            GoalOutput with calculations and recommendations
        """
        # Determine time horizon bucket
        time_horizon_bucket = get_time_horizon_bucket(goal_input.time_horizon_months)
        time_horizon_info = ASSUMPTIONS["time_horizons"][time_horizon_bucket]
        
        # Get suitable investment buckets
        suitable_buckets = get_suitable_buckets(time_horizon_bucket)
        
        # Select recommended bucket based on risk tolerance and time horizon
        if goal_input.risk_tolerance == "low" or time_horizon_bucket == TimeHorizon.SHORT_TERM:
            recommended_bucket = suitable_buckets[0]  # Most conservative
        elif goal_input.risk_tolerance == "high" and time_horizon_bucket == TimeHorizon.LONG_TERM:
            recommended_bucket = suitable_buckets[-1]  # Most aggressive
        else:
            # Medium risk or medium term - pick middle option
            recommended_bucket = suitable_buckets[len(suitable_buckets) // 2]
        
        # Get return assumption for recommended bucket
        return_info = get_return_assumption(recommended_bucket)
        assumed_return_rate = return_info["typical"]
        
        # Calculate required monthly investment
        required_monthly = self.calculate_required_monthly_sip(
            goal_input.target_amount,
            goal_input.time_horizon_months,
            assumed_return_rate
        )
        
        # Check feasibility
        current_monthly = goal_input.monthly_saving or 0.0
        gap = required_monthly - current_monthly
        feasible = gap <= 0
        
        # Generate reason
        if time_horizon_bucket == TimeHorizon.SHORT_TERM:
            reason = "Short-term goal; capital protection matters more than returns"
        elif time_horizon_bucket == TimeHorizon.MEDIUM_TERM:
            reason = "Medium-term goal; balanced approach with moderate risk"
        else:
            reason = "Long-term goal; can tolerate short-term volatility for higher returns"
        
        # Generate alternative scenarios
        alternative_scenarios = []
        
        # Scenario 1: Increase monthly saving
        if not feasible:
            alternative_scenarios.append({
                "type": "increase_monthly",
                "description": f"Increase monthly saving to ₹{required_monthly:,.0f}",
                "monthly_amount": required_monthly,
                "achieves_goal": True
            })
        
        # Scenario 2: Extend timeline
        if not feasible:
            extended_months = goal_input.time_horizon_months + 12  # Add 1 year
            required_with_extension = self.calculate_required_monthly_sip(
                goal_input.target_amount,
                extended_months,
                assumed_return_rate
            )
            alternative_scenarios.append({
                "type": "extend_timeline",
                "description": f"Extend timeline to {extended_months} months",
                "monthly_amount": required_with_extension,
                "new_timeline_months": extended_months,
                "achieves_goal": required_with_extension <= current_monthly
            })
        
        # Scenario 3: Use existing savings
        if goal_input.current_savings > 0:
            # Calculate how much more is needed
            lumpsum_growth = self.calculate_lumpsum_corpus(
                goal_input.current_savings,
                goal_input.time_horizon_months,
                assumed_return_rate
            )
            remaining_needed = max(0, goal_input.target_amount - lumpsum_growth)
            required_monthly_with_lumpsum = self.calculate_required_monthly_sip(
                remaining_needed,
                goal_input.time_horizon_months,
                assumed_return_rate
            )
            
            alternative_scenarios.append({
                "type": "use_existing_savings",
                "description": f"Use existing ₹{goal_input.current_savings:,.0f} + monthly SIP",
                "monthly_amount": required_monthly_with_lumpsum,
                "lumpsum_contribution": lumpsum_growth,
                "achieves_goal": required_monthly_with_lumpsum <= current_monthly
            })
        
        # Generate warnings
        warnings = []
        
        if time_horizon_bucket == TimeHorizon.SHORT_TERM and recommended_bucket == InvestmentBucket.EQUITY:
            warnings.append("Equity investments not recommended for short-term goals due to volatility")
        
        if not feasible and gap > current_monthly:
            warnings.append(f"Goal requires more than double your current monthly saving (gap: ₹{gap:,.0f})")
        
        if goal_input.target_amount > ASSUMPTIONS["goal_planning"]["max_goal_amount"]:
            warnings.append("Very large goal - consider breaking into smaller milestones")
        
        return GoalOutput(
            goal_name=goal_input.goal_name,
            target_amount=goal_input.target_amount,
            time_horizon_months=goal_input.time_horizon_months,
            time_horizon_label=time_horizon_info["description"],
            required_monthly=required_monthly,
            current_monthly=current_monthly,
            gap=gap,
            feasible=feasible,
            recommended_bucket=recommended_bucket.value,
            recommended_bucket_label=return_info["description"],
            assumed_return_rate=assumed_return_rate,
            assumed_return_label=return_info["label"],
            reason=reason,
            alternative_scenarios=alternative_scenarios,
            warnings=warnings
        )


# Singleton instance
_calculator_instance: Optional[GoalPlanningCalculator] = None


def get_goal_calculator() -> GoalPlanningCalculator:
    """Get singleton goal planning calculator instance."""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = GoalPlanningCalculator()
    return _calculator_instance
