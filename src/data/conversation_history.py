"""
MongoDB conversation history manager.

Stores and retrieves conversation history for multi-turn conversations.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from src.config import settings

logger = logging.getLogger(__name__)


class ConversationHistory:
    """
    Manages conversation history in MongoDB.
    
    Features:
    - Store messages with metadata
    - Retrieve conversation history
    - Session management
    - Automatic timestamps
    """
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.conversations = None
        self._connected = False
    
    async def _ensure_connected(self):
        """Ensure MongoDB connection is established."""
        if self.client is None:
            try:
                self.client = AsyncIOMotorClient(settings.mongodb_uri)
                self.db = self.client[settings.mongodb_conversations_database]
                self.conversations = self.db.conversations
                
                # Test connection
                await self.client.admin.command('ping')
                self._connected = True
                logger.info("MongoDB connection established for conversation history")
            except Exception as e:
                logger.warning(f"MongoDB connection failed: {e}. Conversation history disabled.")
                self._connected = False
    
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
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (intent, symbols, latency, etc.)
        """
        if not self._connected:
            await self._ensure_connected()
        
        if not self._connected:
            return
        
        try:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            # Upsert conversation document
            await self.conversations.update_one(
                {"session_id": session_id},
                {
                    "$push": {"messages": message},
                    "$set": {"updated_at": datetime.utcnow()},
                    "$setOnInsert": {
                        "session_id": session_id,
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.debug(f"Added {role} message to session {session_id}")
            
        except Exception as e:
            logger.error(f"Error adding message to conversation history: {e}")
    
    async def get_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of messages (most recent first)
        """
        if not self._connected:
            await self._ensure_connected()
        
        if not self._connected:
            return []
        
        try:
            conversation = await self.conversations.find_one(
                {"session_id": session_id}
            )
            
            if conversation and "messages" in conversation:
                # Return last N messages
                messages = conversation["messages"][-limit:]
                return messages
            
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    async def get_context_string(
        self,
        session_id: str,
        max_messages: int = 5
    ) -> str:
        """
        Get conversation history as formatted string for LLM context.
        
        Args:
            session_id: Session identifier
            max_messages: Maximum messages to include
            
        Returns:
            Formatted conversation history
        """
        messages = await self.get_history(session_id, limit=max_messages)
        
        if not messages:
            return ""
        
        context_parts = ["Previous conversation:"]
        for msg in messages:
            role = msg["role"].capitalize()
            content = msg["content"][:200]  # Truncate long messages
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    async def clear_session(self, session_id: str):
        """Clear conversation history for a session."""
        if not self._connected:
            return
        
        try:
            await self.conversations.delete_one({"session_id": session_id})
            logger.info(f"Cleared conversation history for session {session_id}")
        except Exception as e:
            logger.error(f"Error clearing conversation history: {e}")
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a conversation session."""
        if not self._connected:
            return {}
        
        try:
            conversation = await self.conversations.find_one(
                {"session_id": session_id}
            )
            
            if conversation:
                messages = conversation.get("messages", [])
                return {
                    "message_count": len(messages),
                    "created_at": conversation.get("created_at"),
                    "updated_at": conversation.get("updated_at"),
                    "user_messages": sum(1 for m in messages if m["role"] == "user"),
                    "assistant_messages": sum(1 for m in messages if m["role"] == "assistant")
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {}


# Singleton instance
_conversation_history_instance: Optional[ConversationHistory] = None


def get_conversation_history() -> ConversationHistory:
    """Get singleton conversation history instance."""
    global _conversation_history_instance
    if _conversation_history_instance is None:
        _conversation_history_instance = ConversationHistory()
    return _conversation_history_instance
