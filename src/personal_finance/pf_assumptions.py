"""
Personal Finance Assumptions Library

Static, non-hallucinatory assumptions for consistent guidance.

CRITICAL RULES:
- Never fetch these from the web
- Never let LLM invent them
- Always label as illustrative
- Update only after careful review
"""
from typing import Dict, Any
from enum import Enum


class IncomeType(str, Enum):
    """Income stability types."""
    SALARIED = "salaried"
    VARIABLE = "variable_income"
    BUSINESS = "business"


class TimeHorizon(str, Enum):
    """Investment time horizons."""
    SHORT_TERM = "short_term"  # <= 12 months
    MEDIUM_TERM = "medium_term"  # 1-5 years
    LONG_TERM = "long_term"  # 5+ years


class InvestmentBucket(str, Enum):
    """Investment instrument categories."""
    SAVINGS = "savings"  # Savings account, FD
    LIQUID = "liquid"  # Liquid funds, RD
    DEBT = "debt"  # Debt mutual funds
    HYBRID = "hybrid"  # Balanced funds
    EQUITY = "equity"  # Equity mutual funds, stocks


# Core Assumptions (STATIC - DO NOT MODIFY WITHOUT REVIEW)
ASSUMPTIONS = {
    # Emergency Fund Requirements
    "emergency_fund_months": {
        IncomeType.SALARIED: 6,
        IncomeType.VARIABLE: 9,
        IncomeType.BUSINESS: 12
    },
    
    # Investment Time Horizons
    "time_horizons": {
        TimeHorizon.SHORT_TERM: {
            "months": (0, 12),
            "description": "Less than 1 year",
            "suitable_buckets": [InvestmentBucket.SAVINGS, InvestmentBucket.LIQUID]
        },
        TimeHorizon.MEDIUM_TERM: {
            "months": (12, 60),
            "description": "1 to 5 years",
            "suitable_buckets": [InvestmentBucket.LIQUID, InvestmentBucket.DEBT, InvestmentBucket.HYBRID]
        },
        TimeHorizon.LONG_TERM: {
            "months": (60, float('inf')),
            "description": "5+ years",
            "suitable_buckets": [InvestmentBucket.HYBRID, InvestmentBucket.EQUITY]
        }
    },
    
    # Return Assumptions (ILLUSTRATIVE - NOT GUARANTEES)
    "return_assumptions": {
        InvestmentBucket.SAVINGS: {
            "min": 3.0,
            "max": 4.0,
            "typical": 3.5,
            "label": "3-4% (illustrative)",
            "description": "Savings accounts, FDs"
        },
        InvestmentBucket.LIQUID: {
            "min": 4.0,
            "max": 6.0,
            "typical": 5.0,
            "label": "4-6% (illustrative)",
            "description": "Liquid funds, RDs"
        },
        InvestmentBucket.DEBT: {
            "min": 5.0,
            "max": 7.0,
            "typical": 6.0,
            "label": "5-7% (illustrative)",
            "description": "Debt mutual funds"
        },
        InvestmentBucket.HYBRID: {
            "min": 7.0,
            "max": 10.0,
            "typical": 8.5,
            "label": "7-10% (illustrative)",
            "description": "Balanced/hybrid funds"
        },
        InvestmentBucket.EQUITY: {
            "min": 10.0,
            "max": 12.0,
            "typical": 11.0,
            "label": "10-12% (illustrative)",
            "description": "Equity mutual funds (long-term)"
        }
    },
    
    # Volatility & Risk Rules
    "volatility_rules": {
        "short_term_equity": {
            "recommended": False,
            "reason": "High volatility risk for short horizons"
        },
        "sip_benefit": {
            "reduces": "Timing risk (rupee cost averaging)",
            "does_not_reduce": "Market risk or loss risk"
        },
        "emergency_fund_volatility": {
            "max_allowed": InvestmentBucket.LIQUID,
            "reason": "Must be accessible without loss"
        }
    },
    
    # Savings Rate Health Thresholds
    "savings_rate_thresholds": {
        "critical": 0.05,  # < 5%
        "weak": 0.10,  # 5-10%
        "moderate": 0.20,  # 10-20%
        "strong": 0.30,  # 20-30%
        "excellent": 0.40  # 30%+
    },
    
    # Investment Readiness Criteria
    "investment_readiness": {
        "min_savings_rate": 0.10,  # 10%
        "min_emergency_fund_months": {
            IncomeType.SALARIED: 6,
            IncomeType.VARIABLE: 9,
            IncomeType.BUSINESS: 12
        }
    },
    
    # Goal Planning Defaults
    "goal_planning": {
        "min_goal_amount": 10000,  # ₹10,000
        "max_goal_amount": 10000000,  # ₹1 crore
        "min_time_horizon_months": 1,
        "max_time_horizon_months": 360,  # 30 years
        "default_return_rate": 8.0,  # 8% for balanced approach
    }
}


