"""
Test script for SSE streaming endpoints
"""
import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auth.oauth_client import OAuthClient
from src.config import config


async def test_weather_streaming():
    """Test weather streaming endpoint"""
    print("\n" + "="*60)
    print("🌤️  Testing Weather Streaming Endpoint")
    print("="*60)
    
    # Get OAuth token
    print("\n1. Getting OAuth token...")
    oauth_client = OAuthClient(
        config.OAUTH_TOKEN_URL,
        config.OAUTH_CLIENT_ID,
        config.OAUTH_CLIENT_SECRET,
        config.OAUTH_AUDIENCE
    )
    
    token = await oauth_client.get_access_token()
    print(f"✅ Token obtained: {token[:50]}...")
    
    # Connect to streaming endpoint
    url = "http://localhost:8000/stream/weather?city=London"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream"
    }
    
    print(f"\n2. Connecting to: {url}")
    print("3. Listening for events...\n")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                text = await response.text()
                print(f"❌ Error {response.status}: {text}")
                return
            
            print("✅ Connected! Receiving events:\n")
            
            event_count = 0
            async for line in response.content:
                line = line.decode('utf-8').strip()
                
                if not line:
                    continue
                
                if line.startswith(':'):
                    # Keepalive message
                    print(f"💓 {line}")
                    continue
                
                if line.startswith('event:'):
                    event_type = line.split(':', 1)[1].strip()
                    print(f"\n📨 Event Type: {event_type}")
                    event_count += 1
                
                elif line.startswith('data:'):
                    data = line.split(':', 1)[1].strip()
                    try:
                        parsed = json.loads(data)
                        print(f"   Data: {json.dumps(parsed, indent=6)}")
                    except json.JSONDecodeError:
                        print(f"   Data: {data}")
                    
                    # Stop after complete event
                    if event_type == 'complete':
                        print(f"\n✅ Received {event_count} events total")
                        return


async def test_file_streaming():
    """Test file streaming endpoint"""
    print("\n" + "="*60)
    print("📄 Testing File Streaming Endpoint")
    print("="*60)
    
    # Get OAuth token
    print("\n1. Getting OAuth token...")
    oauth_client = OAuthClient(
        config.OAUTH_TOKEN_URL,
        config.OAUTH_CLIENT_ID,
        config.OAUTH_CLIENT_SECRET,
        config.OAUTH_AUDIENCE
    )
    
    token = await oauth_client.get_access_token()
    print(f"✅ Token obtained: {token[:50]}...")
    
    # Test write operation
    url = "http://localhost:8000/stream/file"
    params = {
        "operation": "write",
        "filepath": "test_output/streaming_test.txt",
        "content": "Hello from SSE streaming test!"
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream"
    }
    
    print(f"\n2. Connecting to: {url}")
    print(f"   Operation: write")
    print(f"   File: {params['filepath']}")
    print("3. Listening for events...\n")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                text = await response.text()
                print(f"❌ Error {response.status}: {text}")
                return
            
            print("✅ Connected! Receiving events:\n")
            
            event_count = 0
            async for line in response.content:
                line = line.decode('utf-8').strip()
                
                if not line:
                    continue
                
                if line.startswith(':'):
                    # Keepalive message
                    print(f"💓 {line}")
                    continue
                
                if line.startswith('event:'):
                    event_type = line.split(':', 1)[1].strip()
                    print(f"\n📨 Event Type: {event_type}")
                    event_count += 1
                
                elif line.startswith('data:'):
                    data = line.split(':', 1)[1].strip()
                    try:
                        parsed = json.loads(data)
                        print(f"   Data: {json.dumps(parsed, indent=6)}")
                    except json.JSONDecodeError:
                        print(f"   Data: {data}")
                    
                    # Stop after complete event
                    if event_type == 'complete':
                        print(f"\n✅ Received {event_count} events total")
                        return


async def main():
    """Run all SSE streaming tests"""
    print("\n🧪 SSE Streaming Tests")
    print("Make sure the server is running on port 8000!\n")
    
    try:
        # Test weather streaming
        await test_weather_streaming()
        
        # Wait a bit between tests
        await asyncio.sleep(2)
        
        # Test file streaming
        await test_file_streaming()
        
        print("\n" + "="*60)
        print("✅ All SSE streaming tests completed!")
        print("="*60 + "\n")
        
    except aiohttp.ClientConnectorError:
        print("\n❌ Error: Could not connect to server")
        print("   Make sure the server is running: python -m src.server")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
