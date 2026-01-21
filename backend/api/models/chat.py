"""
Chat-related Pydantic models.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: str = Field(..., description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is the price of Reliance?",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "metadata": {}
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    
    response: str = Field(..., description="Bot response")
    session_id: str = Field(..., description="Session identifier")
    intent: Optional[str] = Field(None, description="Detected intent")
    symbols: Optional[List[str]] = Field(default_factory=list, description="Detected stock symbols")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "The current price of Reliance Industries is ₹2,450.30",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "intent": "stock_price",
                "symbols": ["RELIANCE"],
                "metadata": {
                    "latency_ms": 1250,
                    "model_used": "gpt-4o-mini",
                    "cost_estimate": 0.0012
                }
            }
        }


class StreamChunk(BaseModel):
    """Streaming response chunk."""
    
    type: str = Field(..., description="Chunk type: 'chunk', 'metadata', 'complete'")
    content: Optional[str] = Field(None, description="Chunk content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Chunk metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "chunk",
                "content": "The current price of Reliance is ₹2,450.30",
                "metadata": {}
            }
        }


class SessionInfo(BaseModel):
    """Session information."""
    
    session_id: str = Field(..., description="Session identifier")
    created_at: datetime = Field(..., description="Session creation time")
    message_count: int = Field(0, description="Number of messages in session")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")


class MessageHistoryItem(BaseModel):
    """Single message in conversation history."""
    
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Message metadata")


class MessageHistoryResponse(BaseModel):
    """Response model for message history."""
    
    session_id: str = Field(..., description="Session identifier")
    messages: List[MessageHistoryItem] = Field(..., description="List of messages")
    total_count: int = Field(..., description="Total message count")
