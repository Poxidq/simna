"""
Database models for the Notes App.

This module contains SQLAlchemy ORM models that represent the database schema.
"""
from datetime import datetime
from typing import List, Optional, ClassVar, Any, TYPE_CHECKING, cast, Type

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column

# Create base class
Base = declarative_base()

# Forward references for type checking
if TYPE_CHECKING:
    from typing import List
    # Define these as strings to avoid the redefinition issue
    UserType = 'User'
    NoteType = 'Note'


class User(Base):  # type: ignore
    """User model for authentication and authorization."""

    __tablename__ = "users"
    __allow_unmapped__ = True

    # For SQLAlchemy 1.4 compatibility, we need to keep the Column syntax
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship with Note model
    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """Return string representation of User object."""
        return f"User(id={self.id}, username={self.username})"


class Note(Base):  # type: ignore
    """Note model for storing user notes."""

    __tablename__ = "notes"
    __allow_unmapped__ = True

    # For SQLAlchemy 1.4 compatibility, we need to keep the Column syntax
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    is_translated = Column(Boolean, default=False)
    original_content = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship with User model
    owner = relationship("User", back_populates="notes")

    def __repr__(self) -> str:
        """Return string representation of Note object."""
        return f"Note(id={self.id}, title={self.title}, user_id={self.user_id})" 