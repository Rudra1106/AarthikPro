"""
Personal Finance LangGraph Assembly

Creates the PF chatbot state machine with progressive disclosure flow.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import logging

from .pf_state import PFChatState
from .pf_nodes import (
    classify_pf_intent_node,
    check_user_profile_node,
    determine_questions_node,
    run_rules_engine_node,
    synthesize_pf_response_node,
    extract_and_save_profile_data_node
)

logger = logging.getLogger(__name__)


def should_ask_questions(state: PFChatState) -> bool:
    """Determine if we need to ask questions."""
    return state.get("needs_questions", False)


def should_run_rules_engine(state: PFChatState) -> bool:
    """Determine if we need to run rules engine."""
    pf_intent = state.get("pf_intent", "")
    return pf_intent in ["pf_action", "pf_goal_planning"]


def create_pf_graph() -> StateGraph:
    """
    Create the Personal Finance LangGraph state machine.
    
    Flow:
    START → classify_intent → check_profile → determine_questions
    → [if questions needed] → ask questions → END
    → [if no questions] → run_rules (if needed) → synthesize_response → END
    """
    # Initialize graph
    graph = StateGraph(PFChatState)
    
    # Add nodes
    graph.add_node("classify_intent", classify_pf_intent_node)
    graph.add_node("check_profile", check_user_profile_node)
    graph.add_node("determine_questions", determine_questions_node)
    graph.add_node("run_rules", run_rules_engine_node)
    graph.add_node("synthesize_response", synthesize_pf_response_node)
    
    # Add edges
    graph.add_edge(START, "classify_intent")
    graph.add_edge("classify_intent", "check_profile")
    graph.add_edge("check_profile", "determine_questions")
    
    # Conditional: If questions needed, synthesize will return question message
    # Otherwise, run rules (if needed) then synthesize
    graph.add_conditional_edges(
        "determine_questions",
        should_run_rules_engine,
        {
            True: "run_rules",
            False: "synthesize_response"
        }
    )
    
    graph.add_edge("run_rules", "synthesize_response")
    graph.add_edge("synthesize_response", END)
    
    return graph


def compile_pf_graph():
    """
    Compile the PF graph with memory for conversation history.
    
    Returns:
        Compiled graph ready for execution
    """
    graph = create_pf_graph()
    
    # Add memory saver for conversation history
    memory = MemorySaver()
    
    # Compile
    compiled_graph = graph.compile(checkpointer=memory)
    
    logger.info("PF graph compiled successfully")
    
    return compiled_graph


# Create singleton instance
_compiled_pf_graph = None


def get_pf_graph():
    """Get compiled PF graph instance."""
    global _compiled_pf_graph
    if _compiled_pf_graph is None:
        _compiled_pf_graph = compile_pf_graph()
    return _compiled_pf_graph
