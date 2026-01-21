"""
Selective Web Search for Personal Finance

CRITICAL RULES:
- Web search = facts only (prices, rates, policy changes)
- Never fetch advice, rankings, or opinions
- Source whitelisting enforced
- Price caps enforced (anti-hallucination)

Use cases:
✅ Product prices (for goal planning)
✅ Interest rates (PPF, EPF, FD)
✅ Tax limits and rules
✅ Policy changes

NOT for:
❌ Investment advice
❌ Fund rankings
❌ "Best" recommendations
❌ Influencer opinions
"""
from typing import Optional, Dict, Any, List
import logging
import re

from .pf_assumptions import (
    is_domain_whitelisted,
    is_domain_blocked,
    get_price_cap,
    PRICE_CAPS
)

logger = logging.getLogger(__name__)


class PFWebSearchGuardrails:
    """
    Enforces guardrails for personal finance web search.
    
    Ensures only factual data is fetched from trusted sources.
    """
    
    def __init__(self):
        self.allowed_query_types = {
            "price",  # Product prices
            "rate",  # Interest rates
            "tax",  # Tax limits/rules
            "policy"  # Policy changes
        }
    
    def classify_query_type(self, query: str) -> Optional[str]:
        """
        Classify query type to determine if web search is allowed.
        
        Args:
            query: User query
            
        Returns:
            Query type if allowed, None otherwise
        """
        query_lower = query.lower()
        
        # Price queries
        if any(kw in query_lower for kw in ["price", "cost", "how much"]):
            if any(product in query_lower for product in ["macbook", "laptop", "camera", "phone", "bike", "car"]):
                return "price"
        
        # Rate queries
        if any(kw in query_lower for kw in ["interest rate", "ppf rate", "epf rate", "fd rate"]):
            return "rate"
        
        # Tax queries
        if any(kw in query_lower for kw in ["tax limit", "80c", "80d", "tax rule"]):
            return "tax"
        
        # Policy queries
        if any(kw in query_lower for kw in ["policy change", "new rule", "regulation"]):
            return "policy"
        
        return None
    
    def should_use_web_search(self, query: str) -> bool:
        """
        Determine if web search should be used for this query.
        
        Args:
            query: User query
            
        Returns:
            True if web search is appropriate
        """
        query_type = self.classify_query_type(query)
        return query_type is not None
    
    def filter_search_results(
        self,
        results: List[Dict[str, Any]],
        query_type: str
    ) -> List[Dict[str, Any]]:
        """
        Filter search results based on domain whitelisting and query type.
        
        Args:
            results: Raw search results
            query_type: Type of query (price, rate, tax, policy)
            
        Returns:
            Filtered results
        """
        filtered = []
        
        for result in results:
            url = result.get("url", "")
            domain = self._extract_domain(url)
            
            # Check if domain is blocked
            if is_domain_blocked(domain):
                logger.warning(f"Blocked domain: {domain}")
                continue
            
            # For price queries, only allow official brand sites
            if query_type == "price":
                if not is_domain_whitelisted(domain):
                    logger.warning(f"Non-whitelisted domain for price query: {domain}")
                    continue
            
            # For rate/tax/policy, allow government sites only
            if query_type in ["rate", "tax", "policy"]:
                if not any(gov in domain for gov in ["gov.in", "rbi.org.in", "sebi.gov.in"]):
                    logger.warning(f"Non-government domain for {query_type} query: {domain}")
                    continue
            
            filtered.append(result)
        
        return filtered
    
    def extract_price_from_text(
        self,
        text: str,
        category: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract price from text with anti-hallucination caps.
        
        Args:
            text: Text containing price
            category: Price category (laptop, camera, etc.)
            
        Returns:
            Dict with price info or None
        """
        # Extract prices in rupees
        price_patterns = [
            r'₹\s*([0-9,]+)',
            r'Rs\.?\s*([0-9,]+)',
            r'INR\s*([0-9,]+)',
        ]
        
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    price = float(match.replace(',', ''))
                    prices.append(price)
                except ValueError:
                    continue
        
        if not prices:
            return None
        
        # Get price range
        min_price = min(prices)
        max_price = max(prices)
        
        # Apply price cap
        price_cap = get_price_cap(category)
        
        if min_price > price_cap or max_price > price_cap:
            logger.warning(f"Price exceeds cap for {category}: {max_price} > {price_cap}")
            return None
        
        return {
            "min_price": min_price,
            "max_price": max_price,
            "price_range": f"₹{min_price:,.0f} - ₹{max_price:,.0f}",
            "category": category,
            "source_label": "Public listed prices (approximate)"
        }
    
    def extract_rate_from_text(self, text: str, rate_type: str) -> Optional[Dict[str, Any]]:
        """
        Extract interest rate from text.
        
        Args:
            text: Text containing rate
            rate_type: Type of rate (ppf, epf, fd, etc.)
            
        Returns:
            Dict with rate info or None
        """
        # Extract percentage rates
        rate_patterns = [
            r'(\d+\.?\d*)\s*%',
            r'(\d+\.?\d*)\s*percent',
        ]
        
        rates = []
        for pattern in rate_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    rate = float(match)
                    # Sanity check: rates should be between 0-20%
                    if 0 < rate < 20:
                        rates.append(rate)
                except ValueError:
                    continue
        
        if not rates:
            return None
        
        # Use most recent/highest rate (typically current rate)
        current_rate = max(rates)
        
        return {
            "rate": current_rate,
            "rate_label": f"{current_rate}%",
            "rate_type": rate_type,
            "source_label": "As per latest published data"
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        # Simple domain extraction
        if "://" in url:
            url = url.split("://")[1]
        domain = url.split("/")[0]
        return domain.lower()


# Singleton instance
_guardrails_instance: Optional[PFWebSearchGuardrails] = None


def get_web_search_guardrails() -> PFWebSearchGuardrails:
    """Get singleton web search guardrails instance."""
    global _guardrails_instance
    if _guardrails_instance is None:
        _guardrails_instance = PFWebSearchGuardrails()
    return _guardrails_instance


async def fetch_product_price(
    product_name: str,
    category: str,
    perplexity_client
) -> Optional[Dict[str, Any]]:
    """
    Fetch product price with guardrails.
    
    Args:
        product_name: Product name (e.g., "MacBook Pro M3")
        category: Price category (laptop, camera, etc.)
        perplexity_client: Perplexity client instance
        
    Returns:
        Price info dict or None
    """
    guardrails = get_web_search_guardrails()
    
    # Construct search query
    query = f"{product_name} price India official"
    
    try:
        # Search using Perplexity
        results = await perplexity_client.web_search(
            query=query,
            country="IN",
            max_results=3
        )
        
        if not results or "answer" not in results:
            return None
        
        # Extract price from answer
        price_info = guardrails.extract_price_from_text(
            results["answer"],
            category
        )
        
        if price_info:
            logger.info(f"Fetched price for {product_name}: {price_info['price_range']}")
        
        return price_info
        
    except Exception as e:
        logger.error(f"Error fetching price for {product_name}: {e}")
        return None


async def fetch_interest_rate(
    rate_type: str,
    perplexity_client
) -> Optional[Dict[str, Any]]:
    """
    Fetch interest rate with guardrails.
    
    Args:
        rate_type: Type of rate (ppf, epf, fd, etc.)
        perplexity_client: Perplexity client instance
        
    Returns:
        Rate info dict or None
    """
    guardrails = get_web_search_guardrails()
    
    # Construct search query
    query_map = {
        "ppf": "PPF interest rate India current",
        "epf": "EPF interest rate India current",
        "fd": "Fixed deposit interest rate India SBI HDFC current"
    }
    
    query = query_map.get(rate_type.lower(), f"{rate_type} interest rate India current")
    
    try:
        # Search using Perplexity
        results = await perplexity_client.web_search(
            query=query,
            country="IN",
            max_results=2
        )
        
        if not results or "answer" not in results:
            return None
        
        # Extract rate from answer
        rate_info = guardrails.extract_rate_from_text(
            results["answer"],
            rate_type
        )
        
        if rate_info:
            logger.info(f"Fetched {rate_type} rate: {rate_info['rate_label']}")
        
        return rate_info
        
    except Exception as e:
        logger.error(f"Error fetching {rate_type} rate: {e}")
        return None
