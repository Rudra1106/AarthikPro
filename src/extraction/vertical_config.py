"""
Vertical/Segment Configuration
Defines keywords and rules for detecting business verticals in annual reports.
"""

# Vertical keywords for Indian market
VERTICAL_KEYWORDS = {
    "BFSI": [
        "banking", "financial services", "insurance", "bfsi", "nbfc",
        "bank", "finance", "lending", "credit", "loans"
    ],
    "Manufacturing": [
        "manufacturing", "industrial", "production", "factory",
        "assembly", "fabrication"
    ],
    "Retail": [
        "retail", "consumer", "e-commerce", "ecommerce", "shopping",
        "stores", "outlets", "distribution"
    ],
    "Healthcare": [
        "healthcare", "pharma", "pharmaceutical", "life sciences",
        "medical", "hospital", "diagnostics", "drugs"
    ],
    "Energy": [
        "energy", "power", "utilities", "oil", "gas", "petroleum",
        "electricity", "renewable", "solar", "wind"
    ],
    "IT Services": [
        "it services", "software", "technology", "digital",
        "information technology", "tech", "cloud", "saas"
    ],
    "Telecom": [
        "telecom", "telecommunications", "network", "mobile",
        "broadband", "connectivity", "wireless"
    ],
    "Real Estate": [
        "real estate", "property", "construction", "infrastructure",
        "housing", "residential", "commercial"
    ],
    "Auto": [
        "automotive", "automobile", "vehicles", "auto", "cars",
        "two-wheeler", "four-wheeler", "ev", "electric vehicle"
    ],
    "Metals": [
        "metals", "steel", "mining", "iron", "aluminum",
        "copper", "zinc", "ore"
    ],
    "FMCG": [
        "fmcg", "consumer goods", "packaged goods", "food",
        "beverages", "personal care", "household"
    ],
    "Chemicals": [
        "chemicals", "specialty chemicals", "agrochemicals",
        "petrochemicals", "fertilizers"
    ],
    "Textiles": [
        "textiles", "apparel", "garments", "fabric", "clothing",
        "fashion", "yarn"
    ]
}

# Growth/performance terms
GROWTH_TERMS = [
    "grew", "growth", "declined", "decline", "increase", "increased",
    "decrease", "decreased", "margin", "margins", "revenue", "revenues",
    "profit", "profits", "ebitda", "sales", "turnover", "performance",
    "yoy", "y-o-y", "qoq", "q-o-q", "expansion", "contraction"
]

# Numeric indicators
NUMERIC_PATTERNS = [
    r'\d+\.?\d*%',  # Percentages
    r'\d+\.?\d*\s*cr',  # Crores
    r'\d+\.?\d*\s*lakh',  # Lakhs
    r'\d+\.?\d*\s*million',  # Millions
    r'\d+\.?\d*\s*billion',  # Billions
]

# Confidence thresholds
CONFIDENCE_THRESHOLDS = {
    "high": 0.8,
    "medium": 0.5,
    "low": 0.3
}

def get_vertical_keywords() -> dict:
    """Get vertical keywords dictionary."""
    return VERTICAL_KEYWORDS

def get_growth_terms() -> list:
    """Get growth/performance terms."""
    return GROWTH_TERMS

def get_all_verticals() -> list:
    """Get list of all vertical names."""
    return list(VERTICAL_KEYWORDS.keys())
