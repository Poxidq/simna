"""
Database connection and session handling.

This module provides functions and classes for database connection and session management.
"""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings

# Create SQLite database engine
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session.

    This function provides a database session context manager,
    ensuring the session is closed after use.

    Yields:
        Session: SQLAlchemy database session

    Example:
        ```
        from backend.app.db.database import get_db

        # Using as a FastAPI dependency
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def atomic_transaction(db: Session) -> Generator[Session, None, None]:
    """
    Context manager for atomic database transactions.

    This ensures that database operations are atomic - either all operations
    succeed or all fail and are rolled back.

    Args:
        db (Session): SQLAlchemy database session

    Yields:
        Session: The same database session

    Example:
        ```
        from backend.app.db.database import atomic_transaction, get_db

        db = next(get_db())
        with atomic_transaction(db) as tx:
            tx.add(item1)
            tx.add(item2)
            # If any operation fails, all changes will be rolled back
        ```
    """
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise 