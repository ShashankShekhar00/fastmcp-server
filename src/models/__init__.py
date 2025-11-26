"""
Database models for the MCP server.
Uses SQLAlchemy ORM for database interactions.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """User model for OAuth authentication."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, index=True, nullable=False)  # From OAuth token (sub claim)
    email = Column(String(255), unique=True, index=True)
    username = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("UserNote", back_populates="user", cascade="all, delete-orphan")
    profiles = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(user_id='{self.user_id}', email='{self.email}')>"


class Token(Base):
    """OAuth token storage."""
    
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False, index=True)
    access_token = Column(Text, nullable=False)
    token_type = Column(String(50), default="Bearer")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    scopes = Column(JSON)  # Store as JSON array
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_revoked = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="tokens")
    
    def __repr__(self):
        return f"<Token(user_id='{self.user_id}', expires_at='{self.expires_at}')>"


class UserProfile(Base):
    """User profile data - OAuth protected."""
    
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False, unique=True, index=True)
    name = Column(String(255))
    bio = Column(Text)
    avatar_url = Column(String(500))
    preferences = Column(JSON)  # Store user preferences as JSON
    extra_data = Column(JSON)  # Additional metadata (renamed from 'metadata')
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    version = Column(Integer, default=1)
    
    # Relationships
    user = relationship("User", back_populates="profiles")
    
    def __repr__(self):
        return f"<UserProfile(user_id='{self.user_id}', name='{self.name}')>"


class UserNote(Base):
    """User notes - OAuth protected, user-specific data."""
    
    __tablename__ = "user_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False, index=True)
    title = Column(String(500))
    content = Column(Text, nullable=False)
    tags = Column(JSON)  # Array of tags
    is_pinned = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="notes")
    
    def __repr__(self):
        return f"<UserNote(id={self.id}, user_id='{self.user_id}', title='{self.title}')>"


class APILog(Base):
    """API request logs for monitoring and debugging."""
    
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)
    request_data = Column(JSON)
    response_data = Column(JSON)
    duration_ms = Column(Integer)
    error_message = Column(Text)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    def __repr__(self):
        return f"<APILog(endpoint='{self.endpoint}', status={self.status_code})>"
