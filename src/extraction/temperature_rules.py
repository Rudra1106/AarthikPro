"""
Temperature Classification Rules
Classifies documents as hot/warm/cold based on fiscal year.
"""

from datetime import datetime


def classify_temperature(fiscal_year: int) -> str:
    """
    Classify document temperature based on fiscal year.
    
    Hot: Last 3 years (FY2025, FY2024, FY2023) - goes to Pinecone
    Warm: 3-5 years old (MongoDB only)
    Cold: 5+ years old (MongoDB only)
    
    Args:
        fiscal_year: Fiscal year of the document
        
    Returns:
        "hot", "warm", or "cold"
    """
    current_year = datetime.now().year
    age = current_year - fiscal_year
    
    if age <= 3:  # Changed from 2 to 3 to include FY2025, FY2024, FY2023
        return "hot"
    elif age <= 5:
        return "warm"
    else:
        return "cold"


def should_index_in_pinecone(temperature: str) -> bool:
    """
    Determine if document should be indexed in Pinecone.
    
    Args:
        temperature: Document temperature
        
    Returns:
        True if should be indexed in Pinecone
    """
    return temperature == "hot"


def get_temperature_description(temperature: str) -> str:
    """Get human-readable description of temperature."""
    descriptions = {
        "hot": "Recent data (last 3 years: FY2025, FY2024, FY2023) - High query frequency",
        "warm": "Moderate age (3-5 years) - Medium query frequency",
        "cold": "Historical data (5+ years) - Low query frequency"
    }
    return descriptions.get(temperature, "Unknown")
