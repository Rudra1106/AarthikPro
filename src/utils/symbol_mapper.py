"""
Symbol Mapper - Company Name to Ticker Conversion.

Maps company names to stock ticker symbols for better query understanding.
"""

from typing import Optional, Dict

# Comprehensive company name to ticker mapping
COMPANY_NAME_TO_TICKER: Dict[str, str] = {
    # Food Delivery & Restaurant Tech
    "zomato": "ZOMATO",
    "zomato limited": "ZOMATO",
    "eternal": "ZOMATO",
    "eternal limited": "ZOMATO",
    "swiggy": "SWIGGY",
    
    # IT Services
    "tcs": "TCS",
    "tata consultancy": "TCS",
    "tata consultancy services": "TCS",
    "infosys": "INFY",
    "wipro": "WIPRO",
    "hcl": "HCLTECH",
    "hcl tech": "HCLTECH",
    "hcl technologies": "HCLTECH",
    "tech mahindra": "TECHM",
    "ltim": "LTIM",
    "lti mindtree": "LTIM",
    
    # Banking
    "hdfc bank": "HDFCBANK",
    "hdfc": "HDFCBANK",
    "icici bank": "ICICIBANK",
    "icici": "ICICIBANK",
    "sbi": "SBIN",
    "state bank": "SBIN",
    "kotak": "KOTAKBANK",
    "kotak bank": "KOTAKBANK",
    "axis bank": "AXISBANK",
    "axis": "AXISBANK",
    "indusind": "INDUSINDBK",
    "indusind bank": "INDUSINDBK",
    
    # NBFC & Finance
    "bajaj finance": "BAJFINANCE",
    "bajaj finserv": "BAJAJFINSV",
    
    # Conglomerates
    "reliance": "RELIANCE",
    "reliance industries": "RELIANCE",
    "ril": "RELIANCE",
    "tata motors": "TATAMOTORS",
    "tata steel": "TATASTEEL",
    "tata power": "TATAPOWER",
    "larsen": "LT",
    "larsen toubro": "LT",
    "l&t": "LT",
    
    # Auto
    "maruti": "MARUTI",
    "maruti suzuki": "MARUTI",
    "mahindra": "M&M",
    "m&m": "M&M",
    "bajaj auto": "BAJAJ-AUTO",
    "hero motocorp": "HEROMOTOCO",
    "hero": "HEROMOTOCO",
    "eicher": "EICHERMOT",
    "eicher motors": "EICHERMOT",
    "tvs motor": "TVSMOTOR",
    "tvs": "TVSMOTOR",
    
    # Pharma
    "sun pharma": "SUNPHARMA",
    "sun pharmaceutical": "SUNPHARMA",
    "dr reddy": "DRREDDY",
    "dr reddys": "DRREDDY",
    "cipla": "CIPLA",
    "lupin": "LUPIN",
    "divi": "DIVISLAB",
    "divis lab": "DIVISLAB",
    "apollo hospitals": "APOLLOHOSP",
    "apollo": "APOLLOHOSP",
    
    # FMCG
    "itc": "ITC",
    "hindustan unilever": "HINDUNILVR",
    "hul": "HINDUNILVR",
    "nestle": "NESTLEIND",
    "britannia": "BRITANNIA",
    "dabur": "DABUR",
    "marico": "MARICO",
    "godrej consumer": "GODREJCP",
    
    # Energy & Power
    "ongc": "ONGC",
    "ntpc": "NTPC",
    "power grid": "POWERGRID",
    "powergrid": "POWERGRID",
    "adani green": "ADANIGREEN",
    "adani power": "ADANIPOWER",
    "gail": "GAIL",
    
    # Telecom
    "bharti airtel": "BHARTIARTL",
    "airtel": "BHARTIARTL",
    "bharti": "BHARTIARTL",
    
    # Metals
    "jsw steel": "JSWSTEEL",
    "hindalco": "HINDALCO",
    "vedanta": "VEDL",
    "coal india": "COALINDIA",
    
    # Cement
    "ultratech": "ULTRACEMCO",
    "ultratech cement": "ULTRACEMCO",
    "shree cement": "SHREECEM",
    "ambuja": "AMBUJACEM",
    "ambuja cement": "AMBUJACEM",
    "acc": "ACC",
    
    # Insurance
    "sbi life": "SBILIFE",
    "hdfc life": "HDFCLIFE",
    "icici prudential": "ICICIPRULI",
    "lic": "LICI",
    
    # Consumer Durables
    "titan": "TITAN",
    "asian paints": "ASIANPAINT",
    
    # E-commerce & Fintech
    "paytm": "PAYTM",
    "nykaa": "NYKAA",
    "fsn": "NYKAA",
    "policybazaar": "POLICYBZR",
}


def map_company_name_to_ticker(query: str) -> Optional[str]:
    """
    Map company name in query to ticker symbol.
    
    Args:
        query: User query containing company name
        
    Returns:
        Ticker symbol if found, None otherwise
        
    Examples:
        >>> map_company_name_to_ticker("performance of Zomato Limited")
        'ZOMATO'
        >>> map_company_name_to_ticker("Tell me about TCS")
        'TCS'
    """
    query_lower = query.lower().strip()
    
    # Sort by length (longest first) to match "tata consultancy services" before "tata"
    sorted_names = sorted(COMPANY_NAME_TO_TICKER.items(), key=lambda x: len(x[0]), reverse=True)
    
    for company_name, ticker in sorted_names:
        if company_name in query_lower:
            return ticker
    
    return None


def get_all_tickers() -> list:
    """Get list of all supported ticker symbols."""
    return list(set(COMPANY_NAME_TO_TICKER.values()))


def get_company_names_for_ticker(ticker: str) -> list:
    """Get all company name variations for a ticker."""
    return [name for name, tick in COMPANY_NAME_TO_TICKER.items() if tick == ticker]
