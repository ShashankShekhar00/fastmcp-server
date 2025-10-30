"""Quick test to understand FastMCP API."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import fastmcp

print("FastMCP version:", fastmcp.__version__)
print("\nFastMCP attributes:")
print([x for x in dir(fastmcp) if not x.startswith('_')])

# Create instance
mcp = fastmcp.FastMCP("Test Server")

print("\nFastMCP instance methods:")
print([x for x in dir(mcp) if not x.startswith('_') and callable(getattr(mcp, x))])

# Check for run method
if hasattr(mcp, 'run'):
    print("\n✓ Has 'run' method")
if hasattr(mcp, 'get_asgi_app'):
    print("✓ Has 'get_asgi_app' method")
if hasattr(mcp, 'tool'):
    print("✓ Has 'tool' decorator")

print("\nFastMCP object type:", type(mcp))
