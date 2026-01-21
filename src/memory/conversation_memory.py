"""
Conversation Memory for AarthikAI Chatbot.

Provides short-term memory using Redis to remember:
- Last 10 messages in conversation
- Last mentioned stocks
- User intent patterns
- Conversation context for ambiguity resolution

Usage:
    memory = ConversationMemory()
    await memory.add_message(session_id, "user", "Is Zomato expensive?", {"stocks": ["ZOMATO"]})
    context = await memory.get_context(session_id)
    resolved_query = await memory.resolve_ambiguity("What about peers?", context)
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.data.redis_client import get_redis_cache

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Manages conversation memory using Redis.
    
    Features:
    - Stores last 10 messages per session
    - Tracks mentioned stocks
    - Resolves ambiguous queries using context
    - Auto-expires old sessions (1 hour)
    """
    
    def __init__(self):
        self.redis = get_redis_cache()
        self.max_messages = 10
        self.session_ttl = 3600  # 1 hour
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a message to conversation history.
        
        Args:
            session_id: Unique session identifier
            role: "user" or "assistant"
            content: Message content
            metadata: Additional metadata (stocks mentioned, intent, etc.)
        """
        try:
            # Get existing history
            history_key = f"conversation:{session_id}:history"
            history = await self.redis.get(history_key) or []
            
            # Create message object
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Add to history (keep last 10 messages)
            history.append(message)
            if len(history) > self.max_messages:
                history = history[-self.max_messages:]
            
            # Save back to Redis
            await self.redis.set(history_key, history, ttl=self.session_ttl)
            
            # Update last mentioned stocks
            if metadata and "stocks" in metadata:
                await self._update_mentioned_stocks(session_id, metadata["stocks"])
            
            # Update last intent
            if metadata and "intent" in metadata:
                await self._update_last_intent(session_id, metadata["intent"])
            
        except Exception as e:
            logger.error(f"Error adding message to conversation memory: {e}")
    
    async def _update_mentioned_stocks(self, session_id: str, stocks: List[str]):
        """Update list of mentioned stocks (keep last 5)."""
        key = f"conversation:{session_id}:stocks"
        mentioned = await self.redis.get(key) or []
        
        # Add new stocks
        for stock in stocks:
            if stock not in mentioned:
                mentioned.append(stock)
        
        # Keep last 5
        mentioned = mentioned[-5:]
        
        await self.redis.set(key, mentioned, ttl=self.session_ttl)
    
    async def _update_last_intent(self, session_id: str, intent: str):
        """Update last detected intent."""
        key = f"conversation:{session_id}:last_intent"
        await self.redis.set(key, intent, ttl=self.session_ttl)
    
    async def get_context(self, session_id: str, max_messages: int = 10) -> Dict[str, Any]:
        """
        Get conversation context for a session.
        
        Args:
            session_id: Session identifier
            max_messages: Maximum messages to retrieve (default: 10, reduced from 20)
            
        Returns:
            Dict with:
            - last_stocks: List of recently mentioned stocks
            - last_intent: Last detected intent
            - conversation_history: Last N messages
            - last_user_message: Most recent user message
        """
        try:
            # Fetch all context data in parallel
            history_key = f"conversation:{session_id}:history"
            stocks_key = f"conversation:{session_id}:stocks"
            intent_key = f"conversation:{session_id}:last_intent"
            
            history, stocks, last_intent = await asyncio.gather(
                self.redis.get(history_key),
                self.redis.get(stocks_key),
                self.redis.get(intent_key),
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(history, Exception):
                history = []
            if isinstance(stocks, Exception):
                stocks = []
            if isinstance(last_intent, Exception):
                last_intent = None
            
            # Get last user message
            last_user_message = None
            if history:
                for msg in reversed(history):
                    if msg.get("role") == "user":
                        last_user_message = msg.get("content")
                        break
            
            return {
                "last_stocks": stocks or [],
                "last_intent": last_intent,
                "conversation_history": history or [],
                "last_user_message": last_user_message,
                "has_context": bool(history or stocks)
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return {
                "last_stocks": [],
                "last_intent": None,
                "conversation_history": [],
                "last_user_message": None,
                "has_context": False
            }
    
    async def resolve_ambiguity(self, query: str, context: Dict[str, Any]) -> str:
        """
        Resolve ambiguous queries using conversation context.
        
        Examples:
            "What about peers?" → "What about ZOMATO peers?"
            "Compare with competitors" → "Compare INFY with competitors"
            "Is it expensive?" → "Is TCS expensive?"
        
        Args:
            query: User query (potentially ambiguous)
            context: Conversation context from get_context()
            
        Returns:
            Resolved query with explicit stock references
        """
        query_lower = query.lower()
        last_stocks = context.get("last_stocks", [])
        
        # No context available
        if not last_stocks:
            return query
        
        # Ambiguous pronouns and references
        ambiguous_patterns = [
            ("it", "its", "this stock", "the stock", "the company"),
            ("what about", "how about", "tell me about"),
            ("peers", "competitors", "similar companies"),
            ("parent company", "subsidiary", "subsidiaries"),
        ]
        
        # Check if query contains ambiguous references
        is_ambiguous = any(
            pattern in query_lower 
            for pattern_group in ambiguous_patterns 
            for pattern in pattern_group
        )
        
        if not is_ambiguous:
            return query
        
        # Resolve using last mentioned stock
        primary_stock = last_stocks[-1]  # Most recent
        
        # Pattern-based resolution
        if any(word in query_lower for word in ["it", "its", "this stock", "the stock"]):
            # Replace pronouns
            resolved = query.replace("it", primary_stock)
            resolved = resolved.replace("It", primary_stock)
            resolved = resolved.replace("this stock", primary_stock)
            resolved = resolved.replace("the stock", primary_stock)
            resolved = resolved.replace("the company", primary_stock)
            return resolved
        
        elif any(phrase in query_lower for phrase in ["what about", "how about", "tell me about"]):
            # Prepend stock name
            return f"{query} for {primary_stock}"
        
        elif any(word in query_lower for word in ["peers", "competitors"]):
            # Add stock context
            if primary_stock not in query:
                return f"{primary_stock} {query}"
            return query
        
        elif any(word in query_lower for word in ["parent company", "subsidiary"]):
            # Add stock context
            if primary_stock not in query:
                return f"What is {primary_stock}'s {query}"
            return query
        
        else:
            # Generic: prepend stock name if not present
            if not any(stock in query.upper() for stock in last_stocks):
                return f"{query} for {primary_stock}"
            return query
    
    async def clear_session(self, session_id: str):
        """Clear all conversation data for a session."""
        try:
            keys_to_delete = [
                f"conversation:{session_id}:history",
                f"conversation:{session_id}:stocks",
                f"conversation:{session_id}:last_intent"
            ]
            
            for key in keys_to_delete:
                await self.redis.delete(key)
            
            logger.info(f"Cleared conversation memory for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
    
    async def get_stats(self, session_id: str) -> Dict[str, Any]:
        """Get conversation statistics for a session."""
        context = await self.get_context(session_id)
        
        return {
            "total_messages": len(context.get("conversation_history", [])),
            "stocks_mentioned": len(context.get("last_stocks", [])),
            "has_context": context.get("has_context", False),
            "last_intent": context.get("last_intent")
        }


# Singleton instance
_conversation_memory_instance: Optional[ConversationMemory] = None


def get_conversation_memory() -> ConversationMemory:
    """Get singleton conversation memory instance."""
    global _conversation_memory_instance
    if _conversation_memory_instance is None:
        _conversation_memory_instance = ConversationMemory()
    return _conversation_memory_instance
