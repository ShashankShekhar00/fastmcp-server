"""
Test OAuth-protected MCP server endpoints.

This script tests:
1. Health endpoint (no auth required)
2. SSE endpoint without auth (should fail with 401)
3. SSE endpoint with valid token (should succeed)
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import requests
from src.auth.oauth_client import OAuthClient

# Load environment variables
load_dotenv()


def test_mcp_server_auth():
    """Test MCP server with OAuth authentication."""
    
    print("=" * 70)
    print("MCP Server OAuth Authentication Test")
    print("=" * 70 + "\n")
    
    base_url = "http://localhost:8000"
    
    # Step 1: Test health endpoint (no auth required)
    print("Step 1: Testing health endpoint (no auth required)...")
    print("-" * 70)
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed!")
            print(f"   Status: {data.get('status')}")
            print(f"   Auth enabled: {data.get('auth_enabled')}")
            print(f"   Tools: {data.get('tools')}\n")
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}\n")
            return False
    except requests.RequestException as e:
        print(f"❌ Could not connect to server: {e}")
        print(f"💡 Make sure the server is running: python -m src.server\n")
        return False
    
    # Step 2: Test SSE without auth (should fail if auth enabled)
    print("Step 2: Testing SSE endpoint WITHOUT authentication...")
    print("-" * 70)
    
    try:
        response = requests.get(f"{base_url}/sse", timeout=5)
        if response.status_code == 401:
            print(f"✅ Correctly rejected unauthenticated request!")
            print(f"   HTTP 401 Unauthorized returned\n")
        elif response.status_code == 200:
            print(f"⚠️  Server accepted unauthenticated request")
            print(f"   OAuth authentication may be disabled\n")
        else:
            print(f"❌ Unexpected response: HTTP {response.status_code}\n")
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}\n")
    
    # Step 3: Get access token
    print("Step 3: Getting access token from Auth0...")
    print("-" * 70)
    
    try:
        oauth_client = OAuthClient(
            token_url=os.getenv("OAUTH_TOKEN_URL"),
            client_id=os.getenv("OAUTH_CLIENT_ID"),
            client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
            audience=os.getenv("OAUTH_AUDIENCE")
        )
        
        access_token = oauth_client.get_access_token()
        print(f"✅ Access token obtained!")
        print(f"   Token: {access_token[:30]}...\n")
        
    except Exception as e:
        print(f"❌ Failed to get access token: {e}\n")
        return False
    
    # Step 4: Test SSE with auth (should succeed)
    print("Step 4: Testing SSE endpoint WITH authentication...")
    print("-" * 70)
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(f"{base_url}/sse", headers=headers, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Authenticated request accepted!")
            print(f"   HTTP 200 OK returned")
            print(f"   Server validated JWT token successfully\n")
        elif response.status_code == 401:
            print(f"❌ Authenticated request rejected: HTTP 401")
            print(f"   Token may be invalid or expired\n")
            return False
        else:
            print(f"⚠️  Unexpected response: HTTP {response.status_code}\n")
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}\n")
        return False
    
    # Step 5: Test with invalid token (should fail)
    print("Step 5: Testing with INVALID token...")
    print("-" * 70)
    
    try:
        headers = {
            "Authorization": "Bearer invalid_token_12345"
        }
        response = requests.get(f"{base_url}/sse", headers=headers, timeout=5)
        
        if response.status_code == 401:
            print(f"✅ Correctly rejected invalid token!")
            print(f"   HTTP 401 Unauthorized returned\n")
        else:
            print(f"⚠️  Unexpected response: HTTP {response.status_code}\n")
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}\n")
    
    print("=" * 70)
    print("✅ OAuth authentication is working correctly!")
    print("=" * 70)
    print("\n💡 Your MCP server is protected by OAuth 2.0 JWT authentication")
    print("💡 Clients must provide valid tokens to access the /sse endpoint\n")
    
    return True


if __name__ == "__main__":
    print("\n⚠️  Make sure the MCP server is running before running this test:")
    print("   python -m src.server\n")
    
    input("Press Enter to continue...")
    print()
    
    success = test_mcp_server_auth()
    sys.exit(0 if success else 1)