# Price Caps (ANTI-HALLUCINATION)
PRICE_CAPS = {
    "laptop": 500000,  # ₹5 lakhs max
    "camera": 400000,  # ₹4 lakhs max
    "phone": 200000,  # ₹2 lakhs max
    "bike": 300000,  # ₹3 lakhs max
    "car": 2000000,  # ₹20 lakhs max
    "house_down_payment": 5000000,  # ₹50 lakhs max
    "education": 5000000,  # ₹50 lakhs max
    "wedding": 2000000,  # ₹20 lakhs max
    "vacation": 500000,  # ₹5 lakhs max
}


# Whitelisted Domains for Web Search (FACTS ONLY)
WHITELISTED_DOMAINS = {
    # Official Brand Sites (for prices)
    "apple.com",
    "sony.co.in",
    "samsung.com",
    
    # Government / Regulatory
    "rbi.org.in",  # Reserve Bank of India
    "incometaxindia.gov.in",  # Income Tax Department
    "epfindia.gov.in",  # EPF
    "nsdl.co.in",  # NSDL
    "sebi.gov.in",  # SEBI
    
    # Official Financial Institutions
    "sbi.co.in",  # SBI (for rates)
    "hdfcbank.com",  # HDFC (for rates)
    "icicidirect.com",  # ICICI (for rates)
}


# Blocked Domains (NEVER USE)
BLOCKED_DOMAINS = {
    "moneycontrol.com",  # News/blogs
    "economictimes.indiatimes.com",  # News
    "youtube.com",  # Influencers
    "reddit.com",  # Anecdotes
    "quora.com",  # Opinions
    "medium.com",  # Blogs
}


def get_assumption(category: str, key: str = None) -> Any:
    """
    Get assumption from library.
    
    Args:
        category: Assumption category (e.g., "emergency_fund_months")
        key: Optional key within category
        
    Returns:
        Assumption value
    """
    if category not in ASSUMPTIONS:
        raise ValueError(f"Unknown assumption category: {category}")
    
    if key is None:
        return ASSUMPTIONS[category]
    
    return ASSUMPTIONS[category].get(key)


def get_time_horizon_bucket(months: int) -> TimeHorizon:
    """
    Determine time horizon bucket based on months.
    
    Args:
        months: Time horizon in months
        
    Returns:
        TimeHorizon enum
    """
    if months <= 12:
        return TimeHorizon.SHORT_TERM
    elif months <= 60:
        return TimeHorizon.MEDIUM_TERM
    else:
        return TimeHorizon.LONG_TERM


def get_suitable_buckets(time_horizon: TimeHorizon) -> list[InvestmentBucket]:
    """
    Get suitable investment buckets for time horizon.
    
    Args:
        time_horizon: Time horizon enum
        
    Returns:
        List of suitable investment buckets
    """
    return ASSUMPTIONS["time_horizons"][time_horizon]["suitable_buckets"]


def get_return_assumption(bucket: InvestmentBucket) -> Dict[str, Any]:
    """
    Get return assumption for investment bucket.
    
    Args:
        bucket: Investment bucket enum
        
    Returns:
        Dict with return assumptions
    """
    return ASSUMPTIONS["return_assumptions"][bucket]


def is_domain_whitelisted(domain: str) -> bool:
    """Check if domain is whitelisted for web search."""
    return any(allowed in domain.lower() for allowed in WHITELISTED_DOMAINS)


def is_domain_blocked(domain: str) -> bool:
    """Check if domain is blocked."""
    return any(blocked in domain.lower() for blocked in BLOCKED_DOMAINS)


def get_price_cap(category: str) -> float:
    """
    Get price cap for category.
    
    Args:
        category: Price category (e.g., "laptop", "camera")
        
    Returns:
        Maximum allowed price
    """
    return PRICE_CAPS.get(category.lower(), 1000000)  # Default 10 lakhs
