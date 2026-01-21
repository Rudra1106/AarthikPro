"""
Authentication API routes.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from backend.api.models.auth import (
    ZerodhaAuthRequest,
    ZerodhaAuthResponse,
    AuthStatus,
    DisconnectRequest,
    DisconnectResponse
)
from src.auth.zerodha_oauth import (
    initiate_zerodha_login,
    is_zerodha_connected,
    disconnect_zerodha
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/zerodha/initiate", response_model=ZerodhaAuthResponse)
async def initiate_zerodha(request: ZerodhaAuthRequest) -> ZerodhaAuthResponse:
    """
    Initiate Zerodha OAuth flow.
    
    Returns a login URL that the client should redirect to.
    """
    try:
        result = await initiate_zerodha_login(request.session_id)
        
        # Extract login URL from result
        if isinstance(result, dict):
            login_url = result.get('login_url', '')
        else:
            login_url = result
        
        return ZerodhaAuthResponse(
            login_url=login_url,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error initiating Zerodha OAuth: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/zerodha/status/{session_id}", response_model=AuthStatus)
async def get_zerodha_status(session_id: str) -> AuthStatus:
    """
    Check Zerodha connection status for a session.
    """
    try:
        connected = await is_zerodha_connected(session_id)
        
        return AuthStatus(
            connected=connected,
            session_id=session_id,
            user_id=None,  # TODO: Get from stored credentials
            connected_at=None  # TODO: Get from stored credentials
        )
        
    except Exception as e:
        logger.error(f"Error checking Zerodha status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/zerodha/disconnect", response_model=DisconnectResponse)
async def disconnect_zerodha_account(request: DisconnectRequest) -> DisconnectResponse:
    """
    Disconnect Zerodha account for a session.
    """
    try:
        success = await disconnect_zerodha(request.session_id)
        
        if success:
            return DisconnectResponse(
                success=True,
                message="Zerodha account disconnected successfully"
            )
        else:
            return DisconnectResponse(
                success=False,
                message="Failed to disconnect Zerodha account"
            )
            
    except Exception as e:
        logger.error(f"Error disconnecting Zerodha: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/zerodha/callback")
async def zerodha_callback(
    request_token: str,
    state: str
) -> Dict[str, Any]:
    """
    OAuth callback endpoint for Zerodha.
    
    This is called by Zerodha after user authorizes the app.
    """
    try:
        # TODO: Implement callback handling
        # This should:
        # 1. Exchange request_token for access_token
        # 2. Store credentials in MongoDB
        # 3. Return success response or redirect
        
        return {
            "success": True,
            "message": "Zerodha connected successfully",
            "redirect_url": "/"  # Redirect to frontend
        }
        
    except Exception as e:
        logger.error(f"Error in Zerodha callback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
