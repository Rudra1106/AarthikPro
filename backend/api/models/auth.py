"""
Authentication-related Pydantic models.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ZerodhaAuthRequest(BaseModel):
    """Request to initiate Zerodha OAuth."""
    
    session_id: str = Field(..., description="Session identifier")


class ZerodhaAuthResponse(BaseModel):
    """Response from Zerodha OAuth initiation."""
    
    login_url: str = Field(..., description="Zerodha login URL")
    session_id: str = Field(..., description="Session identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "login_url": "https://kite.zerodha.com/connect/login?api_key=...",
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class AuthStatus(BaseModel):
    """Zerodha authentication status."""
    
    connected: bool = Field(..., description="Whether Zerodha is connected")
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(None, description="Zerodha user ID if connected")
    connected_at: Optional[datetime] = Field(None, description="Connection timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "connected": True,
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "AB1234",
                "connected_at": "2026-01-19T23:00:00Z"
            }
        }


class DisconnectRequest(BaseModel):
    """Request to disconnect Zerodha."""
    
    session_id: str = Field(..., description="Session identifier")


class DisconnectResponse(BaseModel):
    """Response from disconnect request."""
    
    success: bool = Field(..., description="Whether disconnect was successful")
    message: str = Field(..., description="Status message")
