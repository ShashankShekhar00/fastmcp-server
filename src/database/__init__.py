"""
Database session management and connection handling.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

from src.models import Base

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager."""
    
    def __init__(self, database_url: str, echo: bool = False):
        """
        Initialize database connection.
        
        Args:
            database_url: SQLAlchemy database URL
            echo: Whether to echo SQL statements (for debugging)
        """
        self.database_url = database_url
        
        # SQLite specific configuration
        if database_url.startswith("sqlite"):
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=echo
            )
        else:
            # PostgreSQL or other databases
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,  # Verify connections before using
                echo=echo
            )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Database initialized: {database_url.split('@')[-1]}")  # Don't log credentials
    
    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")
    
    def drop_tables(self):
        """Drop all tables in the database. USE WITH CAUTION!"""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("Database tables dropped")
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy Session instance
        """
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope for database operations.
        
        Usage:
            with db.session_scope() as session:
                user = session.query(User).first()
        
        Yields:
            SQLAlchemy Session instance
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global database instance (initialized in main application)
db: Database = None


def init_database(database_url: str, echo: bool = False) -> Database:
    """
    Initialize the global database instance.
    
    Args:
        database_url: SQLAlchemy database URL
        echo: Whether to echo SQL statements
        
    Returns:
        Database instance
    """
    global db
    db = Database(database_url, echo)
    db.create_tables()
    return db


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to inject database session.
    
    Usage in FastAPI:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    
    Yields:
        SQLAlchemy Session instance
    """
    if db is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()
