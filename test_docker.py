#!/usr/bin/env python3
"""
Quick test script to verify Docker deployment.
Run after: docker compose up -d
"""

import sys
import time
import urllib.request
import json

def test_endpoint(url, test_name):
    """Test an endpoint and return result."""
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.status
            print(f"✅ {test_name}: HTTP {status}")
            return True
    except urllib.error.HTTPError as e:
        # 400 or 405 is OK for MCP endpoint
        if e.code in (400, 405):
            print(f"✅ {test_name}: Server responding (HTTP {e.code})")
            return True
        print(f"❌ {test_name}: HTTP {e.code}")
        return False
    except Exception as e:
        print(f"❌ {test_name}: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("🐳 Docker Deployment Test")
    print("=" * 60)
    print()
    
    print("Waiting for container to be ready...")
    time.sleep(2)
    
    tests = [
        ("http://localhost:8000/mcp", "MCP Endpoint"),
    ]
    
    results = []
    for url, name in tests:
        result = test_endpoint(url, name)
        results.append(result)
        time.sleep(0.5)
    
    print()
    print("=" * 60)
    if all(results):
        print("✅ All tests passed! Docker deployment successful!")
        print()
        print("Your MCP server is running at: http://localhost:8000/mcp")
        print()
        print("Next steps:")
        print("  • View logs: docker compose logs -f")
        print("  • Check health: docker compose ps")
        print("  • Test tools: Use VS Code MCP extension")
        return 0
    else:
        print("❌ Some tests failed. Check logs:")
        print("  docker compose logs -f mcp-server")
        return 1

if __name__ == "__main__":
    sys.exit(main())
