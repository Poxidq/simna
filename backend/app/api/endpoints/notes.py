"""
Notes API endpoints.

This module contains endpoints for note management and translation.
"""
from typing import Any, List, cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.schemas import (
    NoteCreate, NoteResponse, NoteUpdate, TranslationRequest, TranslationResponse
)
from backend.app.core.security import get_current_user
from backend.app.db.database import atomic_transaction, get_db
from backend.app.db.models import Note, User
from backend.app.services.translation import translate_text

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=List[NoteResponse])
async def get_notes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all notes for the current user.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List[NoteResponse]: List of user's notes
    """
    notes = db.query(Note).filter(
        Note.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return notes


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_in: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new note.

    Args:
        note_in: Note data to create
        db: Database session
        current_user: Current authenticated user

    Returns:
        NoteResponse: Newly created note
    """
    with atomic_transaction(db) as tx:
        db_note = Note(
            title=note_in.title,
            content=note_in.content,
            user_id=current_user.id
        )
        tx.add(db_note)
        tx.commit()
        tx.refresh(db_note)
    
    return db_note


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific note by ID.

    Args:
        note_id: ID of the note to retrieve
        db: Database session
        current_user: Current authenticated user

    Returns:
        NoteResponse: Note data

    Raises:
        HTTPException: If note not found or not owned by user
    """
    db_note = db.query(Note).filter(
        Note.id == note_id, 
        Note.user_id == current_user.id
    ).first()
    
    if db_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    return db_note


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_in: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update a note.

    Args:
        note_id: ID of the note to update
        note_in: Updated note data
        db: Database session
        current_user: Current authenticated user

    Returns:
        NoteResponse: Updated note data

    Raises:
        HTTPException: If note not found or not owned by user
    """
    db_note = db.query(Note).filter(
        Note.id == note_id, 
        Note.user_id == current_user.id
    ).first()
    
    if db_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Update only provided fields
    update_data = note_in.model_dump(exclude_unset=True)
    
    with atomic_transaction(db) as tx:
        for key, value in update_data.items():
            setattr(db_note, key, value)
        
        # Reset translation status if content was updated
        if "content" in update_data:
            # Use setattr instead of direct assignment to work around type issues
            setattr(db_note, "is_translated", False)
            setattr(db_note, "original_content", None)
        
        tx.commit()
        tx.refresh(db_note)
    
    return db_note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a note.

    Args:
        note_id: ID of the note to delete
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If note not found or not owned by user
    """
    db_note = db.query(Note).filter(
        Note.id == note_id, 
        Note.user_id == current_user.id
    ).first()
    
    if db_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    with atomic_transaction(db) as tx:
        tx.delete(db_note)
        tx.commit()


@router.post("/{note_id}/translate", response_model=NoteResponse)
async def translate_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Translate a note from Russian to English.

    Args:
        note_id: ID of the note to translate
        db: Database session
        current_user: Current authenticated user

    Returns:
        NoteResponse: Translated note data

    Raises:
        HTTPException: If note not found or not owned by user
    """
    db_note = db.query(Note).filter(
        Note.id == note_id, 
        Note.user_id == current_user.id
    ).first()
    
    if db_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Only translate if not already translated
    if not db_note.is_translated:
        # Cast to string to satisfy mypy
        note_content = cast(str, db_note.content)
        # Translate the note content
        translation_result = await translate_text(note_content)
        
        with atomic_transaction(db) as tx:
            # Store original content and use setattr to work around type issues
            setattr(db_note, "original_content", db_note.content)
            setattr(db_note, "content", translation_result["translated_text"])
            setattr(db_note, "is_translated", True)
            
            tx.commit()
            tx.refresh(db_note)
    
    return db_note 