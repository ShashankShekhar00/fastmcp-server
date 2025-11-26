"""
Personal Notes Service - OAuth Protected

User-specific notes management with full CRUD operations.
Demonstrates OAuth requirement: users can only access their own notes.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone

from src.models import User, UserNote
from src.utils.errors import (
    ResourceNotFoundError,
    DatabaseError,
    InvalidParamsError
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class NotesService:
    """Service for managing user notes with OAuth protection."""
    
    def __init__(self, db: Session):
        """
        Initialize notes service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_note(
        self,
        user_id: str,
        content: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_pinned: bool = False
    ) -> Dict[str, Any]:
        """
        Create new note for user.
        
        Args:
            user_id: OAuth user ID
            content: Note content
            title: Note title
            tags: List of tags
            is_pinned: Whether note is pinned
            
        Returns:
            Created note data
        """
        note = UserNote(
            user_id=user_id,
            title=title,
            content=content,
            tags=tags or [],
            is_pinned=is_pinned,
            is_archived=False
        )
        
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        
        logger.info(f"Note created for user {user_id}: ID {note.id}")
        
        return self._note_to_dict(note)
    
    def get_note(self, note_id: int, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific note (only if owned by user).
        
        Args:
            note_id: Note ID
            user_id: OAuth user ID
            
        Returns:
            Note data or None
        """
        note = self.db.query(UserNote).filter(
            UserNote.id == note_id,
            UserNote.user_id == user_id  # Security: only owner can access
        ).first()
        
        if not note:
            return None
        
        return self._note_to_dict(note)
    
    def list_notes(
        self,
        user_id: str,
        include_archived: bool = False,
        pinned_only: bool = False,
        tag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all notes for user.
        
        Args:
            user_id: OAuth user ID
            include_archived: Include archived notes
            pinned_only: Show only pinned notes
            tag: Filter by specific tag
            
        Returns:
            List of note data
        """
        query = self.db.query(UserNote).filter(
            UserNote.user_id == user_id  # Security: only show user's notes
        )
        
        if not include_archived:
            query = query.filter(UserNote.is_archived == False)
        
        if pinned_only:
            query = query.filter(UserNote.is_pinned == True)
        
        if tag:
            # Filter notes that have this tag
            query = query.filter(UserNote.tags.contains([tag]))
        
        # Sort: pinned first, then by creation date (newest first)
        query = query.order_by(
            desc(UserNote.is_pinned),
            desc(UserNote.created_at)
        )
        
        notes = query.all()
        
        return [self._note_to_dict(note) for note in notes]
    
    def update_note(
        self,
        note_id: int,
        user_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_pinned: Optional[bool] = None,
        is_archived: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update existing note.
        
        Args:
            note_id: Note ID
            user_id: OAuth user ID (for ownership verification)
            title: New title
            content: New content
            tags: New tags list
            is_pinned: Pin status
            is_archived: Archive status
            
        Returns:
            Updated note data
            
        Raises:
            ResourceNotFoundError: If note not found or not owned by user
        """
        note = self.db.query(UserNote).filter(
            UserNote.id == note_id,
            UserNote.user_id == user_id  # Security: only owner can update
        ).first()
        
        if not note:
            raise ResourceNotFoundError("Note", note_id)
        
        # Update fields if provided
        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        if tags is not None:
            note.tags = tags
        if is_pinned is not None:
            note.is_pinned = is_pinned
        if is_archived is not None:
            note.is_archived = is_archived
        
        note.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(note)
        
        logger.info(f"Note updated: ID {note_id} by user {user_id}")
        
        return self._note_to_dict(note)
    
    def delete_note(self, note_id: int, user_id: str) -> bool:
        """
        Delete note (only if owned by user).
        
        Args:
            note_id: Note ID
            user_id: OAuth user ID
            
        Returns:
            True if deleted, False if not found
        """
        note = self.db.query(UserNote).filter(
            UserNote.id == note_id,
            UserNote.user_id == user_id  # Security: only owner can delete
        ).first()
        
        if not note:
            return False
        
        self.db.delete(note)
        self.db.commit()
        
        logger.info(f"Note deleted: ID {note_id} by user {user_id}")
        
        return True
    
    def _note_to_dict(self, note: UserNote) -> Dict[str, Any]:
        """Convert note model to dictionary."""
        return {
            'id': note.id,
            'user_id': note.user_id,
            'title': note.title,
            'content': note.content,
            'tags': note.tags or [],
            'is_pinned': note.is_pinned,
            'is_archived': note.is_archived,
            'created_at': note.created_at.isoformat(),
            'updated_at': note.updated_at.isoformat()
        }


class NotesTool:
    """
    OAuth-protected personal notes tool.
    
    Demonstrates OAuth requirement:
    - All operations are scoped to authenticated user
    - Users cannot see or modify other users' notes
    - user_id comes from validated OAuth token
    """
    
    def __init__(self, db: Session, user_id: str):
        """
        Initialize notes tool.
        
        Args:
            db: Database session
            user_id: OAuth user ID (from validated token)
        """
        self.service = NotesService(db)
        self.user_id = user_id  # From OAuth token!
    
    def execute(
        self,
        action: str,
        note_id: Optional[int] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_pinned: Optional[bool] = None,
        is_archived: Optional[bool] = None,
        include_archived: bool = False,
        pinned_only: bool = False,
        tag_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute notes operation for authenticated user.
        
        Args:
            action: Operation (create, get, list, update, delete)
            note_id: Note ID (for get/update/delete)
            title: Note title
            content: Note content
            tags: Tags list
            is_pinned: Pin status
            is_archived: Archive status
            include_archived: Include archived in list
            pinned_only: Show only pinned in list
            tag_filter: Filter list by tag
            
        Returns:
            Operation result
        """
        action = action.lower().strip()
        
        valid_actions = ['create', 'get', 'list', 'update', 'delete']
        if action not in valid_actions:
            raise InvalidParamsError(
                f"Invalid action: {action}. Must be: {', '.join(valid_actions)}"
            )
        
        logger.info(f"Notes action '{action}' for user: {self.user_id}")
        
        try:
            if action == 'create':
                if not content:
                    raise InvalidParamsError("Content is required to create note")
                
                note = self.service.create_note(
                    user_id=self.user_id,
                    content=content,
                    title=title,
                    tags=tags,
                    is_pinned=is_pinned or False
                )
                return {
                    'success': True,
                    'message': 'Note created',
                    'note': note
                }
            
            elif action == 'get':
                if note_id is None:
                    raise InvalidParamsError("note_id is required for get action")
                
                note = self.service.get_note(note_id, self.user_id)
                if not note:
                    return {
                        'success': False,
                        'message': 'Note not found or access denied',
                        'note_id': note_id
                    }
                return {
                    'success': True,
                    'message': 'Note retrieved',
                    'note': note
                }
            
            elif action == 'list':
                notes = self.service.list_notes(
                    user_id=self.user_id,
                    include_archived=include_archived,
                    pinned_only=pinned_only,
                    tag=tag_filter
                )
                return {
                    'success': True,
                    'message': f'Found {len(notes)} notes',
                    'count': len(notes),
                    'notes': notes
                }
            
            elif action == 'update':
                if note_id is None:
                    raise InvalidParamsError("note_id is required for update action")
                
                note = self.service.update_note(
                    note_id=note_id,
                    user_id=self.user_id,
                    title=title,
                    content=content,
                    tags=tags,
                    is_pinned=is_pinned,
                    is_archived=is_archived
                )
                return {
                    'success': True,
                    'message': 'Note updated',
                    'note': note
                }
            
            elif action == 'delete':
                if note_id is None:
                    raise InvalidParamsError("note_id is required for delete action")
                
                deleted = self.service.delete_note(note_id, self.user_id)
                if deleted:
                    return {
                        'success': True,
                        'message': 'Note deleted',
                        'note_id': note_id
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Note not found or access denied',
                        'note_id': note_id
                    }
        
        except Exception as e:
            logger.error(f"Notes tool error: {e}", exc_info=True)
            raise


def create_notes_tool(db: Session, user_id: str) -> NotesTool:
    """
    Factory function to create notes tool with OAuth user context.
    
    Args:
        db: Database session
        user_id: OAuth user ID from token
        
    Returns:
        NotesTool instance
    """
    return NotesTool(db, user_id)
