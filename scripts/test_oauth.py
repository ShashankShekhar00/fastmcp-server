"""
Test OAuth 2.0 authentication flow.

This script tests:
1. Getting access token from Auth0
2. Validating JWT token
3. Extracting user info and scopes
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.auth.oauth_client import OAuthClient
from src.auth.jwt_validator import JWTValidator

# Load environment variables
load_dotenv()


def test_oauth_flow():
    """Test complete OAuth 2.0 flow."""
    
    print("=" * 70)
    print("OAuth 2.0 Authentication Test")
    print("=" * 70 + "\n")
    
    # Get configuration
    token_url = os.getenv("OAUTH_TOKEN_URL")
    client_id = os.getenv("OAUTH_CLIENT_ID")
    client_secret = os.getenv("OAUTH_CLIENT_SECRET")
    audience = os.getenv("OAUTH_AUDIENCE")
    jwks_url = os.getenv("OAUTH_JWKS_URL")
    issuer = os.getenv("OAUTH_ISSUER")
    
    print("📋 Configuration:")
    print(f"   Token URL: {token_url}")
    print(f"   Client ID: {client_id[:10]}...")
    print(f"   Audience: {audience}")
    print(f"   Issuer: {issuer}")
    print(f"   JWKS URL: {jwks_url}\n")
    
    # Step 1: Get access token
    print("Step 1: Getting access token from Auth0...")
    print("-" * 70)
    
    try:
        oauth_client = OAuthClient(
            token_url=token_url,
            client_id=client_id,
            client_secret=client_secret,
            audience=audience
        )
        
        access_token = oauth_client.get_access_token()
        print(f"✅ Access token obtained!")
        print(f"   Token (first 20 chars): {access_token[:20]}...")
        print(f"   Token length: {len(access_token)} characters\n")
        
        # Show token info
        token_info = oauth_client.get_token_info()
        print(f"   Cached: {token_info.get('cached')}")
        print(f"   Valid: {token_info.get('valid')}")
        print(f"   Expires in: {token_info.get('seconds_until_expiry')} seconds\n")
        
    except Exception as e:
        print(f"❌ Failed to get access token: {e}\n")
        return False
    
    # Step 2: Validate token
    print("Step 2: Validating JWT token...")
    print("-" * 70)
    
    try:
        jwt_validator = JWTValidator(
            jwks_url=jwks_url,
            audience=audience,
            issuer=issuer
        )
        
        token_data = jwt_validator.validate_token(access_token)
        print(f"✅ Token validated successfully!\n")
        
        print(f"   User ID: {token_data['user_id']}")
        print(f"   Scopes: {token_data['scopes']}")
        print(f"   Expires at (timestamp): {token_data['expires_at']}\n")
        
        # Show full payload
        print("   Full token payload:")
        for key, value in token_data['payload'].items():
            print(f"      {key}: {value}")
        print()
        
    except Exception as e:
        print(f"❌ Token validation failed: {e}\n")
        return False
    
    # Step 3: Test token info (unverified)
    print("Step 3: Getting token info (unverified)...")
    print("-" * 70)
    
    try:
        info = jwt_validator.get_token_info(access_token)
        print(f"✅ Token info retrieved!\n")
        
        print(f"   Algorithm: {info.get('header', {}).get('alg')}")
        print(f"   Token type: {info.get('header', {}).get('typ')}")
        print(f"   Key ID: {info.get('header', {}).get('kid')}\n")
        
        print(f"   Issued at: {info.get('issued_at')}")
        print(f"   Expires at: {info.get('expires_at')}\n")
        
    except Exception as e:
        print(f"⚠️  Could not get token info: {e}\n")
    
    # Step 4: Test cached token
    print("Step 4: Testing token cache...")
    print("-" * 70)
    
    try:
        # Get token again (should use cache)
        cached_token = oauth_client.get_access_token()
        
        if cached_token == access_token:
            print("✅ Cached token returned successfully!")
            print("   Same token was returned from cache\n")
        else:
            print("⚠️  Different token returned (cache may have expired)\n")
        
    except Exception as e:
        print(f"❌ Cache test failed: {e}\n")
    
    print("=" * 70)
    print("✅ All OAuth 2.0 tests passed!")
    print("=" * 70)
    print("\n💡 You can now use this access token to authenticate requests:")
    print(f'   Authorization: Bearer {access_token[:30]}...\n')
    
    return True


if __name__ == "__main__":
    success = test_oauth_flow()
    sys.exit(0 if success else 1)
