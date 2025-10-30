"""
Simplified FastMCP Server - Using FastMCP's native capabilities.
"""

import time
from typing import Dict, Any

from fastmcp import FastMCP

from src.config import config
from src.tools.file_operations import create_file_operations_tool
from src.tools.weather import create_weather_tool
from src.utils.logging import init_app_logger, get_logger, log_tool_execution
from src.utils.errors import MCPError

# Initialize logger
logger = init_app_logger(
    log_level=config.LOG_LEVEL if config else "INFO",
    structured=False
)

# Initialize FastMCP
mcp = FastMCP("MCP Server")

# Initialize tools
file_tool = None
weather_tool = None

if config:
    try:
        file_tool = create_file_operations_tool(config)
        weather_tool = create_weather_tool(config)
        logger.info("Tools initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing tools: {e}")


# Register File Operations Tool
@mcp.tool()
def file_operations(operation: str, filepath: str, content: str = "") -> Dict[str, Any]:
    """
    Secure file operations with path validation.
    
    Supports read and write operations within allowed directories only.
    
    Args:
        operation: Operation type - 'read' or 'write'
        filepath: Absolute path to file (must be in allowed directories)
        content: Content to write (required for write operation)
    
    Returns:
        For read: {"content": str, "metadata": {...}}
        For write: {"success": bool, "filepath": str, "bytes_written": int}
    """
    if not file_tool:
        raise MCPError(
            -32000,
            "File operations tool not initialized",
            {"config_loaded": config is not None}
        )
    
    start_time = time.time()
    request_id = f"file-{int(time.time() * 1000)}"
    
    try:
        result = file_tool.execute(operation=operation, filepath=filepath, content=content)
        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(logger, "file_operations", duration_ms, True, request_id=request_id)
        return result
    except MCPError:
        raise
    except Exception as e:
        raise MCPError(-32603, f"Internal error: {str(e)}", {"operation": operation})


# Register Weather Tool
@mcp.tool()
def weather(city: str) -> Dict[str, Any]:
    """
    Get current weather data for a city.
    
    Fetches real-time weather information from OpenWeatherMap API.
    
    Args:
        city: City name (e.g., "London", "New York", "São Paulo")
    
    Returns:
        Weather data including temperature, humidity, wind speed, description
    """
    if not weather_tool:
        raise MCPError(
            -32000,
            "Weather tool not initialized",
            {"config_loaded": config is not None}
        )
    
    start_time = time.time()
    request_id = f"weather-{int(time.time() * 1000)}"
    
    try:
        result = weather_tool.execute(city=city)
        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(logger, "weather", duration_ms, True, request_id=request_id)
        return result
    except MCPError:
        raise
    except Exception as e:
        raise MCPError(-32603, f"Internal error: {str(e)}", {"city": city})


# Run server
if __name__ == "__main__":
    # For development, allow running without OAuth credentials
    if not config:
        print("⚠️  Warning: Running with incomplete configuration")
        print("💡 Some features may not work without proper credentials in .env")
        print()
        # We can still run the server, tools just won't work yet
    
    print("=" * 60)
    print("🚀 MCP Server Starting")
    print("=" * 60)
    print(f"📍 Environment: {config.ENVIRONMENT if config else 'development'}")
    print(f"🔧 Transport: SSE")
    print(f"🌐 Port: 8000")
    print(f"📝 Log Level: INFO")
    print("=" * 60)
    print(f"🔌 Registered Tools:")
    print(f"   • file_operations (read/write with path validation)")
    print(f"   • weather (OpenWeatherMap API)")
    print("=" * 60)
    print(f"💡 Server will start on http://localhost:8000")
    print(f"💡 Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    # Run FastMCP's built-in server
    mcp.run(transport="sse", port=8000)
