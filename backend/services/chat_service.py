"""
Chat service - Core business logic for chat functionality.
Extracted from app.py to be framework-agnostic.
"""
import asyncio
import logging
from typing import Dict, Any, AsyncGenerator, Optional
from datetime import datetime

from src.graph.graph import get_graph
from src.personal_finance.graph.pf_graph import get_pf_graph
from src.data.conversation_history import get_conversation_history
from src.memory import get_conversation_memory

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat interactions."""
    
    def __init__(self):
        self.conversation_history = get_conversation_history()
        self.conversation_memory = get_conversation_memory()
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        user_mode: str = "pro",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message and return response.
        
        Args:
            message: User message
            session_id: Session identifier
            user_mode: Chat mode ("pro" or "personal")
            metadata: Additional metadata
            
        Returns:
            Response dictionary with content and metadata
        """
        try:
            # Get conversation history
            history_messages = await self.conversation_history.get_history(session_id, limit=5)
            
            # Convert to message format
            message_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in history_messages
            ]
            
            # Store user message
            await self.conversation_history.add_message(
                session_id=session_id,
                role="user",
                content=message
            )
            
            # Store in conversation memory
            await self.conversation_memory.add_message(
                session_id=session_id,
                role="user",
                content=message,
                metadata=metadata or {}
            )
            
            # Create initial state based on mode
            if user_mode == "personal":
                graph = get_pf_graph()
                initial_state = {
                    "query": message,
                    "user_id": session_id,
                    "conversation_history": message_history + [{"role": "user", "content": message}],
                    "pf_intent": "",
                    "intent_confidence": 0.0,
                    "personalization_level": "none",
                    "user_profile": {},
                    "profile_is_empty": True,
                    "missing_fields": [],
                    "needs_questions": False,
                    "questions_to_ask": [],
                    "questions_explanation": None,
                    "waiting_for_user_input": False,
                    "extracted_data": {},
                    "rules_output": None,
                    "response": "",
                    "market_context": None
                }
            else:
                graph = get_graph()
                initial_state = {
                    "query": message,
                    "messages": message_history + [{"role": "user", "content": message}],
                    "session_id": session_id,
                    "last_mentioned_stocks": [],
                    "conversation_history": [],
                    "intent": "",
                    "confidence": 0.0,
                    "stock_symbols": [],
                    "canonical_intent": "",
                    "vector_context": [],
                    "structured_data": {},
                    "news_data": {},
                    "market_data": {},
                    "market_overview_data": {},
                    "sector_data": {},
                    "sector_news": {},
                    "reasoning_steps": [],
                    "response": "",
                    "citations": [],
                    "related_questions": [],
                    "model_used": "",
                    "cache_hit": False,
                    "latency_ms": 0.0,
                    "cost_estimate": 0.0,
                    "error": None
                }
            
            # Execute graph
            config = {"configurable": {"thread_id": "default"}}
            start_time = datetime.now()
            
            final_state = None
            async for event in graph.astream(initial_state, config):
                # Get the last event
                if event:
                    for key in event:
                        final_state = event[key]
            
            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            if final_state:
                response_text = final_state.get("response", "I apologize, but I couldn't generate a response.")
                
                # Store assistant response
                await self.conversation_history.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=response_text,
                    metadata={
                        "intent": str(final_state.get('intent', 'unknown')),
                        "symbols": final_state.get('stock_symbols', []),
                        "latency_ms": latency_ms,
                        "model_used": final_state.get('model_used', 'unknown'),
                        "cost_estimate": final_state.get('cost_estimate', 0)
                    }
                )
                
                # Store in conversation memory
                await self.conversation_memory.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=response_text,
                    metadata={
                        "intent": str(final_state.get('intent', 'unknown')),
                        "stocks": final_state.get('stock_symbols', []),
                    }
                )
                
                return {
                    "response": response_text,
                    "session_id": session_id,
                    "intent": final_state.get("intent"),
                    "symbols": final_state.get("stock_symbols", []),
                    "metadata": {
                        "latency_ms": latency_ms,
                        "model_used": final_state.get("model_used", "unknown"),
                        "cost_estimate": final_state.get("cost_estimate", 0),
                        "cache_hit": final_state.get("cache_hit", False)
                    }
                }
            else:
                raise Exception("No response generated from graph")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            raise
    
    async def stream_message(
        self,
        message: str,
        session_id: str,
        user_mode: str = "pro",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a chat message and stream response chunks.
        
        Args:
            message: User message
            session_id: Session identifier
            user_mode: Chat mode ("pro" or "personal")
            metadata: Additional metadata
            
        Yields:
            Response chunks
        """
        try:
            # Get conversation history
            history_messages = await self.conversation_history.get_history(session_id, limit=5)
            
            # Convert to message format
            message_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in history_messages
            ]
            
            # Store user message
            await self.conversation_history.add_message(
                session_id=session_id,
                role="user",
                content=message
            )
            
            # Store in conversation memory
            await self.conversation_memory.add_message(
                session_id=session_id,
                role="user",
                content=message,
                metadata=metadata or {}
            )
            
            # Yield status update
            yield {
                "type": "status",
                "content": "Processing your query...",
                "metadata": {}
            }
            
            # Create initial state based on mode
            if user_mode == "personal":
                graph = get_pf_graph()
                initial_state = {
                    "query": message,
                    "user_id": session_id,
                    "conversation_history": message_history + [{"role": "user", "content": message}],
                    "pf_intent": "",
                    "response": "",
                }
            else:
                graph = get_graph()
                initial_state = {
                    "query": message,
                    "messages": message_history + [{"role": "user", "content": message}],
                    "session_id": session_id,
                    "intent": "",
                    "response": "",
                }
            
            # Execute graph with streaming
            config = {"configurable": {"thread_id": "default"}}
            start_time = datetime.now()
            
            final_state = None
            async for event in graph.astream(initial_state, config):
                # Yield progress updates
                if "classify_intent" in event:
                    intent = event["classify_intent"].get("intent", "")
                    yield {
                        "type": "status",
                        "content": f"Analyzing: {intent}",
                        "metadata": {"intent": intent}
                    }
                elif "synthesize_response" in event:
                    final_state = event["synthesize_response"]
            
            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            if final_state:
                response_text = final_state.get("response", "I apologize, but I couldn't generate a response.")
                
                # Stream response in chunks
                chunk_size = 50
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i + chunk_size]
                    yield {
                        "type": "chunk",
                        "content": chunk,
                        "metadata": {}
                    }
                    await asyncio.sleep(0.01)  # Small delay for smooth streaming
                
                # Store assistant response
                await self.conversation_history.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=response_text,
                    metadata={
                        "intent": str(final_state.get('intent', 'unknown')),
                        "symbols": final_state.get('stock_symbols', []),
                        "latency_ms": latency_ms,
                    }
                )
                
                # Yield completion
                yield {
                    "type": "complete",
                    "content": "",
                    "metadata": {
                        "latency_ms": latency_ms,
                        "model_used": final_state.get("model_used", "unknown"),
                        "cost_estimate": final_state.get("cost_estimate", 0),
                        "intent": final_state.get("intent"),
                        "symbols": final_state.get("stock_symbols", [])
                    }
                }
            else:
                yield {
                    "type": "error",
                    "content": "No response generated",
                    "metadata": {}
                }
                
        except Exception as e:
            logger.error(f"Error streaming message: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"Error: {str(e)}",
                "metadata": {}
            }
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> list[Dict[str, Any]]:
        """Get conversation history for a session."""
        return await self.conversation_history.get_history(session_id, limit=limit)
    
    async def clear_session(self, session_id: str) -> bool:
        """Clear conversation history for a session."""
        try:
            # Clear from both systems
            await self.conversation_history.clear_history(session_id)
            await self.conversation_memory.clear_session(session_id)
            return True
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            return False


# Singleton instance
_chat_service = None


def get_chat_service() -> ChatService:
    """Get chat service singleton."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
