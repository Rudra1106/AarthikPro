"""
LangGraph state machine assembly.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.graph.state import ChatState
from src.graph.nodes import (
    classify_intent_node,
    fetch_vector_context_node,
    fetch_structured_data_node,
    fetch_news_node,
    fetch_market_data_node,
    fetch_portfolio_data_node,  # NEW: For portfolio queries
    fetch_market_overview_node,
    fetch_sector_data_node,  # NEW: For sector performance queries
    synthesize_response_node
)
from src.intent_classifier import QueryIntent


def should_fetch_vector_context(state: ChatState) -> bool:
    """Determine if we should fetch vector context."""
    intent = state.get("intent", "")
    return intent in [QueryIntent.FUNDAMENTAL, QueryIntent.MULTI, QueryIntent.GENERAL]


def should_fetch_structured_data(state: ChatState) -> bool:
    """
    Determine if we should fetch structured data from MongoDB.
    
    Fetches for ANY query with stock symbols (except simple price queries).
    This ensures comparison queries, fundamental analysis, and comprehensive
    queries all get the data they need.
    """
    symbols = state.get("stock_symbols", [])
    intent = state.get("intent", "")
    canonical = state.get("canonical_intent", "")
    
    # No symbols = no structured data needed
    if not symbols:
        return False
    
    # Skip for simple price queries (market data from Dhan is enough)
    # These are queries like "What is TCS price?" or "Current price of Infosys"
    if intent == QueryIntent.MARKET_DATA and canonical == "price_action":
        return False
    
    # Fetch for everything else with symbols
    # This includes: FUNDAMENTAL, TECHNICAL, MULTI, comparisons, general queries
    return True


def should_fetch_news(state: ChatState) -> bool:
    """
    Determine if we should fetch news from Perplexity/Indian API.
    
    Triggers for:
    - NEWS queries (breaking news, latest updates)
    - MULTI queries (comprehensive analysis)
    - FUNDAMENTAL queries (for recent context)
    - STOCK_OVERVIEW canonical intent (comprehensive stock analysis)
    - STOCK_DEEP_DIVE canonical intent (detailed analysis)
    
    Optimized for low latency:
    - Parallel execution with other data sources
    - 5-second timeout on Perplexity calls
    - Cached results (6-hour TTL)
    """
    intent = state.get("intent", "")
    canonical = state.get("canonical_intent", "")
    
    # Trigger for NEWS and MULTI (original logic)
    if intent in [QueryIntent.NEWS, QueryIntent.MULTI]:
        return True
    
    # NEW: Also trigger for FUNDAMENTAL analysis (adds recent context)
    if intent == QueryIntent.FUNDAMENTAL:
        return True
    
    # NEW: Trigger for comprehensive canonical intents
    comprehensive_intents = [
        "stock_overview",      # General stock analysis
        "stock_deep_dive",     # Detailed analysis
        "news_analysis",       # News-focused queries
        "risk_analysis"        # Risk assessment (needs recent events)
    ]
    
    if canonical in comprehensive_intents:
        return True
    
    return False


def should_fetch_market_data(state: ChatState) -> bool:
    """
    Determine if we should fetch live market data from Zerodha.
    
    Always fetch when stock symbols are detected to enrich responses
    with current price context, regardless of intent.
    """
    symbols = state.get("stock_symbols", [])
    return bool(symbols)  # Always fetch for ANY query with stock symbols


def should_fetch_market_overview(state: ChatState) -> bool:
    """
    Determine if query is asking for comprehensive market overview.
    
    Triggers enhanced analytics for Nifty, Sensex, FII/DII, etc.
    """
    query = state.get("query", "").lower()
    
    # Market overview keywords
    overview_keywords = [
        "market overview",
        "market summary", 
        "how is the market",
        "market today",
        "market update",
        "nifty sensex",
        "current market",
        "market status",
        "market situation",
        # Nifty-specific queries
        "nifty 50 performance",
        "nifty performance",
        "analyse nifty",
        "analyze nifty",
        "nifty 50 analysis",
        "nifty analysis",
        "how is nifty",
        "nifty today",
        "nifty 50 today"
    ]
    
    return any(keyword in query for keyword in overview_keywords)


def should_fetch_sector_data(state: ChatState) -> bool:
    """
    Determine if we should fetch sector performance data.
    
    Triggers for:
    - SECTOR_PERFORMANCE intent
    - sector_rotation or sector_overview canonical intents
    - Time-sensitive sector queries ("this year", "2025", "growing", etc.)
    """
    intent = state.get("intent", "")
    canonical = state.get("canonical_intent", "")
    query = state.get("query", "").lower()
    
    # Trigger for sector-related intents
    if intent == QueryIntent.SECTOR_PERFORMANCE:
        return True
    if canonical in ["sector_overview", "sector_rotation"]:
        return True
    
    # Time-sensitive sector keywords
    time_keywords = ["this year", "2025", "this quarter", "currently", "now", "latest", "best sector", "top sector", "growing sector", "performing sector"]
    sector_keywords = ["sector", "sectors", "industry", "industries"]
    
    has_time = any(kw in query for kw in time_keywords)
    has_sector = any(kw in query for kw in sector_keywords)
    
    # Also trigger for general sector questions without time keywords
    sector_question_patterns = [
        "which sector",
        "what sector",
        "best performing",
        "top performing",
        "sector rotation",
        "sector performance"
    ]
    has_sector_question = any(pattern in query for pattern in sector_question_patterns)
    
    return (has_time and has_sector) or has_sector_question


def should_fetch_portfolio_data(state: ChatState) -> bool:
    """
    Determine if we should fetch user's portfolio data.
    
    Triggers for:
    - PORTFOLIO intent (legacy)
    - Queries about user's holdings, stocks, investments
    """
    # IMPORTANT: Use legacy intent because canonical mapper doesn't have portfolio intent
    intent = state.get("intent", "")
    
    # Always fetch for PORTFOLIO intent
    if intent == QueryIntent.PORTFOLIO:
        return True
    
    # Also check query for portfolio keywords as fallback
    query = state.get("query", "").lower()
    portfolio_keywords = [
        "my portfolio",
        "my holdings",
        "my stocks",
        "my investments",
        "what do i own",
        "stocks do i own",
        "stocks in my portfolio",
        "list me all",
        "show me my",
        "portfolio performance",
        "my profit",
        "my loss"
    ]
    
    return any(keyword in query for keyword in portfolio_keywords)


def create_graph() -> StateGraph:
    """
    Create the LangGraph state machine.
    
    Flow:
    START → classify_intent → [parallel data fetching] → synthesize_response → END
    """
    # Initialize graph
    graph = StateGraph(ChatState)
    
    # Add nodes
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("fetch_vector_context", fetch_vector_context_node)
    graph.add_node("fetch_structured_data", fetch_structured_data_node)
    graph.add_node("fetch_news", fetch_news_node)
    graph.add_node("fetch_market_data", fetch_market_data_node)
    graph.add_node("fetch_portfolio_data", fetch_portfolio_data_node)  # NEW
    graph.add_node("fetch_market_overview", fetch_market_overview_node)
    graph.add_node("fetch_sector_data", fetch_sector_data_node)  # NEW
    graph.add_node("synthesize_response", synthesize_response_node)
    
    # Add edges
    graph.add_edge(START, "classify_intent")
    
    # Conditional routing after classification - parallel execution
    # Each data source is conditionally fetched based on intent
    graph.add_conditional_edges(
        "classify_intent",
        should_fetch_vector_context,
        {
            True: "fetch_vector_context",
            False: "synthesize_response"
        }
    )
    
    graph.add_conditional_edges(
        "classify_intent",
        should_fetch_structured_data,
        {
            True: "fetch_structured_data",
            False: "synthesize_response"
        }
    )
    
    graph.add_conditional_edges(
        "classify_intent",
        should_fetch_news,
        {
            True: "fetch_news",
            False: "synthesize_response"
        }
    )
    
    graph.add_conditional_edges(
        "classify_intent",
        should_fetch_market_data,
        {
            True: "fetch_market_data",
            False: "synthesize_response"
        }
    )
    
    graph.add_conditional_edges(
        "classify_intent",
        should_fetch_market_overview,
        {
            True: "fetch_market_overview",
            False: "synthesize_response"
        }
    )
    
    # NEW: Sector data fetching for sector performance queries
    graph.add_conditional_edges(
        "classify_intent",
        should_fetch_sector_data,
        {
            True: "fetch_sector_data",
            False: "synthesize_response"
        }
    )
    
    # NEW: Portfolio data fetching for portfolio queries
    graph.add_conditional_edges(
        "classify_intent",
        should_fetch_portfolio_data,
        {
            True: "fetch_portfolio_data",
            False: "synthesize_response"
        }
    )
    
    # All data fetching nodes lead to synthesis
    graph.add_edge("fetch_vector_context", "synthesize_response")
    graph.add_edge("fetch_structured_data", "synthesize_response")
    graph.add_edge("fetch_news", "synthesize_response")
    graph.add_edge("fetch_market_data", "synthesize_response")
    graph.add_edge("fetch_portfolio_data", "synthesize_response")  # NEW
    graph.add_edge("fetch_market_overview", "synthesize_response")
    graph.add_edge("fetch_sector_data", "synthesize_response")  # NEW
    
    # Synthesis leads to end
    graph.add_edge("synthesize_response", END)
    
    return graph


def compile_graph():
    """
    Compile the graph with memory for conversation history.
    
    Returns:
        Compiled graph ready for execution
    """
    graph = create_graph()
    
    # Add memory saver for conversation history
    memory = MemorySaver()
    
    # Compile
    compiled_graph = graph.compile(checkpointer=memory)
    
    return compiled_graph


# Create singleton instance
_compiled_graph = None


def get_graph():
    """Get compiled graph instance."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = compile_graph()
    return _compiled_graph
