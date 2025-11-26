"""
User profile management tool - OAuth protected.
Provides operations for managing user profiles.
"""

from typing import Dict, Any, Optional
from src.services.profile_service import UserProfileService
from src.utils.errors import MCPError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ProfileTool:
    """Wrapper for profile service as MCP tool."""
    
    def __init__(self, db_session_factory):
        """
        Initialize profile tool.
        
        Args:
            db_session_factory: Callable that returns a database session
        """
        self.db_session_factory = db_session_factory
        logger.info("ProfileTool initialized")
    
    def execute(
        self,
        action: str,
        user_id: str,
        name: Optional[str] = None,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute profile operations.
        
        Args:
            action: Operation to perform (get, create, update, delete)
            user_id: OAuth user ID (from token)
            name: User's display name
            bio: User biography
            avatar_url: URL to user avatar image
            preferences: User preferences dictionary
            
        Returns:
            Operation result
            
        Raises:
            MCPError: If action is invalid or operation fails
        """
        try:
            with self.db_session_factory() as db:
                service = UserProfileService(db)
                
                # Ensure user exists
                service.get_or_create_user(user_id)
                
                if action == "get":
                    result = service.get_profile(user_id)
                    if not result:
                        # Return empty profile structure if not exists
                        result = {
                            "user_id": user_id,
                            "name": None,
                            "bio": None,
                            "avatar_url": None,
                            "preferences": {},
                            "exists": False
                        }
                    else:
                        result["exists"] = True
                    
                elif action == "create":
                    if not name:
                        raise MCPError(-32602, "name is required for create action")
                    result = service.create_profile(
                        user_id=user_id,
                        name=name,
                        bio=bio,
                        avatar_url=avatar_url,
                        preferences=preferences or {}
                    )
                    
                elif action == "update":
                    result = service.update_profile(
                        user_id=user_id,
                        name=name,
                        bio=bio,
                        avatar_url=avatar_url,
                        preferences=preferences
                    )
                    if not result:
                        raise MCPError(-32001, "Profile not found")
                    
                elif action == "delete":
                    success = service.delete_profile(user_id)
                    if not success:
                        raise MCPError(-32001, "Profile not found")
                    result = {"success": True, "message": "Profile deleted"}
                    
                else:
                    raise MCPError(
                        -32602,
                        f"Invalid action: {action}",
                        {"valid_actions": ["get", "create", "update", "delete"]}
                    )
                
                logger.info(f"Profile action '{action}' completed for user {user_id}")
                return result
            
        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Profile tool error: {e}", exc_info=True)
            raise MCPError(-32603, f"Internal error: {str(e)}")


def create_profile_tool(db_session_factory):
    """
    Factory function to create profile tool instance.
    
    Args:
        db_session_factory: Database session factory
        
    Returns:
        ProfileTool instance
    """
    return ProfileTool(db_session_factory)
