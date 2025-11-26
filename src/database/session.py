"""
Database session management for MCP server.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from src.config import config
from src.models import Base
from src.utils.logging import get_logger

logger = get_logger(__name__)


# Create engine
engine = create_engine(
    config.DATABASE_URL,
    echo=config.DATABASE_ECHO,
    pool_pre_ping=True  # Verify connections before using
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """
    Initialize database - create all tables.
    Should be called at application startup.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Ensures proper cleanup even if exceptions occur.
    
    Usage:
        with get_db_session() as db:
            # use db
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session_factory():
    """
    Get a database session factory function.
    
    Returns:
        Callable that returns a database session context manager
    """
    return get_db_session
