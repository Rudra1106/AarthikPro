"""
State schema for LangGraph state machine.
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph.message import add_messages
import operator


class ChatState(TypedDict):
    """
    State schema for the financial intelligence chatbot.
    
    This state is passed through all nodes in the LangGraph state machine.
    """
    # User input
    query: str
    messages: Annotated[List[Dict[str, str]], add_messages]
    
    # Conversation Memory (Phase 1)
    session_id: str  # Unique session identifier
    last_mentioned_stocks: List[str]  # Recently mentioned stocks for context
    conversation_history: List[Dict[str, Any]]  # Last N messages
    
    # Intent classification
    intent: str
    confidence: float
    stock_symbols: List[str]
    canonical_intent: str  # Canonical intent from blueprint system
    
    # Data retrieval - can be updated by multiple parallel nodes
    vector_context: Annotated[List[Dict[str, Any]], operator.add]
    structured_data: Dict[str, Any]
    news_data: Dict[str, Any]
    market_data: Dict[str, Any]
    market_overview_data: Dict[str, Any]  # Web search results for market overview
    
    # Sector data (for sector performance queries)
    sector_data: Dict[str, Any]  # From get_sector_performance() - Zerodha sectoral indices
    sector_news: Dict[str, Any]  # From Perplexity - current sector context
    
    # Portfolio data (for user's Zerodha portfolio)
    portfolio_data: Optional[Dict[str, Any]]  # Raw portfolio data from Zerodha
    portfolio_context: Optional[str]  # Formatted portfolio string for LLM
    
    # Response generation
    reasoning_steps: Annotated[List[str], operator.add]  # Multiple nodes add reasoning
    response: str
    citations: Annotated[List[str], operator.add]  # Multiple nodes can add citations
    related_questions: List[str]  # Clickable suggested follow-up questions
    
    # Metadata
    model_used: str
    cache_hit: bool
    latency_ms: float
    cost_estimate: float
    
    # Error handling
    error: Optional[str]

