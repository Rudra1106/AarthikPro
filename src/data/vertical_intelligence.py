"""
Vertical Intelligence System - Business segment/vertical analysis.

Enables institutional-grade vertical-level analysis for RAs and traders.
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from src.data.mongo_client import get_mongo_client

logger = logging.getLogger(__name__)


# Vertical Taxonomy - Industry-specific segment mappings
VERTICAL_TAXONOMY = {
    # IT Services Companies
    "IT_SERVICES": {
        "companies": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTI", "COFORGE"],
        "verticals": {
            "BFSI": {
                "display_name": "Banking & Financial Services",
                "keywords": ["bfsi", "banking", "financial services", "insurance", "fintech", "capital markets"],
                "typical_margin": 25.0,
                "growth_benchmark": 12.0
            },
            "Manufacturing": {
                "display_name": "Manufacturing",
                "keywords": ["manufacturing", "industrial", "automotive", "discrete manufacturing"],
                "typical_margin": 22.0,
                "growth_benchmark": 10.0
            },
            "Retail": {
                "display_name": "Retail & CPG",
                "keywords": ["retail", "consumer", "cpg", "consumer goods", "e-commerce"],
                "typical_margin": 23.0,
                "growth_benchmark": 11.0
            },
            "Healthcare": {
                "display_name": "Healthcare & Life Sciences",
                "keywords": ["healthcare", "life sciences", "pharma", "medical", "clinical"],
                "typical_margin": 24.0,
                "growth_benchmark": 13.0
            },
            "Telecom": {
                "display_name": "Telecom & Media",
                "keywords": ["telecom", "telecommunications", "media", "communications"],
                "typical_margin": 21.0,
                "growth_benchmark": 9.0
            },
            "Energy": {
                "display_name": "Energy & Utilities",
                "keywords": ["energy", "utilities", "oil", "gas", "power"],
                "typical_margin": 20.0,
                "growth_benchmark": 8.0
            },
            "HiTech": {
                "display_name": "Hi-Tech & Products",
                "keywords": ["hi-tech", "technology", "products", "software products", "isv"],
                "typical_margin": 26.0,
                "growth_benchmark": 14.0
            }
        }
    },
    
    # Automotive Companies
    "AUTOMOTIVE": {
        "companies": ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO"],
        "verticals": {
            "PassengerVehicles": {
                "display_name": "Passenger Vehicles",
                "keywords": ["passenger", "cars", "sedan", "suv", "hatchback", "pv"],
                "typical_margin": 8.0,
                "growth_benchmark": 10.0
            },
            "CommercialVehicles": {
                "display_name": "Commercial Vehicles",
                "keywords": ["commercial", "trucks", "buses", "lcv", "mcv", "hcv", "cv"],
                "typical_margin": 6.0,
                "growth_benchmark": 8.0
            },
            "ElectricVehicles": {
                "display_name": "Electric Vehicles (EV)",
                "keywords": ["electric", "ev", "electric vehicle", "battery", "e-mobility"],
                "typical_margin": -5.0,  # Often negative initially
                "growth_benchmark": 50.0
            },
            "Tractors": {
                "display_name": "Tractors & Farm Equipment",
                "keywords": ["tractor", "farm", "agriculture", "agri"],
                "typical_margin": 12.0,
                "growth_benchmark": 7.0
            },
            "TwoWheelers": {
                "display_name": "Two Wheelers",
                "keywords": ["two wheeler", "motorcycle", "scooter", "bike", "2w"],
                "typical_margin": 10.0,
                "growth_benchmark": 9.0
            },
            "SpareParts": {
                "display_name": "Spare Parts & Services",
                "keywords": ["spare parts", "aftermarket", "service", "parts"],
                "typical_margin": 15.0,
                "growth_benchmark": 12.0
            }
        }
    },
    
    # Banking Companies
    "BANKING": {
        "companies": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "INDUSINDBK"],
        "verticals": {
            "RetailBanking": {
                "display_name": "Retail Banking",
                "keywords": ["retail", "retail banking", "consumer", "personal banking", "home loan", "auto loan"],
                "typical_margin": 45.0,
                "growth_benchmark": 15.0
            },
            "CorporateBanking": {
                "display_name": "Corporate Banking",
                "keywords": ["corporate", "wholesale", "corporate banking", "sme", "msme"],
                "typical_margin": 35.0,
                "growth_benchmark": 10.0
            },
            "Treasury": {
                "display_name": "Treasury Operations",
                "keywords": ["treasury", "investment", "trading", "securities"],
                "typical_margin": 60.0,
                "growth_benchmark": 5.0
            },
            "International": {
                "display_name": "International Operations",
                "keywords": ["international", "overseas", "foreign", "global"],
                "typical_margin": 30.0,
                "growth_benchmark": 12.0
            }
        }
    },
    
    # Conglomerates
    "CONGLOMERATE": {
        "companies": ["RELIANCE", "ITC", "ADANIENT"],
        "verticals": {
            "OilGas": {
                "display_name": "Oil & Gas",
                "keywords": ["oil", "gas", "refining", "petrochemicals", "o2c"],
                "typical_margin": 10.0,
                "growth_benchmark": 8.0
            },
            "Retail": {
                "display_name": "Retail",
                "keywords": ["retail", "reliance retail", "consumer", "stores"],
                "typical_margin": 7.0,
                "growth_benchmark": 25.0
            },
            "Telecom": {
                "display_name": "Telecom (Jio)",
                "keywords": ["jio", "telecom", "digital", "connectivity"],
                "typical_margin": 45.0,
                "growth_benchmark": 20.0
            },
            "DigitalServices": {
                "display_name": "Digital Services",
                "keywords": ["digital", "platforms", "jiomart", "technology"],
                "typical_margin": 30.0,
                "growth_benchmark": 40.0
            }
        }
    }
}


def get_company_industry(ticker: str) -> Optional[str]:
    """Get industry category for a ticker."""
    for industry, config in VERTICAL_TAXONOMY.items():
        if ticker in config["companies"]:
            return industry
    return None


def get_vertical_metadata(ticker: str) -> Dict[str, Any]:
    """
    Get vertical taxonomy for a company.
    
    Returns:
        Dict with industry and vertical definitions
    """
    industry = get_company_industry(ticker)
    if not industry:
        return {}
    
    return {
        "ticker": ticker,
        "industry": industry,
        "verticals": VERTICAL_TAXONOMY[industry]["verticals"]
    }


async def get_vertical_performance(
    ticker: str,
    fiscal_year: str = "FY2024"
) -> Dict[str, Any]:
    """
    Extract segment-wise performance using Pinecone semantic search + LLM.
    
    Since MongoDB tables don't have segment data, we use:
    1. Pinecone to find segment-related content from annual reports
    2. LLM to extract structured vertical data
    
    Args:
        ticker: Company ticker (e.g., "TCS")
        fiscal_year: Fiscal year (e.g., "FY2024")
        
    Returns:
        Dict with vertical performance data
    """
    from src.data.pinecone_client import get_pinecone_client
    from langchain_openai import ChatOpenAI
    from src.config import settings
    
    # Get vertical metadata
    metadata = get_vertical_metadata(ticker)
    if not metadata:
        return {
            "error": f"No vertical taxonomy defined for {ticker}",
            "ticker": ticker
        }
    
    # Get Pinecone client
    pinecone = get_pinecone_client()
    
    # Query Pinecone for segment-related content
    query = f"{ticker} segment-wise revenue vertical performance business segment breakdown {fiscal_year}"
    
    try:
        results = await pinecone.query(
            query=query,
            top_k=5,
            filter={"ticker": ticker}
        )
        
        if not results:
            return {
                "error": f"No segment data found in annual reports for {ticker}",
                "ticker": ticker,
                "fiscal_year": fiscal_year,
                "suggestion": "Try querying general company performance or check if annual report is available"
            }
        
        # Combine results into context
        context = "\n\n".join([r.get("text", "") for r in results])
        
        # Get vertical names from taxonomy
        verticals = metadata.get("verticals", {})
        vertical_names = [v["display_name"] for v in verticals.values()]
        
        # Use LLM to extract structured vertical data
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1
        )
        
        extraction_prompt = f"""Extract segment/vertical-wise performance data for {ticker} from the following text.

