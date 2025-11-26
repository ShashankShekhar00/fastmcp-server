#!/usr/bin/env python3
"""
Simple health check script for Docker container.
Returns exit code 0 if healthy, 1 if unhealthy.
"""

import sys
import urllib.request
import urllib.error

def check_health():
    """Check if the MCP server is responding."""
    try:
        # Try to connect to the MCP endpoint
        with urllib.request.urlopen('http://localhost:8000/mcp', timeout=5) as response:
            # Any response (even error) means server is running
            return 0
    except urllib.error.HTTPError as e:
        # HTTP errors mean server is running but returned error
        # This is OK for health check (400 Bad Request is expected for GET)
        if e.code in (400, 405, 500):
            return 0
        return 1
    except (urllib.error.URLError, ConnectionRefusedError, TimeoutError):
        # Connection failed - server is down
        return 1
    except Exception as e:
        print(f"Health check error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(check_health())
