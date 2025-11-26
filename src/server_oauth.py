"""
FastMCP Server with OAuth Support - Pure FastMCP Approach
Provides both public and OAuth-protected tools via SSE transport.
"""

import logging
from typing import Optional, Dict, Any, List
from fastmcp import FastMCP

from src.config import config
from src.database.session import get_db_session_factory
from src.tools.file_operations import FileOperationsTool
from src.tools.weather import WeatherTool
from src.tools.notes import NotesTool
from src.tools.profile import ProfileTool

# Setup logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize database
db_session_factory = get_db_session_factory()

# Initialize tools
file_tool = FileOperationsTool(
    allowed_directories=config.ALLOWED_FILE_PATHS,
    max_file_size_bytes=config.MAX_FILE_SIZE_BYTES,
    allowed_extensions=config.ALLOWED_FILE_EXTENSIONS
)
weather_tool = WeatherTool(
    api_key=config.OPENWEATHER_API_KEY,
    base_url=config.OPENWEATHER_BASE_URL
)
notes_tool = NotesTool(db_session_factory)
profile_tool = ProfileTool(db_session_factory)

logger.info("Database initialized")
logger.info("All tools initialized successfully")

# Create FastMCP instance
mcp = FastMCP("lund09")


# ============================================================================
# PUBLIC TOOLS (No Authentication Required)
# ============================================================================

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
    try:
        result = file_tool.execute(operation=operation, filepath=filepath, content=content)
        logger.info(f"File operation '{operation}' completed successfully")
        return result
    except Exception as e:
        logger.error(f"File operation failed: {e}")
        raise


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
    try:
        result = weather_tool.execute(city=city)
        logger.info(f"Weather fetched for city: {city}")
        return result
    except Exception as e:
        logger.error(f"Weather fetch failed: {e}")
        raise


# ============================================================================
# OAUTH-PROTECTED TOOLS (Using test user for now)
# ============================================================================

@mcp.tool()
def notes(
    action: str,
    note_id: Optional[int] = None,
    title: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None,
    is_pinned: bool = False,
    include_archived: bool = False,
    tag: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage personal notes (OAuth required - currently using test user).
    
    Actions:
        - create: Create new note (requires: content, optional: title, tags, is_pinned)
        - get: Get specific note (requires: note_id)
        - list: List all notes (optional: include_archived, tag)
        - update: Update note (requires: note_id, optional: title, content, tags, is_pinned)
        - delete: Delete note (requires: note_id)
        - archive: Archive note (requires: note_id)
        - unarchive: Unarchive note (requires: note_id)
        - pin: Pin note (requires: note_id)
        - unpin: Unpin note (requires: note_id)
    
    Args:
        action: Operation to perform
        note_id: Note ID (for get, update, delete, archive, pin operations)
        title: Note title
        content: Note content
        tags: List of tags
        is_pinned: Pin status
        include_archived: Include archived notes in list
        tag: Filter by tag
    
    Returns:
        Operation result with note data
    """
    # TODO: Extract user_id from OAuth token
    # For now, use test user
    test_user_id = "test_user_123"
    
    try:
        result = notes_tool.execute(
            action=action,
            user_id=test_user_id,
            note_id=note_id,
            title=title,
            content=content,
            tags=tags,
            is_pinned=is_pinned,
            include_archived=include_archived,
            tag=tag
        )
        logger.info(f"Notes action '{action}' completed for user: {test_user_id}")
        return result
    except Exception as e:
        logger.error(f"Notes operation failed: {e}")
        raise


@mcp.tool()
def profile(
    action: str,
    name: Optional[str] = None,
    bio: Optional[str] = None,
    avatar_url: Optional[str] = None,
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Manage user profile (OAuth required - currently using test user).
    
    Actions:
        - get: Get current user profile
        - create: Create profile (requires: name, optional: bio, avatar_url, preferences)
        - update: Update profile (optional: name, bio, avatar_url, preferences)
        - delete: Delete profile
    
    Args:
        action: Operation to perform
        name: User's display name
        bio: User biography
        avatar_url: URL to avatar image
        preferences: User preferences dictionary
    
    Returns:
        Operation result with profile data
    """
    # TODO: Extract user_id from OAuth token
    # For now, use test user
    test_user_id = "test_user_123"
    
    try:
        result = profile_tool.execute(
            action=action,
            user_id=test_user_id,
            name=name,
            bio=bio,
            avatar_url=avatar_url,
            preferences=preferences
        )
        logger.info(f"Profile action '{action}' completed for user: {test_user_id}")
        return result
    except Exception as e:
        logger.error(f"Profile operation failed: {e}")
        raise


# Run server
if __name__ == "__main__":
    print("=" * 70)
    print("🚀 FastMCP Server with OAuth Starting")
    print("=" * 70)
    print(f"📍 Environment: {config.ENVIRONMENT}")
    print(f"🔧 Transport: HTTP")
    print(f"🌐 Port: {config.PORT}")
    print(f"📝 Log Level: {config.LOG_LEVEL}")
    print("=" * 70)
    print("🔌 Registered Tools:")
    print("   PUBLIC (No Auth):")
    print("     • file_operations - Read/write with path validation")
    print("     • weather - OpenWeatherMap API")
    print("   OAUTH-PROTECTED (Using test user for now):")
    print("     • notes - Personal notes CRUD")
    print("     • profile - User profile management")
    print("=" * 70)
    print(f"💡 Server URL: http://localhost:{config.PORT}")
    print(f"💡 MCP Endpoint: http://localhost:{config.PORT}/mcp")
    print(f"💡 Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=config.PORT
    )
