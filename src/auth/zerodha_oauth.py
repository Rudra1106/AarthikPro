"""
Zerodha OAuth 2.0 authentication flow implementation.

Handles:
- OAuth login initiation
- Callback processing and token exchange
- User connection management
- CSRF protection with state parameter
"""

import logging
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from kiteconnect import KiteConnect

from src.config import settings
from src.auth.token_manager import encrypt_token, decrypt_token, is_token_expired
from src.data.mongo_client import get_mongo_client

logger = logging.getLogger(__name__)


async def initiate_zerodha_login(session_id: str) -> Dict[str, str]:
    """
    Initiate Zerodha OAuth login flow.
    
    Args:
        session_id: User's session ID
        
    Returns:
        Dict with 'login_url' for redirecting user
        
    Example:
        >>> result = await initiate_zerodha_login("user-session-123")
        >>> print(result['login_url'])
        'https://kite.zerodha.com/connect/login?v=3&api_key=xxx&redirect_params=state%3D...'
    """
    try:
        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state temporarily in MongoDB (expires in 5 minutes)
        mongo = get_mongo_client()
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        await mongo.save_oauth_state(
            state=state,
            session_id=session_id,
            expires_at=expires_at
        )
        
        # Build Zerodha login URL with redirect_params
        # Zerodha doesn't echo 'state' by default, so we use redirect_params
        import urllib.parse
        redirect_params = urllib.parse.urlencode({"state": state})
        
        login_url = (
            f"https://kite.zerodha.com/connect/login?"
            f"v=3&"
            f"api_key={settings.zerodha_api_key}&"
            f"redirect_params={redirect_params}"
        )
        
        logger.info(f"Initiated Zerodha login for session {session_id[:8]}... with state {state[:10]}...")
        
        return {
            "login_url": login_url,
            "state": state
        }
        
    except Exception as e:
        logger.error(f"Error initiating Zerodha login: {e}")
        raise


async def handle_zerodha_callback(
    request_token: str,
    state: str
) -> Dict[str, Any]:
    """
    Handle OAuth callback from Zerodha.
    
    Exchanges request_token for access_token and stores encrypted in MongoDB.
    
    Args:
        request_token: Token from Zerodha callback
        state: State parameter for CSRF validation
        
    Returns:
        Dict with connection status and user info
        
    Raises:
        ValueError: If state is invalid or token exchange fails
    """
    try:
        # Verify state and get session_id
        mongo = get_mongo_client()
        session_id = await mongo.verify_oauth_state(state)
        
        if not session_id:
            raise ValueError("Invalid or expired OAuth state")
        
        # Initialize KiteConnect
        kite = KiteConnect(api_key=settings.zerodha_api_key)
        
        # Exchange request_token for access_token
        logger.info(f"Exchanging request_token for access_token (session: {session_id[:8]}...)")
        
        session_data = kite.generate_session(
            request_token=request_token,
            api_secret=settings.zerodha_api_secret
        )
        
        # Extract session info
        access_token = session_data["access_token"]
        user_id = session_data["user_id"]
        user_name = session_data.get("user_name", "")
        email = session_data.get("email", "")
        
        # Encrypt access token
        encrypted_token = encrypt_token(access_token)
        
        # Calculate expiry (24 hours from now)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Save connection to MongoDB
        await mongo.save_zerodha_connection(
            session_id=session_id,
            zerodha_user_id=user_id,
            access_token=encrypted_token,
            expires_at=expires_at,
            user_name=user_name,
            email=email
        )
        
        # Cleanup OAuth state
        await mongo.cleanup_oauth_state(state)
        
        logger.info(f"Successfully connected Zerodha account for session {session_id[:8]}...")
        
        return {
            "success": True,
            "session_id": session_id,
            "zerodha_user_id": user_id,
            "user_name": user_name,
            "email": email,
            "expires_at": expires_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error handling Zerodha callback: {e}")
        raise


async def get_user_zerodha_connection(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user's Zerodha connection details.
    
    Args:
        session_id: User's session ID
        
    Returns:
        Connection details with decrypted access_token, or None if not connected
    """
    try:
        mongo = get_mongo_client()
        connection = await mongo.get_zerodha_connection(session_id)
        
        if not connection:
            return None
        
        # Check if token expired
        if is_token_expired(connection["expires_at"]):
            logger.warning(f"Zerodha token expired for session {session_id[:8]}...")
            return None
        
        # Decrypt access token
        try:
            connection["access_token"] = decrypt_token(connection["access_token"])
        except Exception as e:
            logger.error(f"Failed to decrypt token: {e}")
            return None
        
        return connection
        
    except Exception as e:
        logger.error(f"Error getting Zerodha connection: {e}")
        return None


async def is_zerodha_connected(session_id: str) -> bool:
    """
    Check if user has active Zerodha connection.
    
    Args:
        session_id: User's session ID
        
    Returns:
        True if connected and token valid, False otherwise
    """
    connection = await get_user_zerodha_connection(session_id)
    return connection is not None


async def disconnect_zerodha(session_id: str) -> bool:
    """
    Disconnect user's Zerodha account.
    
    Args:
        session_id: User's session ID
        
    Returns:
        True if disconnected successfully
    """
    try:
        mongo = get_mongo_client()
        await mongo.delete_zerodha_connection(session_id)
        logger.info(f"Disconnected Zerodha for session {session_id[:8]}...")
        return True
    except Exception as e:
        logger.error(f"Error disconnecting Zerodha: {e}")
        return False
