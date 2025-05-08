"""
Tests for notes endpoints.

This module contains tests for note creation, retrieval, update, deletion, and translation.
"""
import pytest
from fastapi import status


def test_get_notes(authorized_client, test_notes):
    """Test getting all notes for the current user."""
    # Send request to get all notes
    response = authorized_client.get("/api/v1/notes")
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(test_notes)
    assert {note["id"] for note in data} == {note.id for note in test_notes}


def test_get_notes_unauthorized(client):
    """Test getting notes without authentication."""
    # Send request without authentication
    response = client.get("/api/v1/notes")
    
    # Assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_note(authorized_client, db_session):
    """Test creating a new note."""
    # Prepare note data
    note_data = {
        "title": "New Test Note",
        "content": "This is a new test note content."
    }
    
    # Send request to create note
    response = authorized_client.post("/api/v1/notes", json=note_data)
    
    # Assert response
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == note_data["title"]
    assert data["content"] == note_data["content"]
    assert not data["is_translated"]
    assert data["original_content"] is None
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data
    assert "updated_at" in data
    
    # Check that the note was created in the database
    from backend.app.db.models import Note
    db_note = db_session.query(Note).filter(Note.id == data["id"]).first()
    assert db_note is not None
    assert db_note.title == note_data["title"]
    assert db_note.content == note_data["content"]


def test_create_note_unauthorized(client):
    """Test creating a note without authentication."""
    # Prepare note data
    note_data = {
        "title": "New Test Note",
        "content": "This is a new test note content."
    }
    
    # Send request without authentication
    response = client.post("/api/v1/notes", json=note_data)
    
    # Assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_note(authorized_client, test_notes):
    """Test getting a specific note by ID."""
    # Get the first test note
    test_note = test_notes[0]
    
    # Send request to get the note
    response = authorized_client.get(f"/api/v1/notes/{test_note.id}")
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_note.id
    assert data["title"] == test_note.title
    assert data["content"] == test_note.content
    assert data["user_id"] == test_note.user_id


def test_get_note_not_found(authorized_client):
    """Test getting a non-existent note."""
    # Send request with non-existent ID
    response = authorized_client.get("/api/v1/notes/9999")
    
    # Assert response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Note not found" in response.json()["detail"]


def test_get_note_unauthorized(client, test_notes):
    """Test getting a note without authentication."""
    # Get the first test note
    test_note = test_notes[0]
    
    # Send request without authentication
    response = client.get(f"/api/v1/notes/{test_note.id}")
    
    # Assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_note(authorized_client, test_notes, db_session):
    """Test updating a note."""
    # Get the first test note
    test_note = test_notes[0]
    
    # Prepare update data
    update_data = {
        "title": "Updated Title",
        "content": "Updated content for testing."
    }
    
    # Send request to update the note
    response = authorized_client.put(f"/api/v1/notes/{test_note.id}", json=update_data)
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_note.id
    assert data["title"] == update_data["title"]
    assert data["content"] == update_data["content"]
    assert not data["is_translated"]  # Should reset translation status
    assert data["original_content"] is None
    
    # Check that the note was updated in the database
    from backend.app.db.models import Note
    db_note = db_session.query(Note).filter(Note.id == test_note.id).first()
    assert db_note.title == update_data["title"]
    assert db_note.content == update_data["content"]


def test_update_note_partial(authorized_client, test_notes, db_session):
    """Test partial update of a note (only title)."""
    # Get the first test note
    test_note = test_notes[0]
    original_content = test_note.content
    
    # Prepare partial update data (only title)
    update_data = {
        "title": "Only Title Updated"
    }
    
    # Send request to update the note
    response = authorized_client.put(f"/api/v1/notes/{test_note.id}", json=update_data)
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_note.id
    assert data["title"] == update_data["title"]
    assert data["content"] == original_content  # Content should not change
    
    # Check that only the title was updated in the database
    from backend.app.db.models import Note
    db_note = db_session.query(Note).filter(Note.id == test_note.id).first()
    assert db_note.title == update_data["title"]
    assert db_note.content == original_content


def test_update_note_not_found(authorized_client):
    """Test updating a non-existent note."""
    # Prepare update data
    update_data = {
        "title": "Updated Title",
        "content": "Updated content for testing."
    }
    
    # Send request with non-existent ID
    response = authorized_client.put("/api/v1/notes/9999", json=update_data)
    
    # Assert response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Note not found" in response.json()["detail"]


def test_update_note_unauthorized(client, test_notes):
    """Test updating a note without authentication."""
    # Get the first test note
    test_note = test_notes[0]
    
    # Prepare update data
    update_data = {
        "title": "Updated Title",
        "content": "Updated content for testing."
    }
    
    # Send request without authentication
    response = client.put(f"/api/v1/notes/{test_note.id}", json=update_data)
    
    # Assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_note(authorized_client, test_notes, db_session):
    """Test deleting a note."""
    # Get the first test note
    test_note = test_notes[0]
    
    # Send request to delete the note
    response = authorized_client.delete(f"/api/v1/notes/{test_note.id}")
    
    # Assert response
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Check that the note was deleted from the database
    from backend.app.db.models import Note
    db_note = db_session.query(Note).filter(Note.id == test_note.id).first()
    assert db_note is None
    
    # Check that other notes still exist
    remaining_notes = db_session.query(Note).all()
    assert len(remaining_notes) == len(test_notes) - 1


def test_delete_note_not_found(authorized_client):
    """Test deleting a non-existent note."""
    # Send request with non-existent ID
    response = authorized_client.delete("/api/v1/notes/9999")
    
    # Assert response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Note not found" in response.json()["detail"]


def test_delete_note_unauthorized(client, test_notes):
    """Test deleting a note without authentication."""
    # Get the first test note
    test_note = test_notes[0]
    
    # Send request without authentication
    response = client.delete(f"/api/v1/notes/{test_note.id}")
    
    # Assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_translate_note(authorized_client, test_notes, db_session):
    """Test translating a note with Russian content."""
    # Get the Russian test note (third one)
    russian_note = test_notes[2]
    original_content = russian_note.content
    
    # Send request to translate the note
    response = authorized_client.post(f"/api/v1/notes/{russian_note.id}/translate")
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == russian_note.id
    assert data["is_translated"] is True
    assert data["original_content"] == original_content
    assert data["content"] is not None  # Should have some translated content
    assert data["content"] != original_content  # Content should be different after translation
    
    # Check that the note was updated in the database
    from backend.app.db.models import Note
    db_note = db_session.query(Note).filter(Note.id == russian_note.id).first()
    assert db_note.is_translated is True
    assert db_note.original_content == original_content
    assert db_note.content is not None
    assert db_note.content != original_content 