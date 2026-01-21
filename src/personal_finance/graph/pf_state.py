"""
Personal Finance Graph State

State schema for PF chatbot LangGraph flow.
"""
from typing import TypedDict, Optional, List, Dict, Any


class PFChatState(TypedDict, total=False):
    """
    State for Personal Finance chatbot graph.
    
    Flow:
    query → classify_intent → check_profile → ask_questions (if needed) 
    → run_rules → synthesize_response
    """
    # Input
    query: str
    user_id: str
    conversation_history: List[Dict[str, str]]
    
    # Intent classification
    pf_intent: str  # PF_EDUCATION, PF_EVALUATION, etc.
    intent_confidence: float
    personalization_level: str  # "none", "optional", "required"
    
    # User profile
    user_profile: Dict[str, Any]  # From MongoDB
    profile_is_empty: bool
    missing_fields: List[str]  # Fields needed for this intent
    
    # Question handling
    needs_questions: bool
    questions_to_ask: List[str]
    questions_explanation: Optional[str]
    waiting_for_user_input: bool
    
    # Data extraction
    extracted_data: Dict[str, Any]  # From user's response
    
    # Rules engine
    rules_output: Optional[Dict[str, Any]]  # From PF rules engine
    
    # Response generation
    response: str
    
    # Context (optional)
    market_context: Optional[Dict[str, Any]]  # If PF_MARKET_CONTEXT
