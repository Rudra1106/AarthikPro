"""
Simple script to get Zerodha tokens and save to .env file.

This is a standalone script that handles the complete OAuth flow
and saves tokens directly to .env file for use by background services.

Usage:
    python scripts/get_zerodha_tokens_simple.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kiteconnect import KiteConnect
from dotenv import load_dotenv, set_key
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_tokens_interactive():
    """Get Zerodha tokens interactively."""
    
    # Load environment
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    
    api_key = os.getenv("ZERODHA_API_KEY")
    api_secret = os.getenv("ZERODHA_API_SECRET")
    
    if not api_key or not api_secret:
        logger.error("ZERODHA_API_KEY and ZERODHA_API_SECRET must be set in .env")
        return False
    
    # Initialize Kite
    kite = KiteConnect(api_key=api_key)
    
    # Generate login URL
    login_url = kite.login_url()
    
    print("=" * 70)
    print("Zerodha Token Setup - Interactive Mode")
    print("=" * 70)
    print()
    print("Step 1: Open this URL in your browser:")
    print(login_url)
    print()
    print("Step 2: Login to Zerodha")
    print()
    print("Step 3: After login, you'll be redirected to a URL like:")
    print("http://127.0.0.1:8080/api/zerodha/callback?request_token=XXX&...")
    print()
    print("Step 4: Copy the 'request_token' value from that URL")
    print("(It's the part after 'request_token=' and before '&')")
    print()
    print("=" * 70)
    print()
    
    # Get request token from user
    request_token = input("Paste the request_token here: ").strip()
    
    if not request_token:
        logger.error("No request token provided")
        return False
    
    try:
        # Exchange for access token
        logger.info("Exchanging request_token for access_token...")
        
        session_data = kite.generate_session(
            request_token=request_token,
            api_secret=api_secret
        )
        
        access_token = session_data["access_token"]
        refresh_token = session_data.get("refresh_token", "")
        user_id = session_data.get("user_id", "")
        
        # Save to .env
        logger.info("Saving tokens to .env file...")
        
        set_key(env_path, "ZERODHA_ACCESS_TOKEN", access_token)
        if refresh_token:
            set_key(env_path, "ZERODHA_REFRESH_TOKEN", refresh_token)
        
        print()
        print("=" * 70)
        print("✅ SUCCESS! Tokens saved to .env")
        print("=" * 70)
        print()
        print(f"User ID: {user_id}")
        print(f"Access Token: {access_token[:20]}...")
        if refresh_token:
            print(f"Refresh Token: {refresh_token[:20]}...")
        print()
        print("Next steps:")
        print("1. Restart your application to use the new tokens")
        print("2. Test token refresh: python scripts/refresh_zerodha_token.py")
        print("3. Set up daily cron job for automatic refresh")
        print()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Token exchange failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        if "request_token" in str(e).lower():
            logger.error("Request token is invalid or expired (5-minute limit)")
            logger.error("Please try again and paste the token quickly")
        
        return False


if __name__ == "__main__":
    try:
        success = get_tokens_interactive()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
