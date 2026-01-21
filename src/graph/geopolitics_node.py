"""
Geopolitics data fetching node - Fetch geopolitical intelligence.

Handles:
- GEO_NEWS: General geopolitics news
- SANCTIONS_STATUS: Sanctions information
- MARKET_IMPACT: Market reaction analysis
- INDIA_IMPACT: India-specific impact
"""

async def fetch_geopolitics_node(state: ChatState) -> Dict[str, Any]:
    """
    Fetch geopolitical intelligence from Perplexity and Indian API.
    
    Triggered for geopolitics intents:
    - GEO_NEWS
    - SANCTIONS_STATUS
    - MARKET_IMPACT
    - INDIA_IMPACT
    
    Returns:
        Updated state with geopolitics_data and india_impact
    """
    from src.data.perplexity_client import get_perplexity_client
    from src.data.indian_api_client import get_indian_api_client
    from src.intelligence.geopolitics_query_builder import get_geopolitics_query_builder
    from src.intelligence.india_impact_mapper import get_india_impact_mapper
    
    query = state.get("query", "")
    intent = state.get("intent")
    
    # Map legacy intent to geopolitics intent
    geo_intent = None
    if intent and hasattr(intent, 'value'):
        intent_value = intent.value
        if intent_value in ["geo_news", "sanctions_status", "market_impact", "india_impact"]:
            geo_intent = intent_value
    
    if not geo_intent:
        logger.info("Not a geopolitics query, skipping geopolitics node")
        return {}
    
    logger.info(f"Fetching geopolitics data for intent: {geo_intent}")
    
    # Initialize clients
    perplexity = get_perplexity_client()
    indian_api = get_indian_api_client()
    query_builder = get_geopolitics_query_builder()
    impact_mapper = get_india_impact_mapper()
    
    # Build optimized query
    optimized_query, metadata = query_builder.build_query(query, geo_intent)
    
    logger.info(f"Optimized query: {optimized_query}")
    logger.info(f"Entities: {metadata['entities']}")
    
    # Fetch data from Perplexity
    perplexity_data = {}
    try:
        # Use appropriate recency filter
        recency_filter = "week" if metadata["recency_days"] <= 7 else "month"
        
        perplexity_data = await perplexity.search_news(
            optimized_query,
            recency_filter=recency_filter,
            max_results=5
        )
        
        logger.info(f"Fetched Perplexity data: {len(perplexity_data.get('answer', ''))} chars")
    except Exception as e:
        logger.error(f"Error fetching Perplexity data: {e}")
        perplexity_data = {"error": str(e)}
    
    # Fetch Indian API news if India-related
    indian_news = []
    if geo_intent == "india_impact" or "India" in metadata["entities"].get("countries", []):
        try:
            indian_news = await indian_api.get_market_news(limit=10)
            logger.info(f"Fetched {len(indian_news)} Indian news items")
        except Exception as e:
            logger.error(f"Error fetching Indian API news: {e}")
    
    # Calculate India impact
    india_impact = None
    if geo_intent in ["india_impact", "market_impact", "sanctions_status"]:
        try:
            india_impact = impact_mapper.get_impact(query, metadata["entities"])
            logger.info(f"India impact calculated: {india_impact.get('strength', 'N/A')}")
        except Exception as e:
            logger.error(f"Error calculating India impact: {e}")
    
    return {
        "geopolitics_data": perplexity_data,
        "indian_api_news": indian_news,
        "india_impact": india_impact,
        "geopolitics_metadata": metadata,
        "reasoning_steps": [
            f"Fetched geopolitics data for intent: {geo_intent}",
            f"Optimized query: {optimized_query}",
            f"Entities: {metadata['entities']}"
        ]
    }
