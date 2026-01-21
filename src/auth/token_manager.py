"""
Token encryption and management utilities for Zerodha OAuth.

Provides AES-256 encryption for secure token storage.
"""

import logging
from typing import Optional
from datetime import datetime
from cryptography.fernet import Fernet
import base64
import hashlib

from src.config import settings

logger = logging.getLogger(__name__)


def _get_encryption_key() -> bytes:
    """
    Get or generate encryption key from settings.
    
    Returns:
        32-byte encryption key for Fernet
    """
    if not hasattr(settings, 'zerodha_encryption_key') or not settings.zerodha_encryption_key:
        raise ValueError(
            "ZERODHA_ENCRYPTION_KEY not set in environment. "
            "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    
    # Ensure key is 32 bytes for Fernet
    key = settings.zerodha_encryption_key.encode() if isinstance(settings.zerodha_encryption_key, str) else settings.zerodha_encryption_key
    
    # Use SHA256 to ensure exactly 32 bytes
    key_hash = hashlib.sha256(key).digest()
    return base64.urlsafe_b64encode(key_hash)


def encrypt_token(token: str) -> str:
    """
    Encrypt access token using AES-256 (Fernet).
    
    Args:
        token: Plain text access token
        
    Returns:
        Encrypted token as base64 string
        
    Example:
        >>> encrypted = encrypt_token("my_access_token_xyz")
        >>> print(encrypted)
        'gAAAAABh...'
    """
    try:
        key = _get_encryption_key()
        cipher = Fernet(key)
        encrypted = cipher.encrypt(token.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Error encrypting token: {e}")
        raise


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt access token.
    
    Args:
        encrypted_token: Encrypted token string
        
    Returns:
        Decrypted plain text token
        
    Raises:
        ValueError: If decryption fails (invalid token or key)
    """
    try:
        key = _get_encryption_key()
        cipher = Fernet(key)
        decrypted = cipher.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error decrypting token: {e}")
        raise ValueError("Failed to decrypt token. Token may be corrupted or encryption key changed.")


def is_token_expired(expires_at: datetime) -> bool:
    """
    Check if token has expired.
    
    Args:
        expires_at: Token expiry datetime (UTC)
        
    Returns:
        True if expired, False otherwise
    """
    return datetime.utcnow() > expires_at


def generate_encryption_key() -> str:
    """
    Generate a new encryption key for development/setup.
    
    Returns:
        Base64-encoded encryption key
        
    Note:
        This is a utility function for initial setup.
        In production, generate once and store in environment variables.
    """
    return Fernet.generate_key().decode()


if __name__ == "__main__":
    # Utility: Generate encryption key
    print("Generated Encryption Key (add to .env as ZERODHA_ENCRYPTION_KEY):")
    print(generate_encryption_key())
