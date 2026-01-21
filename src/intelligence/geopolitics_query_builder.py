"""
Geopolitics Query Builder - Optimized queries for Perplexity API.

Builds targeted queries for geopolitical intelligence:
- Sanctions status
- Market impact
- India-specific effects
- Trump-era policies
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re


class GeopoliticsQueryBuilder:
    """
    Build optimized Perplexity queries for geopolitics intelligence.
    
    Focuses on:
    - Data-grounded queries (avoid speculation)
    - Recency filters (7/30/90 days)
    - Entity extraction (countries, sectors)
    - India-specific context
    """
    
    # Country aliases for query optimization
    COUNTRY_ALIASES = {
        "US": ["United States", "USA", "America"],
        "Russia": ["Russian Federation"],
        "Iran": ["Islamic Republic of Iran"],
        "China": ["PRC", "People's Republic of China"],
        "India": ["Bharat"],
    }
    
    # Sector keywords for impact analysis
    SECTOR_KEYWORDS = {
        "Oil": ["crude", "petroleum", "energy", "oil"],
        "IT": ["technology", "software", "IT", "tech"],
        "Defense": ["military", "defense", "weapons"],
        "Banking": ["financial", "banking", "finance"],
        "Pharma": ["pharmaceutical", "healthcare", "drugs"],
    }
    
    def __init__(self):
        pass
    
    def build_sanctions_query(
        self,
        country: Optional[str] = None,
        admin: Optional[str] = None,
        recency_days: int = 30
    ) -> str:
        """
        Build query for sanctions status.
        
        Args:
            country: Target country (e.g., "Iran", "Russia")
            admin: Administration (e.g., "Trump", "Biden")
            recency_days: How recent (7, 30, 90 days)
        
        Returns:
            Optimized Perplexity query
        """
        query_parts = []
        
        # Base query
        if admin:
            query_parts.append(f"{admin}-era sanctions")
        else:
            query_parts.append("US sanctions")
        
        # Add country if specified
        if country:
            query_parts.append(f"on {country}")
        
        # Add recency
        if recency_days <= 7:
            query_parts.append("announced this week")
        elif recency_days <= 30:
            query_parts.append("announced in the last month")
        else:
            query_parts.append("current status")
        
        # Add data-grounding instruction
        query_parts.append("official announcements only")
        
        return " ".join(query_parts)
    
    def build_market_impact_query(
        self,
        event: str,
        asset_class: Optional[str] = None,
        recency_days: int = 7
    ) -> str:
        """
        Build query for market impact analysis.
        
        Args:
            event: Geopolitical event (e.g., "sanctions on Iran")
            asset_class: Asset class (e.g., "oil", "stocks", "currency")
            recency_days: How recent (7, 30 days)
        
        Returns:
            Optimized Perplexity query
        """
        query_parts = []
        
        # Base query
        query_parts.append(f"market reaction to {event}")
        
        # Add asset class if specified
        if asset_class:
            query_parts.append(f"{asset_class} prices")
        
        # Add recency
        if recency_days <= 7:
            time_filter = "this week"
        elif recency_days <= 30:
            time_filter = "this month"
        else:
            time_filter = "recent"
        
        query_parts.append(time_filter)
        
        # Add data-grounding
        query_parts.append("price data and market analysis")
        
        return " ".join(query_parts)
    
    def build_india_impact_query(
        self,
        event: str,
        sector: Optional[str] = None,
        recency_days: int = 30
    ) -> str:
        """
        Build query for India-specific impact.
        
        Args:
            event: Geopolitical event
            sector: Indian sector (e.g., "Oil", "IT", "Defense")
            recency_days: How recent
        
        Returns:
            Optimized Perplexity query
        """
        query_parts = []
        
        # Base query
        query_parts.append(f"impact of {event} on India")
        
        # Add sector if specified
        if sector:
            sector_keywords = self.SECTOR_KEYWORDS.get(sector, [sector])
            query_parts.append(f"{sector_keywords[0]} sector")
        
        # Add recency
        if recency_days <= 30:
            query_parts.append("recent analysis")
        
        # Add India-specific context
        query_parts.append("Indian economy trade exports imports")
        
        return " ".join(query_parts)
    
    def build_trump_policy_query(
        self,
        policy_area: Optional[str] = None,
        current_status: bool = True
    ) -> str:
        """
        Build query for Trump-era policies.
        
        Args:
            policy_area: Policy area (e.g., "trade", "sanctions", "tariffs")
            current_status: Whether to check current status
        
        Returns:
            Optimized Perplexity query
        """
        query_parts = []
        
        # Base query
        query_parts.append("Trump-era")
        
        # Add policy area
        if policy_area:
            query_parts.append(policy_area)
        else:
            query_parts.append("policies")
        
        # Add status check
        if current_status:
            query_parts.append("still active today current status")
        else:
            query_parts.append("historical impact")
        
        return " ".join(query_parts)
    
    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract entities from user query.
        
        Args:
            query: User's query
        
        Returns:
            Dict with countries, sectors, admins
        """
        entities = {
            "countries": [],
            "sectors": [],
            "admins": []
        }
        
        query_lower = query.lower()
        
        # Extract countries
        for country, aliases in self.COUNTRY_ALIASES.items():
            if country.lower() in query_lower or any(alias.lower() in query_lower for alias in aliases):
                entities["countries"].append(country)
        
        # Extract sectors
        for sector, keywords in self.SECTOR_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                entities["sectors"].append(sector)
        
        # Extract admins
        if "trump" in query_lower:
            entities["admins"].append("Trump")
        if "biden" in query_lower:
            entities["admins"].append("Biden")
        
        return entities
    
    def determine_recency(self, query: str) -> int:
        """
        Determine recency filter from query.
        
        Args:
            query: User's query
        
        Returns:
            Recency in days (7, 30, or 90)
        """
        query_lower = query.lower()
        
        # Check for explicit time references
        if any(word in query_lower for word in ["today", "this week", "recent", "latest"]):
            return 7
        elif any(word in query_lower for word in ["this month", "last month"]):
            return 30
        elif any(word in query_lower for word in ["this year", "recent years"]):
            return 90
        
        # Default to 30 days
        return 30
    
    def build_query(
        self,
        user_query: str,
        intent: str
    ) -> Tuple[str, Dict[str, any]]:
        """
        Build optimized query based on user intent.
        
        Args:
            user_query: User's original query
            intent: Detected intent (GEO_NEWS, SANCTIONS_STATUS, etc.)
        
        Returns:
            Tuple of (optimized_query, metadata)
        """
        # Extract entities
        entities = self.extract_entities(user_query)
        recency = self.determine_recency(user_query)
        
        # Build query based on intent
        if intent == "sanctions_status":
            country = entities["countries"][0] if entities["countries"] else None
            admin = entities["admins"][0] if entities["admins"] else None
            query = self.build_sanctions_query(country, admin, recency)
        
        elif intent == "market_impact":
            # Extract event from query
            event = user_query.lower().replace("how", "").replace("do", "").replace("did", "").strip()
            query = self.build_market_impact_query(event, recency_days=recency)
        
        elif intent == "india_impact":
            event = user_query.lower().replace("how", "").replace("do", "").replace("did", "").strip()
            sector = entities["sectors"][0] if entities["sectors"] else None
            query = self.build_india_impact_query(event, sector, recency)
        
        elif intent == "geo_news":
            # General geopolitics news
            query = f"latest geopolitical news {' '.join(entities['countries'])} last {recency} days"
        
        else:
            # Fallback
            query = user_query
        
        metadata = {
            "entities": entities,
            "recency_days": recency,
            "intent": intent
        }
        
        return query, metadata


# Singleton instance
_query_builder: Optional[GeopoliticsQueryBuilder] = None


def get_geopolitics_query_builder() -> GeopoliticsQueryBuilder:
    """Get singleton query builder instance."""
    global _query_builder
    if _query_builder is None:
        _query_builder = GeopoliticsQueryBuilder()
    return _query_builder