Expected verticals for {ticker}: {', '.join(vertical_names)}

Text:
{context}

Extract the following for each vertical/segment mentioned:
- Vertical name (match to expected verticals if possible)
- Revenue (in Crores)
- YoY growth percentage (if mentioned)
- Any margin or profitability information

Return ONLY a JSON array with this structure:
[
  {{
    "vertical": "BFSI",
    "revenue": 45000,
    "yoy_growth": 12.5,
    "notes": "Strong demand, deal pipeline robust"
  }},
  ...
]

If no segment data is found, return an empty array [].
Return ONLY the JSON, no other text."""

        response = await llm.ainvoke(extraction_prompt)
        
        # Parse LLM response
        import json
        import re
        
        response_text = response.content
        
        # Extract JSON from response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if not json_match:
            return {
                "error": "Could not extract structured vertical data from annual report",
                "ticker": ticker,
                "fiscal_year": fiscal_year,
                "raw_context": context[:500]  # First 500 chars for debugging
            }
        
        verticals_data = json.loads(json_match.group())
        
        if not verticals_data:
            return {
                "error": "No vertical data found in annual report",
                "ticker": ticker,
                "fiscal_year": fiscal_year,
                "suggestion": "Company may not report segment-wise data or data not in annual report"
            }
        
        # Calculate total revenue and enrich data
        total_revenue = sum(v.get("revenue", 0) for v in verticals_data)
        
        for vertical in verticals_data:
            # Add % of total
            if total_revenue > 0:
                vertical["revenue_pct"] = (vertical.get("revenue", 0) / total_revenue) * 100
            else:
                vertical["revenue_pct"] = 0
            
            # Classify trend
            yoy_growth = vertical.get("yoy_growth", 0)
            vertical["trend"] = classify_vertical_trend(yoy_growth, 10.0)  # Default benchmark
            
            # Add display name
            vertical["display_name"] = vertical.get("vertical", "Unknown")
        
        # Sort by revenue
        verticals_data.sort(key=lambda x: x.get("revenue", 0), reverse=True)
        
        # Identify top performers
        top_vertical = verticals_data[0]["vertical"] if verticals_data else None
        fastest_growing = max(verticals_data, key=lambda x: x.get("yoy_growth", 0))["vertical"] if verticals_data else None
        
        return {
            "ticker": ticker,
            "fiscal_year": fiscal_year,
            "industry": metadata["industry"],
            "verticals": verticals_data,
            "total_revenue": total_revenue,
            "top_vertical": top_vertical,
            "fastest_growing": fastest_growing,
            "vertical_count": len(verticals_data),
            "data_source": "pinecone_annual_reports"
        }
        
    except Exception as e:
        logger.error(f"Error extracting vertical performance for {ticker}: {e}")
        return {
            "error": f"Error extracting vertical data: {str(e)}",
            "ticker": ticker,
            "fiscal_year": fiscal_year
        }



def match_vertical_to_taxonomy(
    vertical_name: str,
    taxonomy: Dict[str, Dict]
) -> Optional[str]:
    """
    Match a vertical name from table to taxonomy using keywords.
    
    Args:
        vertical_name: Name from table (e.g., "Banking and Financial Services")
        taxonomy: Vertical taxonomy dict
        
    Returns:
        Matched vertical key or None
    """
    vertical_name_lower = vertical_name.lower()
    
    for vertical_key, vertical_config in taxonomy.items():
        keywords = vertical_config.get("keywords", [])
        for keyword in keywords:
            if keyword in vertical_name_lower:
                return vertical_key
    
    return None


def parse_financial_value(value_str: str) -> float:
    """
    Parse financial value from string.
    
    Examples:
        "1,00,000" -> 100000
        "1000.5" -> 1000.5
        "N/A" -> 0
    """
    if not value_str or value_str == "N/A" or value_str == "-":
        return 0.0
    
    # Remove commas and convert to float
    try:
        cleaned = value_str.replace(",", "").strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0


def classify_vertical_trend(
    yoy_growth: float,
    benchmark: float
) -> str:
    """
    Classify vertical trend based on YoY growth vs benchmark.
    
    Returns:
        "growing", "stable", or "declining"
    """
    if yoy_growth >= benchmark * 1.2:  # 20% above benchmark
        return "growing"
    elif yoy_growth >= benchmark * 0.8:  # Within 20% of benchmark
        return "stable"
    else:
        return "declining"
