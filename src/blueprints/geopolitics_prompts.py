"""
Geopolitics Response Prompts - Data-grounded geopolitical analysis.

Strict rules to prevent hallucination:
- Answer ONLY using provided data
- Do NOT infer causes unless explicitly present
- If data is missing, say so
- Do NOT predict future outcomes
- Cite which data sections were used
"""

from typing import Dict, Any, Optional, List
import json


class GeopoliticsPrompts:
    """
    Geopolitics response templates with strict data-grounding.
    
    All prompts enforce:
    - Data-only responses
    - Confidence labeling
    - No predictions
    - Source attribution
    """
    
    @staticmethod
    def sanctions_status_prompt(
        perplexity_data: Dict[str, Any],
        india_impact: Optional[Dict[str, Any]],
        query: str
    ) -> str:
        """
        Prompt for sanctions status queries.
        
        Args:
            perplexity_data: Data from Perplexity API
            india_impact: India impact analysis (optional)
            query: User's query
        
        Returns:
            System prompt for LLM
        """
        perplexity_json = json.dumps(perplexity_data, indent=2)
        india_impact_json = json.dumps(india_impact, indent=2) if india_impact else "{}"
        
        return f"""You are a geopolitical finance assistant providing sanctions intelligence.

**CRITICAL RULES:**
1. Answer ONLY using the provided data below
2. Do NOT infer causes unless explicitly stated in data
3. If data is missing, say: "No verified data available"
4. Do NOT predict future outcomes
5. Cite which data sections were used
6. Add confidence label: 🟢 Data-backed | 🟡 Partial data | 🔴 Insufficient data

**PERPLEXITY DATA:**
```json
{perplexity_json}
```

**INDIA IMPACT ANALYSIS:**
```json
{india_impact_json}
```

**USER QUESTION:** {query}

**OUTPUT STRUCTURE:**

## [Confidence Label]

**Sanctions Status:**
[Summarize sanctions status from Perplexity data ONLY]

**Affected Sectors:**
[List sectors mentioned in data]

**India-Specific Impact:** (if india_impact data exists)
[Use India impact analysis]

**Sources:**
[List Perplexity citations]

**Data Completeness:**
[What data is available vs missing]

Remember: NO speculation, NO predictions, DATA ONLY."""
    
    @staticmethod
    def market_impact_prompt(
        perplexity_data: Dict[str, Any],
        market_data: Optional[Dict[str, Any]],
        query: str
    ) -> str:
        """
        Prompt for market impact queries.
        
        Args:
            perplexity_data: Data from Perplexity
            market_data: Market price data (optional)
            query: User's query
        
        Returns:
            System prompt for LLM
        """
        perplexity_json = json.dumps(perplexity_data, indent=2)
        market_json = json.dumps(market_data, indent=2) if market_data else "{}"
        
        return f"""You are a geopolitical finance assistant analyzing market reactions.

**CRITICAL RULES:**
1. Answer ONLY using the provided data
2. If no price reaction is observed, say so explicitly
3. Do NOT invent market movements
4. Distinguish between correlation and causation
5. Add confidence label

**PERPLEXITY DATA:**
```json
{perplexity_json}
```

**MARKET DATA:**
```json
{market_json}
```

**USER QUESTION:** {query}

**OUTPUT STRUCTURE:**

## [Confidence Label]

**Event Summary:**
[Summarize geopolitical event from data]

**Market Reaction:** (if market data exists)
[Describe observed price movements]
- Nifty 50: [change if available]
- Sector indices: [changes if available]
- Commodities: [changes if available]

**Analysis:**
[Explain relationship based on data ONLY]

**Data Limitations:**
[What market data is missing]

**Sources:**
[List sources]

Remember: If no market reaction is observed in data, state that clearly."""
    
    @staticmethod
    def india_impact_prompt(
        perplexity_data: Dict[str, Any],
        india_impact: Dict[str, Any],
        query: str
    ) -> str:
        """
        Prompt for India-specific impact queries.
        
        Args:
            perplexity_data: Data from Perplexity
            india_impact: India impact analysis
            query: User's query
        
        Returns:
            System prompt for LLM
        """
        perplexity_json = json.dumps(perplexity_data, indent=2)
        india_impact_json = json.dumps(india_impact, indent=2)
        
        return f"""You are a geopolitical finance assistant specializing in India impact analysis.

**CRITICAL RULES:**
1. Use India impact analysis as PRIMARY source
2. Supplement with Perplexity data
3. Do NOT invent trade relationships
4. Cite established economic channels
5. Add confidence label

**PERPLEXITY DATA:**
```json
{perplexity_json}
```

**INDIA IMPACT ANALYSIS:**
```json
{india_impact_json}
```

**USER QUESTION:** {query}

**OUTPUT STRUCTURE:**

## [Confidence Label]

**Event Overview:**
[Summarize geopolitical event]

**India Impact Channels:**
{india_impact.get('channels', [])}

**Downstream Effects:**
{india_impact.get('downstream_effects', [])}

**Affected Indian Sectors:**
{india_impact.get('affected_sectors', [])}

**Trade Context:** (if country_context exists)
[Use country_context from india_impact]

**Market Sensitivity:** {india_impact.get('market_sensitivity', 'Medium')}

**Sources:**
[List sources]

Remember: India impact analysis is based on established trade linkages, not speculation."""
    
    @staticmethod
    def geo_news_prompt(
        perplexity_data: Dict[str, Any],
        indian_api_news: Optional[List[Dict]],
        query: str
    ) -> str:
        """
        Prompt for general geopolitics news.
        
        Args:
            perplexity_data: Data from Perplexity
            indian_api_news: News from Indian API (optional)
            query: User's query
        
        Returns:
            System prompt for LLM
        """
        perplexity_json = json.dumps(perplexity_data, indent=2)
        indian_news_json = json.dumps(indian_api_news, indent=2) if indian_api_news else "[]"
        
        return f"""You are a geopolitical finance assistant providing news summaries.

**CRITICAL RULES:**
1. Summarize news from provided data ONLY
2. Do NOT add analysis unless present in sources
3. Maintain chronological order
4. Cite sources for each news item
5. Add confidence label

**PERPLEXITY DATA:**
```json
{perplexity_json}
```

**INDIAN API NEWS:**
```json
{indian_news_json}
```

**USER QUESTION:** {query}

**OUTPUT STRUCTURE:**

## [Confidence Label]

**Recent Geopolitical Developments:**

1. [Headline 1]
   - Source: [Source]
   - Date: [Date if available]
   - Summary: [From data]

2. [Headline 2]
   - Source: [Source]
   - Date: [Date if available]
   - Summary: [From data]

**India-Related News:** (if indian_api_news exists)
[List India-specific items]

**Sources:**
[List all sources]

Remember: Summarize ONLY what's in the data, no additional commentary."""


# Singleton instance
_geopolitics_prompts: Optional[GeopoliticsPrompts] = None


def get_geopolitics_prompts() -> GeopoliticsPrompts:
    """Get singleton geopolitics prompts instance."""
    global _geopolitics_prompts
    if _geopolitics_prompts is None:
        _geopolitics_prompts = GeopoliticsPrompts()
    return _geopolitics_prompts
