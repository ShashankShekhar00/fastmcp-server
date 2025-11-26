"""
Notes management tool - OAuth protected.
Provides CRUD operations for user notes.
"""

from typing import Dict, Any, Optional, List
from src.services.notes_service import NotesService
from src.utils.errors import MCPError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class NotesTool:
    """Wrapper for notes service as MCP tool."""
    
    def __init__(self, db_session_factory):
        """
        Initialize notes tool.
        
        Args:
            db_session_factory: Callable that returns a database session
        """
        self.db_session_factory = db_session_factory
        logger.info("NotesTool initialized")
    
    def execute(
        self,
        action: str,
        user_id: str,
        note_id: Optional[int] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_pinned: bool = False,
        include_archived: bool = False,
        tag: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute notes operations.
        
        Args:
            action: Operation to perform (create, get, list, update, delete, archive, unarchive, pin, unpin)
            user_id: OAuth user ID (from token)
            note_id: Note ID (for get, update, delete, archive, pin operations)
            title: Note title (for create, update)
            content: Note content (for create, update)
            tags: List of tags (for create, update)
            is_pinned: Pin status (for create, update)
            include_archived: Include archived notes in list
            tag: Filter by tag (for list)
            
        Returns:
            Operation result
            
        Raises:
            MCPError: If action is invalid or operation fails
        """
        try:
            with self.db_session_factory() as db:
                service = NotesService(db)
                
                if action == "create":
                    if not content:
                        raise MCPError(-32602, "content is required for create action")
                    result = service.create_note(user_id, content, title, tags, is_pinned)
                    
                elif action == "get":
                    if note_id is None:
                        raise MCPError(-32602, "note_id is required for get action")
                    result = service.get_note(note_id, user_id)
                    if not result:
                        raise MCPError(-32001, f"Note {note_id} not found or access denied")
                    
                elif action == "list":
                    notes = service.list_notes(
                        user_id,
                        include_archived=include_archived,
                        tag=tag
                    )
                    result = {"notes": notes, "count": len(notes)}
                    
                elif action == "update":
                    if note_id is None:
                        raise MCPError(-32602, "note_id is required for update action")
                    result = service.update_note(note_id, user_id, content, title, tags, is_pinned)
                    if not result:
                        raise MCPError(-32001, f"Note {note_id} not found or access denied")
                    
                elif action == "delete":
                    if note_id is None:
                        raise MCPError(-32602, "note_id is required for delete action")
                    success = service.delete_note(note_id, user_id)
                    if not success:
                        raise MCPError(-32001, f"Note {note_id} not found or access denied")
                    result = {"success": True, "message": f"Note {note_id} deleted"}
                    
                elif action == "archive":
                    if note_id is None:
                        raise MCPError(-32602, "note_id is required for archive action")
                    result = service.update_note(note_id, user_id, is_archived=True)
                    if not result:
                        raise MCPError(-32001, f"Note {note_id} not found or access denied")
                    
                elif action == "unarchive":
                    if note_id is None:
                        raise MCPError(-32602, "note_id is required for unarchive action")
                    result = service.update_note(note_id, user_id, is_archived=False)
                    if not result:
                        raise MCPError(-32001, f"Note {note_id} not found or access denied")
                    
                elif action == "pin":
                    if note_id is None:
                        raise MCPError(-32602, "note_id is required for pin action")
                    result = service.update_note(note_id, user_id, is_pinned=True)
                    if not result:
                        raise MCPError(-32001, f"Note {note_id} not found or access denied")
                    
                elif action == "unpin":
                    if note_id is None:
                        raise MCPError(-32602, "note_id is required for unpin action")
                    result = service.update_note(note_id, user_id, is_pinned=False)
                    if not result:
                        raise MCPError(-32001, f"Note {note_id} not found or access denied")
                    
                else:
                    raise MCPError(
                        -32602,
                        f"Invalid action: {action}",
                        {"valid_actions": ["create", "get", "list", "update", "delete", "archive", "unarchive", "pin", "unpin"]}
                    )
                
                logger.info(f"Notes action '{action}' completed for user {user_id}")
                return result
            
        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Notes tool error: {e}", exc_info=True)
            raise MCPError(-32603, f"Internal error: {str(e)}")


def create_notes_tool(db_session_factory):
    """
    Factory function to create notes tool instance.
    
    Args:
        db_session_factory: Database session factory
        
    Returns:
        NotesTool instance
    """
    return NotesTool(db_session_factory)
