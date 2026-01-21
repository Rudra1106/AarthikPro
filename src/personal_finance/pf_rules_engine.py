"""
Personal Finance Rules Engine

Deterministic financial logic - the "Finance Brain".
LLM explains, rules decide. No hallucinations, no guesses.

Core Rules:
1. Cash Flow Health (savings rate)
2. Emergency Fund adequacy
3. Investment Readiness
4. Asset Allocation guardrails
"""
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class HealthStatus(str, Enum):
    """Financial health status levels."""
    CRITICAL = "critical"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    EXCELLENT = "excellent"


class RiskTolerance(str, Enum):
    """Risk tolerance levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RulesEngineOutput:
    """Output from rules engine for LLM to explain."""
    # Calculated metrics
    savings_rate: Optional[float]  # 0.0 to 1.0
    savings_rate_status: Optional[HealthStatus]
    emergency_fund_months: Optional[float]
    emergency_fund_status: Optional[HealthStatus]
    investment_ready: bool
    
    # Recommendations (rule-based, not LLM)
    max_equity_allocation: Optional[float]  # 0.0 to 1.0
    suggested_monthly_investment: Optional[float]
    
    # Warnings/gates
    warnings: list[str]
    blockers: list[str]  # Hard gates (e.g., no emergency fund)
    
    # Assumptions made (for transparency)
    assumptions: list[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for LLM prompt injection."""
        return {
            "savings_rate": f"{self.savings_rate * 100:.1f}%" if self.savings_rate else "Unknown",
            "savings_rate_status": self.savings_rate_status.value if self.savings_rate_status else "Unknown",
            "emergency_fund_months": f"{self.emergency_fund_months:.1f}" if self.emergency_fund_months else "Unknown",
            "emergency_fund_status": self.emergency_fund_status.value if self.emergency_fund_status else "Unknown",
            "investment_ready": self.investment_ready,
            "max_equity_allocation": f"{self.max_equity_allocation * 100:.0f}%" if self.max_equity_allocation else "Not calculated",
            "suggested_monthly_investment": f"₹{self.suggested_monthly_investment:,.0f}" if self.suggested_monthly_investment else "Not calculated",
            "warnings": self.warnings,
            "blockers": self.blockers,
            "assumptions": self.assumptions
        }


