"""
Additional node for semantic cache checking.
Add this to src/graph/nodes.py after classify_intent_node.
"""

async def check_semantic_cache_node(state: ChatState) -> Dict[str, Any]:
    """
    Check semantic cache for similar queries.
    
    NEW: Phase 1 optimization - check if we have a cached response
    for semantically similar queries to reduce latency and cost.
    
    Returns cached response if found, otherwise returns empty dict.
    """
    query = state["query"]
    intent = state.get("intent", "")
    
    # Skip cache for greetings (already hardcoded)
    if state.get("is_greeting", False):
        return {"cache_hit": False}
    
    # Get intent string for cache key
    intent_str = intent.value if hasattr(intent, 'value') else str(intent)
    
    cache = get_semantic_cache()
    
    try:
        cached_result = await cache.get(query, intent=intent_str)
        
        if cached_result:
            logger.info(f"✅ Semantic cache HIT for query: {query[:50]}...")
            return {
                "cache_hit": True,
                "response": cached_result.get("response", ""),
                "citations": cached_result.get("citations", []),
                "model_used": cached_result.get("model_used", "cached"),
                "reasoning_steps": ["Retrieved from semantic cache (no LLM call needed)"]
            }
        else:
            logger.debug(f"Semantic cache MISS for query: {query[:50]}...")
            return {"cache_hit": False}
    
    except Exception as e:
        logger.error(f"Error checking semantic cache: {e}")
        return {"cache_hit": False}
