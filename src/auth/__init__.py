"""
Authentication module for Zerodha OAuth integration.

Provides secure OAuth 2.0 authentication flow for Zerodha Kite Connect.
"""

from src.auth.zerodha_oauth import (
    initiate_zerodha_login,
    handle_zerodha_callback,
    get_user_zerodha_connection,
    disconnect_zerodha,
    is_zerodha_connected
)

from src.auth.token_manager import (
    encrypt_token,
    decrypt_token,
    is_token_expired
)

__all__ = [
    "initiate_zerodha_login",
    "handle_zerodha_callback",
    "get_user_zerodha_connection",
    "disconnect_zerodha",
    "is_zerodha_connected",
    "encrypt_token",
    "decrypt_token",
    "is_token_expired"
]
