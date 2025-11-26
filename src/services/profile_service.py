"""
User Profile Management Service - OAuth Protected

This service handles all user profile operations with OAuth-based access control.
Each user can only access and modify their own profile.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from src.models import User, UserProfile
from src.utils.errors import (
    ResourceNotFoundError,
    DuplicateResourceError,
    DatabaseError,
    InvalidParamsError
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class UserProfileService:
    """Service for managing user profiles with OAuth protection."""
    
    def __init__(self, db: Session):
        """
        Initialize profile service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_or_create_user(self, user_id: str, email: Optional[str] = None) -> User:
        """
        Get existing user or create new one.
        
        Args:
            user_id: OAuth user ID (sub claim)
            email: User email (optional)
            
        Returns:
            User model instance
        """
        user = self.db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            user = User(
                user_id=user_id,
                email=email,
                is_active=True,
                last_login=datetime.now(timezone.utc)
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"New user created: {user_id}")
        else:
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            self.db.commit()
        
        return user
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile.
        
        Args:
            user_id: OAuth user ID
            
        Returns:
            Profile data or None if not found
        """
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not profile:
            return None
        
        return {
            'id': profile.id,
            'user_id': profile.user_id,
            'name': profile.name,
            'bio': profile.bio,
            'avatar_url': profile.avatar_url,
            'preferences': profile.preferences or {},
            'created_at': profile.created_at.isoformat(),
            'updated_at': profile.updated_at.isoformat(),
            'version': profile.version
        }
    
    def create_profile(
        self,
        user_id: str,
        name: str,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create new user profile.
        
        Args:
            user_id: OAuth user ID
            name: Profile name
            bio: User biography
            avatar_url: Avatar image URL
            preferences: User preferences dictionary
            
        Returns:
            Created profile data
            
        Raises:
            DuplicateResourceError: If profile already exists
        """
        # Check if profile already exists
        existing = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if existing:
            raise DuplicateResourceError(
                "UserProfile",
                "Profile already exists. Use update action instead."
            )
        
        # Ensure user exists
        self.get_or_create_user(user_id)
        
        # Create profile
        profile = UserProfile(
            user_id=user_id,
            name=name,
            bio=bio,
            avatar_url=avatar_url,
            preferences=preferences or {},
            version=1
        )
        
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        
        logger.info(f"Profile created for user: {user_id}")
        
        return self.get_profile(user_id)
    
    def update_profile(
        self,
        user_id: str,
        name: Optional[str] = None,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update existing user profile.
        
        Args:
            user_id: OAuth user ID
            name: New profile name
            bio: New biography
            avatar_url: New avatar URL
            preferences: Preferences to merge/update
            
        Returns:
            Updated profile data
            
        Raises:
            ResourceNotFoundError: If profile doesn't exist
        """
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not profile:
            raise ResourceNotFoundError("UserProfile", user_id)
        
        # Update fields if provided
        if name is not None:
            profile.name = name
        if bio is not None:
            profile.bio = bio
        if avatar_url is not None:
            profile.avatar_url = avatar_url
        if preferences is not None:
            # Merge preferences
            current_prefs = profile.preferences or {}
            current_prefs.update(preferences)
            profile.preferences = current_prefs
        
        profile.version += 1
        profile.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(profile)
        
        logger.info(f"Profile updated for user: {user_id}")
        
        return self.get_profile(user_id)
    
    def delete_profile(self, user_id: str) -> bool:
        """
        Delete user profile.
        
        Args:
            user_id: OAuth user ID
            
        Returns:
            True if deleted, False if not found
        """
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not profile:
            return False
        
        self.db.delete(profile)
        self.db.commit()
        
        logger.info(f"Profile deleted for user: {user_id}")
        
        return True


def create_profile_tool(db: Session, user_id: str) -> "ProfileTool":
    """
    Factory function to create profile tool with OAuth user context.
    
    Args:
        db: Database session
        user_id: OAuth user ID from token
        
    Returns:
        ProfileTool instance
    """
    return ProfileTool(db, user_id)


class ProfileTool:
    """
    OAuth-protected profile management tool.
    
    This tool demonstrates proper OAuth usage:
    - Requires authenticated user_id from OAuth token
    - Operations are scoped to the authenticated user
    - Users cannot access other users' profiles
    """
    
    def __init__(self, db: Session, user_id: str):
        """
        Initialize profile tool.
        
        Args:
            db: Database session
            user_id: OAuth user ID (from validated token)
        """
        self.service = UserProfileService(db)
        self.user_id = user_id  # This comes from OAuth token!
    
    def execute(
        self,
        action: str,
        name: Optional[str] = None,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute profile operation for authenticated user.
        
        Args:
            action: Operation (get, create, update, delete)
            name: Profile name
            bio: Biography
            avatar_url: Avatar URL
            preferences: User preferences
            
        Returns:
            Operation result
        """
        action = action.lower().strip()
        
        if action not in ['get', 'create', 'update', 'delete']:
            raise InvalidParamsError(
                f"Invalid action: {action}. Must be: get, create, update, delete"
            )
        
        logger.info(f"Profile action '{action}' for user: {self.user_id}")
        
        try:
            if action == 'get':
                profile = self.service.get_profile(self.user_id)
                if not profile:
                    return {
                        'success': False,
                        'message': 'Profile not found',
                        'user_id': self.user_id,
                        'profile': None
                    }
                return {
                    'success': True,
                    'message': 'Profile retrieved',
                    'profile': profile
                }
            
            elif action == 'create':
                if not name:
                    raise InvalidParamsError("Name is required to create profile")
                
                profile = self.service.create_profile(
                    user_id=self.user_id,
                    name=name,
                    bio=bio,
                    avatar_url=avatar_url,
                    preferences=preferences
                )
                return {
                    'success': True,
                    'message': 'Profile created',
                    'profile': profile
                }
            
            elif action == 'update':
                profile = self.service.update_profile(
                    user_id=self.user_id,
                    name=name,
                    bio=bio,
                    avatar_url=avatar_url,
                    preferences=preferences
                )
                return {
                    'success': True,
                    'message': 'Profile updated',
                    'profile': profile
                }
            
            elif action == 'delete':
                deleted = self.service.delete_profile(self.user_id)
                if deleted:
                    return {
                        'success': True,
                        'message': 'Profile deleted',
                        'user_id': self.user_id
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Profile not found',
                        'user_id': self.user_id
                    }
        
        except Exception as e:
            logger.error(f"Profile tool error: {e}", exc_info=True)
            raise
