"""
Symbol Mapper - Map user-friendly names to Zerodha symbols.

Handles:
- Index names (Nifty 50, Sensex, Bank Nifty)
- Stock aliases (Reliance, TCS, HDFC Bank)
- Common variations and typos
"""

from typing import Optional, Dict, List
import re
import logging

logger = logging.getLogger(__name__)


class SymbolMapper:
    """
    Map user-friendly names to stock/index symbols.
    """
    
    # Index mappings
    INDEX_MAPPINGS = {
        # Nifty indices
        "nifty": "NIFTY 50",
        "nifty 50": "NIFTY 50",
        "nifty50": "NIFTY 50",
        "nifty index": "NIFTY 50",
        "nifty bank": "NIFTY BANK",
        "bank nifty": "NIFTY BANK",
        "banknifty": "NIFTY BANK",
        "nifty it": "NIFTY IT",
        "nifty pharma": "NIFTY PHARMA",
        "nifty auto": "NIFTY AUTO",
        "nifty metal": "NIFTY METAL",
        "nifty fmcg": "NIFTY FMCG",
        "nifty energy": "NIFTY ENERGY",
        "nifty financial": "NIFTY FINANCIAL SERVICES",
        "nifty midcap": "NIFTY MIDCAP 100",
        "nifty smallcap": "NIFTY SMALLCAP 100",
        
        # Sensex
        "sensex": "SENSEX",
        "bse sensex": "SENSEX",
        "bse": "SENSEX",
    }
    
    # Stock aliases (common names → symbols)
    STOCK_ALIASES = {
        # Top stocks
        "reliance": "RELIANCE",
        "reliance industries": "RELIANCE",
        "ril": "RELIANCE",
        
        "tcs": "TCS",
        "tata consultancy": "TCS",
        "tata consultancy services": "TCS",
        
        "hdfc bank": "HDFCBANK",
        "hdfcbank": "HDFCBANK",
        "hdfc": "HDFCBANK",
        
        "infosys": "INFY",
        "infy": "INFY",
        
        "icici bank": "ICICIBANK",
        "icici": "ICICIBANK",
        
        "yes bank": "YESBANK",
        "yes": "YESBANK",
        
        "sbi": "SBIN",
        "state bank": "SBIN",
        "state bank of india": "SBIN",
        
        "bharti airtel": "BHARTIARTL",
        "airtel": "BHARTIARTL",
        
        "itc": "ITC",
        "itc limited": "ITC",
        
        "wipro": "WIPRO",
        
        "hcl tech": "HCLTECH",
        "hcl": "HCLTECH",
        "hcl technologies": "HCLTECH",
        
        "asian paints": "ASIANPAINT",
        "asian paint": "ASIANPAINT",
        
        "maruti": "MARUTI",
        "maruti suzuki": "MARUTI",
        
        "bajaj finance": "BAJFINANCE",
        "bajaj": "BAJFINANCE",
        
        "tata motors": "TATAMOTORS",
        "tatamotors": "TATAMOTORS",
        
        "titan": "TITAN",
        "titan company": "TITAN",
        
        "adani": "ADANIENT",
        "adani enterprises": "ADANIENT",
        
        "larsen": "LT",
        "l&t": "LT",
        "larsen and toubro": "LT",
        "larsen & toubro": "LT",
        
        # Energy & Renewables
        "suzlon": "SUZLON",
        "suzlon energy": "SUZLON",
        
        # Metals & Steel
        "tata steel": "TATASTEEL",
        "tatasteel": "TATASTEEL",
        
        # ETFs
        "tatasilv": "TATASILV",  # Tata Silver ETF
        "tata silver": "TATASILV",
        "tata silver etf": "TATASILV",
        
        # Other stocks
        "cupid": "CUPID",
        "cupid ltd": "CUPID",
    }
    
    def __init__(self):
        # Combine all mappings for quick lookup
        self.all_mappings = {**self.INDEX_MAPPINGS, **self.STOCK_ALIASES}
    
    def normalize_query(self, query: str) -> str:
        """Normalize query for matching."""
        return query.lower().strip()
    
    def map_symbol(self, user_input: str) -> Optional[str]:
        """
        Map user-friendly name to symbol.
        
        Args:
            user_input: User's query or symbol reference
        
        Returns:
            Mapped symbol or None
        """
        normalized = self.normalize_query(user_input)
        
        # Direct lookup
        if normalized in self.all_mappings:
            symbol = self.all_mappings[normalized]
            logger.info(f"Mapped '{user_input}' → '{symbol}'")
            return symbol
        
        # Try partial matching for multi-word queries
        for key, symbol in self.all_mappings.items():
            if key in normalized or normalized in key:
                logger.info(f"Partial match: '{user_input}' → '{symbol}' (via '{key}')")
                return symbol
        
        # No mapping found
        return None
    
    def extract_from_query(self, query: str) -> List[str]:
        """
        Extract and map ALL symbols from full query.
        
        CRITICAL FIX: Now returns ALL matching symbols, not just first one.
        This fixes comparison queries like "Compare TCS and Infosys".
        
        Args:
            query: Full user query
        
        Returns:
            List of mapped symbols (may be empty)
        """
        normalized = self.normalize_query(query)
        symbols = []
        
        # Extract ALL matching symbols
        for key, symbol in self.all_mappings.items():
            if key in normalized:
                if symbol not in symbols:
                    symbols.append(symbol)
                    logger.info(f"Extracted '{symbol}' from query: '{query}'")
        
        return symbols
    
    def is_index(self, symbol: str) -> bool:
        """Check if symbol is an index."""
        return symbol in self.INDEX_MAPPINGS.values()


# Singleton instance
_symbol_mapper: Optional[SymbolMapper] = None


def get_symbol_mapper() -> SymbolMapper:
    """Get singleton symbol mapper instance."""
    global _symbol_mapper
    if _symbol_mapper is None:
        _symbol_mapper = SymbolMapper()
    return _symbol_mapper
