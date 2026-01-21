"""
LangGraph Integration Example.

Shows how to integrate document processing with existing LangGraph nodes.

Add this to src/graph/nodes.py
"""

# Add these imports at the top
from src.workers import enqueue_processing, check_and_upgrade_tier


# Modify fetch_vector_context_node:

async def fetch_vector_context_node(state: ChatState) -> Dict[str, Any]:
    """
    Fetch relevant context from Pinecone vector store.
    
    NEW: Triggers background processing if data not available.
    """
    query = state["query"]
    symbols = state.get("stock_symbols", [])
    
    vector_store = get_vector_store()
    mongo = get_mongo_client()
    
    # NEW: Check processing state and trigger processing if needed
    for symbol in symbols[:1]:  # Process first symbol only
        doc = await mongo.stock_documents.find_one({"symbol": symbol})
        
        if doc:
            processing_state = doc.get("processing_state", {})
            tier = processing_state.get("tier", 0)
            
            # Trigger processing on first query (Tier 0 → Tier 1)
            if tier == 0:
                annual_reports = doc.get("annual_reports", [])
                if annual_reports:
                    latest_report = annual_reports[0]  # Most recent
                    
                    # Get company info
                    general_doc = await mongo.stock_generals.find_one({"symbol": symbol})
                    company_name = general_doc.get("company_name", symbol) if general_doc else symbol
                    isin = general_doc.get("isin", "") if general_doc else ""
                    
                    # Enqueue background processing
                    job_id = enqueue_processing(
                        symbol=symbol,
                        fiscal_year=latest_report["year"],
                        url=latest_report["url"],
                        isin=isin,
                        company_name=company_name,
                        tier=1,  # Start with Tier 1 (TOC extraction)
                        priority="high"  # User-triggered = high priority
                    )
                    
                    logger.info(f"Triggered Tier 1 processing for {symbol} (job: {job_id})")
            
            # Increment query count (for tier upgrade logic)
            await mongo.increment_query_count(symbol)
            
            # Check if tier upgrade is needed
            await check_and_upgrade_tier(symbol)
    
    # Fetch from Pinecone (may be empty for first query)
    if symbols:
        all_docs = []
        for symbol in symbols[:3]:
            docs = await vector_store.search_by_company(query, symbol, top_k=3)
            all_docs.extend(docs)
    else:
        all_docs = await vector_store.search(query, top_k=5)
    
    reasoning = f"Retrieved {len(all_docs)} documents from vector store"
    if len(all_docs) == 0 and symbols:
        reasoning += " (triggered background processing for first-time query)"
    
    return {
        "vector_context": all_docs,
        "reasoning_steps": [reasoning]
    }


# NEW: Add a node to fetch vertical information

async def fetch_vertical_context_node(state: ChatState) -> Dict[str, Any]:
    """
    Fetch vertical/segment information from MongoDB.
    
    Used for vertical analysis queries.
    """
    query = state["query"]
    symbols = state.get("stock_symbols", [])
    
    mongo = get_mongo_client()
    vertical_data = []
    
    for symbol in symbols[:3]:  # Limit to 3 symbols
        # Get latest vertical data
        verticals_doc = await mongo.get_verticals(symbol)
        
        if verticals_doc:
            vertical_data.append({
                "symbol": symbol,
                "fiscal_year": verticals_doc.get("fiscal_year"),
                "verticals": verticals_doc.get("verticals", [])
            })
    
    reasoning = f"Retrieved vertical data for {len(vertical_data)} companies"
    
    return {
        "vertical_context": vertical_data,
        "reasoning_steps": [reasoning]
    }


# Example usage in synthesize_response_node:

async def synthesize_response_node(state: ChatState) -> Dict[str, Any]:
    """
    Synthesize final response using all gathered context.
    
    NEW: Uses vertical context for segment analysis.
    """
    # ... existing code ...
    
    # NEW: Add vertical context if available
    vertical_context = state.get("vertical_context", [])
    
    if vertical_context and intent == QueryIntent.VERTICAL_ANALYSIS:
        # Format vertical data for LLM
        vertical_summary = []
        for company_data in vertical_context:
            symbol = company_data["symbol"]
            verticals = company_data["verticals"]
            
            vertical_summary.append(f"\n{symbol} Business Segments:")
            for v in verticals:
                vertical_summary.append(
                    f"- {v['name']}: ₹{v.get('revenue', 'N/A')} cr "
                    f"({v.get('revenue_percent', 'N/A')}% of total), "
                    f"YoY Growth: {v.get('growth_yoy', 'N/A')}%"
                )
                if v.get('commentary'):
                    vertical_summary.append(f"  {v['commentary']}")
        
        context_parts.append("\n".join(vertical_summary))
    
    # ... rest of existing code ...
