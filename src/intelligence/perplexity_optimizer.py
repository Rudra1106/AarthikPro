"""
Perplexity Search Optimizer - Lean & Fast

Single-query optimization for financial intelligence.
Minimizes latency and cost while maximizing relevance.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PerplexityOptimizer:
    """
    Optimize Perplexity searches for financial intelligence.
    
    Strategy: Single context-aware query (not parallel) for speed.
    """
    
    # Source prioritization (Tier 1 = highest quality)
    TIER_1_SOURCES = [
        "bloomberg.com",
        "reuters.com",
        "ft.com",
        "wsj.com",
    ]
    
    TIER_2_SOURCES = [
        "economictimes.indiatimes.com",
        "moneycontrol.com",
        "cnbc.com",
        "business-standard.com",
    ]
    
    def optimize_query(
        self,
        user_query: str,
        query_type: str = "market_overview",
        urgency: str = "high",
    ) -> str:
        """
        Optimize user query for Perplexity search.
        
        Args:
            user_query: Original user query
            query_type: "market_overview", "stock_analysis", "sector_analysis"
            urgency: "high" (24h), "medium" (7d), "low" (30d)
        
        Returns:
            Optimized search query
        """
        
        # Time filter based on urgency
        time_filter = {
            "high": "last 24 hours",
            "medium": "last 7 days",
            "low": "last 30 days",
        }.get(urgency, "last 24 hours")
        
        # Build context-aware query
        if query_type == "market_overview":
            return self._build_market_overview_query(user_query, time_filter)
        elif query_type == "stock_analysis":
            return self._build_stock_analysis_query(user_query, time_filter)
        elif query_type == "sector_analysis":
            return self._build_sector_analysis_query(user_query, time_filter)
        else:
            return self._build_generic_query(user_query, time_filter)
    
    def _build_market_overview_query(self, user_query: str, time_filter: str) -> str:
        """Build optimized query for market overview."""
        
        tier_1 = " OR ".join(self.TIER_1_SOURCES)
        tier_2 = " OR ".join(self.TIER_2_SOURCES)
        
        return f"""
Search for latest financial market developments: {user_query}

FOCUS AREAS:
1. Geopolitical events affecting markets (wars, sanctions, trade tensions)
2. Central bank decisions and monetary policy
3. Major corporate earnings or market-moving announcements
4. Economic data (inflation, GDP, employment)
5. Significant market volatility or unusual movements

TIME: {time_filter}
SOURCES: Prioritize {tier_1} then {tier_2}
GEOGRAPHY: Global events affecting Indian equity markets

REQUIREMENTS:
- Include specific dates/times
- Include quantitative data (%, numbers, indices)
- Cite sources for each fact
- Assess market impact (which sectors/stocks affected)

AVOID:
- Opinion pieces without data
- Unverified social media claims
- Generic commentary without specifics
"""
    
    def _build_stock_analysis_query(self, user_query: str, time_filter: str) -> str:
        """Build optimized query for stock analysis."""
        
        return f"""
Search for company-specific developments: {user_query}

FOCUS:
1. Latest earnings reports and guidance
2. Corporate actions (M&A, buybacks, dividends)
3. Management changes or controversies
4. Regulatory actions or investigations
5. Analyst upgrades/downgrades with rationale

TIME: {time_filter}
SOURCES: Company filings, Bloomberg, Reuters, ET

REQUIREMENTS:
- Specific numbers (revenue, profit, guidance)
- Source attribution
- Impact on stock price
- Analyst consensus changes
"""
    
    def _build_sector_analysis_query(self, user_query: str, time_filter: str) -> str:
        """Build optimized query for sector analysis."""
        
        return f"""
Search for sector-specific developments: {user_query}

FOCUS:
1. Regulatory changes affecting the sector
2. Industry trends and disruptions
3. Major deals or consolidation
4. Commodity price movements (if relevant)
5. Sector rotation and fund flows

TIME: {time_filter}
SOURCES: Industry reports, Bloomberg, Reuters

REQUIREMENTS:
- Sector-wide impact assessment
- Key players affected
- Quantitative data (growth rates, margins)
- Structural vs cyclical factors
"""
    
    def _build_generic_query(self, user_query: str, time_filter: str) -> str:
        """Build generic optimized query."""
        
        return f"""
Search for: {user_query}

TIME: {time_filter}
SOURCES: Bloomberg, Reuters, Financial Times, Economic Times
FOCUS: Market-relevant information with data

REQUIREMENTS:
- Specific facts with sources
- Quantitative data where available
- Market impact assessment
"""
    
    def add_geopolitical_context(self, base_query: str) -> str:
        """
        Add geopolitical context to query (optional, use sparingly).
        
        Use only for market overview queries during high volatility.
        """
        
        return f"""
{base_query}

GEOPOLITICAL CONTEXT (if relevant):
- US-China trade tensions and tariffs
- Russia-Ukraine conflict and energy markets
- Middle East tensions and oil prices
- US Federal Reserve policy and dollar strength
- India-specific: Border tensions, trade policies, FDI flows

For each geopolitical event:
- Explain market mechanism (how it affects prices)
- Identify affected sectors/stocks
- Assess duration (temporary vs structural)
"""


# Singleton instance
_optimizer: Optional[PerplexityOptimizer] = None


def get_perplexity_optimizer() -> PerplexityOptimizer:
    """Get singleton Perplexity optimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = PerplexityOptimizer()
    return _optimizer
