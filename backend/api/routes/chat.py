"""
Chat API routes.
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import logging
import json

from backend.api.models.chat import (
    ChatRequest,
    ChatResponse,
    MessageHistoryResponse,
    MessageHistoryItem
)
from backend.services.chat_service import get_chat_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest) -> ChatResponse:
    """
    Send a message and get a response.
    
    This endpoint processes the message synchronously and returns
    the complete response.
    
    Supports both 'pro' and 'personal' modes via metadata.
    """
    try:
        chat_service = get_chat_service()
        
        # Get user_mode from metadata, default to 'pro'
        user_mode = request.metadata.get("user_mode", "pro")
        
        result = await chat_service.process_message(
            message=request.message,
            session_id=request.session_id,
            user_mode=user_mode,
            metadata=request.metadata
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in send_message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=MessageHistoryResponse)
async def get_history(session_id: str, limit: int = 50) -> MessageHistoryResponse:
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session identifier
        limit: Maximum number of messages to return
    """
    try:
        chat_service = get_chat_service()
        
        history = await chat_service.get_session_history(session_id, limit=limit)
        
        messages = [
            MessageHistoryItem(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("timestamp"),
                metadata=msg.get("metadata", {})
            )
            for msg in history
        ]
        
        return MessageHistoryResponse(
            session_id=session_id,
            messages=messages,
            total_count=len(messages)
        )
        
    except Exception as e:
        logger.error(f"Error in get_history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def clear_session(session_id: str) -> Dict[str, Any]:
    """
    Clear conversation history for a session.
    
    Args:
        session_id: Session identifier
    """
    try:
        chat_service = get_chat_service()
        
        success = await chat_service.clear_session(session_id)
        
        if success:
            return {"success": True, "message": "Session cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear session")
            
    except Exception as e:
        logger.error(f"Error in clear_session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat.
    
    Client sends:
    {
        "type": "message",
        "session_id": "uuid",
        "content": "message text",
        "metadata": {}
    }
    
    Server sends:
    {
        "type": "chunk|status|complete|error",
        "content": "text",
        "metadata": {}
    }
    """
    await websocket.accept()
    
    try:
        chat_service = get_chat_service()
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") != "message":
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid message type",
                    "metadata": {}
                })
                continue
            
            session_id = message_data.get("session_id")
            content = message_data.get("content")
            metadata = message_data.get("metadata", {})
            
            if not session_id or not content:
                await websocket.send_json({
                    "type": "error",
                    "content": "Missing session_id or content",
                    "metadata": {}
                })
                continue
            
            # Get user_mode from metadata, default to 'pro'
            user_mode = metadata.get("user_mode", "pro")
            
            # Stream response
            async for chunk in chat_service.stream_message(
                message=content,
                session_id=session_id,
                user_mode=user_mode,
                metadata=metadata
            ):
                await websocket.send_json(chunk)
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "content": str(e),
                "metadata": {}
            })
        except:
            pass