class PFRulesEngine:
    """
    Deterministic financial rules engine.
    
    Design principle: Math decides, LLM explains.
    """
    
    # Constants
    REQUIRED_EMERGENCY_MONTHS_SALARIED = 6
    REQUIRED_EMERGENCY_MONTHS_VARIABLE = 12
    MIN_SAVINGS_RATE = 0.10  # 10%
    CRITICAL_EF_THRESHOLD = 3  # months
    
    def calculate_savings_rate(
        self, 
        monthly_income: Optional[float], 
        monthly_expenses: Optional[float]
    ) -> tuple[Optional[float], Optional[HealthStatus]]:
        """
        Calculate savings rate and classify health.
        
        Formula: (income - expenses) / income
        
        Returns:
            (savings_rate, status)
        """
        if monthly_income is None or monthly_expenses is None:
            return None, None
        
        if monthly_income <= 0:
            return None, None
        
        # Handle edge case: expenses > income
        if monthly_expenses >= monthly_income:
            return 0.0, HealthStatus.CRITICAL
        
        savings_rate = (monthly_income - monthly_expenses) / monthly_income
        
        # Classify
        if savings_rate < 0.10:
            status = HealthStatus.WEAK
        elif savings_rate < 0.20:
            status = HealthStatus.MODERATE
        elif savings_rate < 0.30:
            status = HealthStatus.STRONG
        else:
            status = HealthStatus.EXCELLENT
        
        return savings_rate, status
    
    def calculate_emergency_fund_months(
        self,
        emergency_fund_amount: Optional[float],
        monthly_expenses: Optional[float]
    ) -> tuple[Optional[float], Optional[HealthStatus]]:
        """
        Calculate emergency fund coverage in months.
        
        Formula: emergency_fund / monthly_expenses
        
        Returns:
            (months, status)
        """
        if emergency_fund_amount is None or monthly_expenses is None:
            return None, None
        
        if monthly_expenses <= 0:
            return None, None
        
        months = emergency_fund_amount / monthly_expenses
        
        # Classify
        if months < 3:
            status = HealthStatus.CRITICAL
        elif months < 6:
            status = HealthStatus.WEAK
        elif months < 9:
            status = HealthStatus.MODERATE
        elif months < 12:
            status = HealthStatus.STRONG
        else:
            status = HealthStatus.EXCELLENT
        
        return months, status
    
    def check_investment_readiness(
        self,
        savings_rate: Optional[float],
        emergency_fund_months: Optional[float],
        income_type: str = "salaried"
    ) -> bool:
        """
        Determine if user is ready for aggressive investing.
        
        Criteria:
        - Savings rate >= 10%
        - Emergency fund >= required months (6 for salaried, 12 for variable)
        
        Returns:
            True if investment ready, False otherwise
        """
        # Determine required EF months
        required_ef = (
            self.REQUIRED_EMERGENCY_MONTHS_VARIABLE 
            if income_type == "variable" 
            else self.REQUIRED_EMERGENCY_MONTHS_SALARIED
        )
        
        # Check criteria
        has_good_savings = savings_rate is not None and savings_rate >= self.MIN_SAVINGS_RATE
        has_adequate_ef = emergency_fund_months is not None and emergency_fund_months >= required_ef
        
        return has_good_savings and has_adequate_ef
    
    def calculate_max_equity_allocation(
        self,
        age: Optional[int],
        risk_tolerance: RiskTolerance = RiskTolerance.MEDIUM
    ) -> Optional[float]:
        """
        Calculate maximum equity allocation.
        
        Formula: min(100 - age, risk_cap)
        
        Risk caps:
        - Low: 40%
        - Medium: 60%
        - High: 80%
        
        Returns:
            Max equity allocation (0.0 to 1.0)
        """
        if age is None:
            return None
        
        # Risk caps
        risk_caps = {
            RiskTolerance.LOW: 0.40,
            RiskTolerance.MEDIUM: 0.60,
            RiskTolerance.HIGH: 0.80
        }
        
        risk_cap = risk_caps.get(risk_tolerance, 0.60)
        
        # Age-based allocation
        age_based = max(0, (100 - age) / 100)
        
        return min(age_based, risk_cap)
    
    def suggest_monthly_investment(
        self,
        monthly_income: Optional[float],
        monthly_expenses: Optional[float],
        emergency_fund_months: Optional[float],
        income_type: str = "salaried"
    ) -> Optional[float]:
        """
        Suggest monthly investment amount.
        
        Logic:
        - If EF inadequate: suggest building EF first (50% of surplus)
        - If EF adequate: suggest 70-80% of surplus for investment
        
        Returns:
            Suggested monthly investment amount
        """
        if monthly_income is None or monthly_expenses is None:
            return None
        
        surplus = monthly_income - monthly_expenses
        
        if surplus <= 0:
            return 0.0
        
        # Determine required EF months
        required_ef = (
            self.REQUIRED_EMERGENCY_MONTHS_VARIABLE 
            if income_type == "variable" 
            else self.REQUIRED_EMERGENCY_MONTHS_SALARIED
        )
        
        # If EF inadequate, prioritize EF building
        if emergency_fund_months is None or emergency_fund_months < required_ef:
            # Suggest 30-40% of surplus for investment, rest for EF
            return surplus * 0.35
        
        # If EF adequate, suggest 70-80% of surplus for investment
        return surplus * 0.75
    
    def run(self, user_profile: Dict[str, Any]) -> RulesEngineOutput:
        """
        Run rules engine on user profile.
        
        Args:
            user_profile: Dict with keys:
                - monthly_income (float)
                - monthly_expenses (float)
                - emergency_fund_amount (float)
                - age (int)
                - income_type (str): "salaried" or "variable"
                - risk_tolerance (str): "low", "medium", "high"
        
        Returns:
            RulesEngineOutput with calculations and recommendations
        """
        # Extract profile data
        monthly_income = user_profile.get("monthly_income")
        monthly_expenses = user_profile.get("monthly_expenses")
        emergency_fund_amount = user_profile.get("emergency_fund_amount")
        age = user_profile.get("age")
        income_type = user_profile.get("income_type", "salaried")
        risk_tolerance_str = user_profile.get("risk_tolerance", "medium")
        
        # Parse risk tolerance
        try:
            risk_tolerance = RiskTolerance(risk_tolerance_str.lower())
        except ValueError:
            risk_tolerance = RiskTolerance.MEDIUM
        
        # Calculate metrics
        savings_rate, savings_rate_status = self.calculate_savings_rate(
            monthly_income, monthly_expenses
        )
        
        ef_months, ef_status = self.calculate_emergency_fund_months(
            emergency_fund_amount, monthly_expenses
        )
        
        investment_ready = self.check_investment_readiness(
            savings_rate, ef_months, income_type
        )
        
        max_equity = self.calculate_max_equity_allocation(age, risk_tolerance)
        
        suggested_investment = self.suggest_monthly_investment(
            monthly_income, monthly_expenses, ef_months, income_type
        )
        
        # Generate warnings and blockers
        warnings = []
        blockers = []
        assumptions = []
        
        # Savings rate warnings
        if savings_rate is not None and savings_rate < 0.10:
            warnings.append("Your savings rate is below 10%. Focus on reducing expenses or increasing income before aggressive investing.")
        
        # Emergency fund warnings/blockers
        if ef_months is not None:
            if ef_months < 3:
                blockers.append("Emergency fund covers less than 3 months. Build this to at least 6 months before investing aggressively.")
            elif ef_months < 6:
                warnings.append("Emergency fund is below recommended 6 months. Consider building this alongside investments.")
        
        # Missing data assumptions
        if monthly_income is None:
            assumptions.append("Income not provided - calculations are generic.")
        if monthly_expenses is None:
            assumptions.append("Expenses not provided - calculations are generic.")
        if emergency_fund_amount is None:
            assumptions.append("Emergency fund not provided - assuming it needs to be built.")
        if age is None:
            assumptions.append("Age not provided - asset allocation not calculated.")
        
        return RulesEngineOutput(
            savings_rate=savings_rate,
            savings_rate_status=savings_rate_status,
            emergency_fund_months=ef_months,
            emergency_fund_status=ef_status,
            investment_ready=investment_ready,
            max_equity_allocation=max_equity,
            suggested_monthly_investment=suggested_investment,
            warnings=warnings,
            blockers=blockers,
            assumptions=assumptions
        )


# Singleton instance
_rules_engine_instance: Optional[PFRulesEngine] = None


def get_pf_rules_engine() -> PFRulesEngine:
    """Get singleton PF rules engine instance."""
    global _rules_engine_instance
    if _rules_engine_instance is None:
        _rules_engine_instance = PFRulesEngine()
    return _rules_engine_instance
