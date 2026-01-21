"""
Automated Zerodha token refresh script.

Run this daily at 8 AM before market opens to refresh access token.
Uses refresh token to get new access token without manual login.

Usage:
    python scripts/refresh_zerodha_token.py

Schedule with cron:
    0 8 * * * cd /path/to/AarthikAi && python scripts/refresh_zerodha_token.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kiteconnect import KiteConnect
from dotenv import load_dotenv, set_key
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def refresh_token():
    """
    Refresh Zerodha access token using refresh token.
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    # Load environment variables
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    
    api_key = os.getenv("ZERODHA_API_KEY")
    api_secret = os.getenv("ZERODHA_API_SECRET")
    refresh_token = os.getenv("ZERODHA_REFRESH_TOKEN")
    
    # Validate credentials
    if not api_key:
        logger.error("ZERODHA_API_KEY not found in .env")
        return False
    
    if not api_secret:
        logger.error("ZERODHA_API_SECRET not found in .env")
        return False
    
    if not refresh_token:
        logger.error("ZERODHA_REFRESH_TOKEN not found in .env")
        logger.error("You need to login once via chatbot to get refresh token")
        return False
    
    try:
        # Initialize Kite Connect
        kite = KiteConnect(api_key=api_key)
        
        logger.info("Refreshing Zerodha access token...")
        logger.info(f"Using refresh token: {refresh_token[:20]}...")
        
        # Renew access token
        response = kite.renew_access_token(
            refresh_token=refresh_token,
            api_secret=api_secret
        )
        
        if "access_token" not in response:
            logger.error("No access_token in response")
            logger.error(f"Response: {response}")
            return False
        
        new_access_token = response["access_token"]
        
        # Update .env file
        logger.info("Updating .env file with new access token...")
        set_key(env_path, "ZERODHA_ACCESS_TOKEN", new_access_token)
        
        logger.info("✅ Access token refreshed successfully!")
        logger.info(f"New token: {new_access_token[:20]}...")
        logger.info(f"Token saved to: {env_path}")
        
        # Verify token was saved
        load_dotenv(env_path, override=True)
        saved_token = os.getenv("ZERODHA_ACCESS_TOKEN")
        if saved_token == new_access_token:
            logger.info("✅ Token verified in .env file")
        else:
            logger.warning("⚠️ Token in .env doesn't match (may need app restart)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Token refresh failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Common errors
        if "Invalid refresh_token" in str(e):
            logger.error("Refresh token is invalid or expired (1 year validity)")
            logger.error("Login via chatbot to get new refresh token")
        elif "Invalid api_secret" in str(e):
            logger.error("API secret is incorrect")
            logger.error("Check ZERODHA_API_SECRET in .env")
        
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Zerodha Token Refresh Script")
    logger.info("=" * 60)
    
    success = refresh_token()
    
    if success:
        logger.info("=" * 60)
        logger.info("Token refresh completed successfully!")
        logger.info("Restart your application to use the new token")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("Token refresh failed!")
        logger.error("Check logs above for details")
        logger.error("=" * 60)
        sys.exit(1)
