"""
Tests for notes translation API integration.

This module contains tests for the note translation endpoint.
"""
import json
from unittest.mock import patch

import pytest
from fastapi import HTTPException, status

from backend.app.core.config import settings
from backend.app.services.translation import translate_text


# Helper function to create mock translation - this will be used for patching
async def mock_translate_func(text, source_lang="ru", target_lang="en", _mock_response=None):
    """Mock translation function for testing."""
    return {
        "translated_text": "This is a test note in Russian language",
        "original_text": text,
        "source_language": source_lang,
        "target_language": target_lang
    }


def test_translate_note_endpoint(authorized_client, test_notes):
    """Test the note translation endpoint."""
    # Get the Russian note (third test note)
    russian_note = test_notes[2]
    
    # The original content before translation
    original_content = russian_note.content
    
    # Mock the translate_text function directly
    with patch("backend.app.api.endpoints.notes.translate_text", mock_translate_func):
        # Call the API endpoint to translate the note
        response = authorized_client.post(f"/api/v1/notes/{russian_note.id}/translate")
        
        # Assert response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify translation was successful
        assert data["is_translated"] is True
        assert data["original_content"] == original_content
        assert data["content"] == "This is a test note in Russian language"
        assert data["id"] == russian_note.id


def test_translate_note_not_found(authorized_client):
    """Test attempting to translate a non-existent note."""
    # Try to translate a non-existent note ID
    response = authorized_client.post("/api/v1/notes/9999/translate")
    
    # Assert response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Note not found" in response.json()["detail"]


def test_translate_note_unauthorized(client, test_notes):
    """Test attempting to translate a note without authentication."""
    # Get the Russian note (third test note)
    russian_note = test_notes[2]
    
    # Try to translate without authentication
    response = client.post(f"/api/v1/notes/{russian_note.id}/translate")
    
    # Assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_translate_already_translated_note(authorized_client, test_notes):
    """Test translating a note that is already translated."""
    # Get the Russian note (third test note)
    russian_note = test_notes[2]
    
    # Mock the translate_text function
    with patch("backend.app.api.endpoints.notes.translate_text", mock_translate_func):
        # First translation
        response1 = authorized_client.post(f"/api/v1/notes/{russian_note.id}/translate")
        assert response1.status_code == status.HTTP_200_OK
        
        # Second translation (should use cached translation)
        with patch("backend.app.api.endpoints.notes.translate_text") as mock_translate:
            # Second translation attempt
            response2 = authorized_client.post(f"/api/v1/notes/{russian_note.id}/translate")
            
            # Assert that translation function was not called again
            mock_translate.assert_not_called()
        
        # Verify that second translation returned the same data
        assert response2.status_code == status.HTTP_200_OK
        
        # Verify translation data is consistent
        data1 = response1.json()
        data2 = response2.json()
        assert data1["content"] == data2["content"]
        assert data1["original_content"] == data2["original_content"]


def test_translate_note_with_api_error(authorized_client, test_notes):
    """Test handling of API errors during note translation."""
    # Get the Russian note (third test note)
    russian_note = test_notes[2]
    
    # Create a mock that will simulate an API error with HTTPException
    async def mock_error_translate(*args, **kwargs):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Translation service unavailable: API Connection Error"
        )
    
    # Apply the mock
    with patch("backend.app.api.endpoints.notes.translate_text", mock_error_translate):
        # Call the API endpoint to translate the note
        response = authorized_client.post(f"/api/v1/notes/{russian_note.id}/translate")
        
        # Assert that the error is properly returned to the client
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Translation service unavailable" in response.json()["detail"]


def test_create_and_translate_note(authorized_client):
    """Test creating a new note with Russian content and then translating it."""
    # Create a note with Russian content
    note_data = {
        "title": "Test Note with Russian",
        "content": "Это новая заметка для тестирования перевода."
    }
    
    # Create the note
    create_response = authorized_client.post(
        "/api/v1/notes",
        json=note_data
    )
    
    # Assert note creation was successful
    assert create_response.status_code == status.HTTP_201_CREATED
    new_note = create_response.json()
    new_note_id = new_note["id"]
    
    # Mock the translate_text function for the translation request
    with patch("backend.app.api.endpoints.notes.translate_text", mock_translate_func):
        # Translate the note
        translate_response = authorized_client.post(f"/api/v1/notes/{new_note_id}/translate")
        
        # Assert translation was successful
        assert translate_response.status_code == status.HTTP_200_OK
        translated_note = translate_response.json()
        
        # Verify translation
        assert translated_note["is_translated"] is True
        assert translated_note["original_content"] == note_data["content"]
        assert translated_note["content"] == "This is a test note in Russian language"
        
        # Get the note to make sure the translated version persists
        get_response = authorized_client.get(f"/api/v1/notes/{new_note_id}")
        assert get_response.status_code == status.HTTP_200_OK
        retrieved_note = get_response.json()
        
        # Verify the retrieved note has the translation
        assert retrieved_note["is_translated"] is True
        assert retrieved_note["original_content"] == note_data["content"]
        assert retrieved_note["content"] == "This is a test note in Russian language"


def test_update_translated_note(authorized_client, test_notes):
    """Test updating a note after it has been translated."""
    # Get the Russian note (third test note)
    russian_note = test_notes[2]
    
    # Mock the translate_text function for first translation
    with patch("backend.app.api.endpoints.notes.translate_text", mock_translate_func):
        # First translate the note
        translate_response = authorized_client.post(f"/api/v1/notes/{russian_note.id}/translate")
        assert translate_response.status_code == status.HTTP_200_OK
        
        # Update the note
        update_data = {
            "content": "Новое содержание заметки после перевода."
        }
        
        update_response = authorized_client.put(
            f"/api/v1/notes/{russian_note.id}",
            json=update_data
        )
        
        # Assert update was successful
        assert update_response.status_code == status.HTTP_200_OK
        updated_note = update_response.json()
        
        # Verify that updating content resets translation status
        assert updated_note["is_translated"] is False
        assert updated_note["original_content"] is None
        assert updated_note["content"] == update_data["content"]
        
        # Define a different mock for second translation
        async def mock_new_translate(*args, **kwargs):
            return {
                "translated_text": "New note content after translation.",
                "original_text": args[0],
                "source_language": "ru",
                "target_language": "en"
            }
        
        # Mock the translate_text function for second translation
        with patch("backend.app.api.endpoints.notes.translate_text", mock_new_translate):
            # Translate the updated note
            new_translate_response = authorized_client.post(f"/api/v1/notes/{russian_note.id}/translate")
            assert new_translate_response.status_code == status.HTTP_200_OK
            newly_translated_note = new_translate_response.json()
            
            # Verify new translation
            assert newly_translated_note["is_translated"] is True
            assert newly_translated_note["original_content"] == update_data["content"]
            assert newly_translated_note["content"] == "New note content after translation." 