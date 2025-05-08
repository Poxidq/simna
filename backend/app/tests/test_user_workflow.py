"""
Test user workflow.

This module contains end-to-end tests for the complete user journey through the application.
"""
import pytest
from fastapi import status
from unittest.mock import patch

from backend.app.services.translation import translate_text


class TestUserWorkflow:
    """Test the complete user workflow from registration to note management."""

    def test_complete_user_journey(self, client):
        """
        Test the complete user journey through the application:
        - Register a new account
        - Login
        - Create a note
        - Edit the note
        - Delete the note
        - Create a new note with Russian content
        - Translate the note
        """
        # Step 1: Register a new user
        registration_data = {
            "username": "workflowuser",
            "email": "workflow@example.com",
            "password": "SecurePassword123"
        }
        
        register_response = client.post(
            "/api/v1/auth/register", 
            json=registration_data
        )
        
        assert register_response.status_code == status.HTTP_201_CREATED
        user_data = register_response.json()
        assert user_data["username"] == registration_data["username"]
        assert user_data["email"] == registration_data["email"]
        
        # Step 2: Login with the new user
        login_data = {
            "username": registration_data["username"],
            "password": registration_data["password"]
        }
        
        login_response = client.post(
            "/api/v1/auth/login", 
            json=login_data
        )
        
        assert login_response.status_code == status.HTTP_200_OK
        token_data = login_response.json()
        assert "access_token" in token_data
        
        # Set up authorization header for subsequent requests
        auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        
        # Step 3: Verify user can access their profile
        me_response = client.get(
            "/api/v1/auth/me", 
            headers=auth_headers
        )
        
        assert me_response.status_code == status.HTTP_200_OK
        user_profile = me_response.json()
        assert user_profile["username"] == registration_data["username"]
        
        # Step 4: Create a note
        note_data = {
            "title": "My First Note",
            "content": "This is the content of my first note. It will be edited later."
        }
        
        create_note_response = client.post(
            "/api/v1/notes", 
            json=note_data,
            headers=auth_headers
        )
        
        assert create_note_response.status_code == status.HTTP_201_CREATED
        note = create_note_response.json()
        assert note["title"] == note_data["title"]
        assert note["content"] == note_data["content"]
        assert "id" in note
        note_id = note["id"]
        
        # Step 5: Get the list of notes to verify the note was created
        notes_response = client.get(
            "/api/v1/notes", 
            headers=auth_headers
        )
        
        assert notes_response.status_code == status.HTTP_200_OK
        notes = notes_response.json()
        assert len(notes) == 1
        assert notes[0]["id"] == note_id
        
        # Step 6: Edit the note
        updated_note_data = {
            "title": "My Updated Note",
            "content": "This note has been updated with new content."
        }
        
        update_note_response = client.put(
            f"/api/v1/notes/{note_id}",
            json=updated_note_data,
            headers=auth_headers
        )
        
        assert update_note_response.status_code == status.HTTP_200_OK
        updated_note = update_note_response.json()
        assert updated_note["title"] == updated_note_data["title"]
        assert updated_note["content"] == updated_note_data["content"]
        
        # Step 7: Delete the note
        delete_response = client.delete(
            f"/api/v1/notes/{note_id}",
            headers=auth_headers
        )
        
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Step 8: Verify the note was deleted
        notes_response = client.get(
            "/api/v1/notes", 
            headers=auth_headers
        )
        
        assert notes_response.status_code == status.HTTP_200_OK
        notes = notes_response.json()
        assert len(notes) == 0
        
        # Step 9: Create a new note with Russian content for translation
        russian_note_data = {
            "title": "Русская заметка",
            "content": "Это заметка на русском языке, которую мы переведем на английский."
        }
        
        create_note_response = client.post(
            "/api/v1/notes", 
            json=russian_note_data,
            headers=auth_headers
        )
        
        assert create_note_response.status_code == status.HTTP_201_CREATED
        russian_note = create_note_response.json()
        assert russian_note["title"] == russian_note_data["title"]
        assert russian_note["content"] == russian_note_data["content"]
        assert "id" in russian_note
        russian_note_id = russian_note["id"]
        
        # Step 10: Translate the note
        # We need to patch the translate_text function to mock the translation
        async def mock_translate_func(text, source_lang="ru", target_lang="en", _mock_response=None):
            """Mock translation function for testing."""
            if "русском языке" in text:
                return {
                    "translated_text": "This is a note in Russian language that we will translate to English.",
                    "original_text": text,
                    "source_language": source_lang,
                    "target_language": target_lang
                }
            return {
                "translated_text": f"[Translated] {text}",
                "original_text": text,
                "source_language": source_lang,
                "target_language": target_lang
            }
        
        with patch("backend.app.api.endpoints.notes.translate_text", mock_translate_func):
            translate_response = client.post(
                f"/api/v1/notes/{russian_note_id}/translate",
                headers=auth_headers
            )
            
            assert translate_response.status_code == status.HTTP_200_OK
            translated_note = translate_response.json()
            assert translated_note["is_translated"] is True
            assert translated_note["original_content"] == russian_note_data["content"]
            assert "This is a note in Russian language" in translated_note["content"]
        
        # Step 11: Verify the translation was saved to the database
        get_note_response = client.get(
            f"/api/v1/notes/{russian_note_id}",
            headers=auth_headers
        )
        
        assert get_note_response.status_code == status.HTTP_200_OK
        retrieved_note = get_note_response.json()
        assert retrieved_note["is_translated"] is True
        assert retrieved_note["original_content"] == russian_note_data["content"]
        
        # Step 12: Clean up - Delete the translated note
        delete_response = client.delete(
            f"/api/v1/notes/{russian_note_id}",
            headers=auth_headers
        )
        
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT 