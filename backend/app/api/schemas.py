"""
API Schemas.

This module contains Pydantic models for request and response validation.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, validator


# Token Schemas
class Token(BaseModel):
    """Schema for access token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data."""

    user_id: Optional[int] = None


# User Schemas
class UserBase(BaseModel):
    """Base schema for user data."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user creation."""

    password: str = Field(..., min_length=8)

    @validator("password")
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config for ORM mode."""

        from_attributes = True


# Note Schemas
class NoteBase(BaseModel):
    """Base schema for note data."""

    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)


class NoteCreate(NoteBase):
    """Schema for note creation."""

    pass


class NoteUpdate(BaseModel):
    """Schema for note update."""

    title: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=1)


class NoteResponse(NoteBase):
    """Schema for note response."""

    id: int
    is_translated: bool
    original_content: Optional[str] = None
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config for ORM mode."""

        from_attributes = True


# Translation Schema
class TranslationRequest(BaseModel):
    """Schema for translation request."""

    text: str = Field(..., min_length=1)
    source_language: str = "ru"
    target_language: str = "en"


class TranslationResponse(BaseModel):
    """Schema for translation response."""

    translated_text: str
    original_text: str
    source_language: str
    target_language: str 