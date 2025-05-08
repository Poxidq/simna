"""
Test frontend workflow.

This module contains tests for the frontend Streamlit application workflow.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Make sure the module path is correct
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import streamlit for mock
import streamlit as st

# Import the modules to test
from frontend.services.auth_service import login, register, get_current_user
from frontend.services.notes_service import get_notes, create_note, update_note, delete_note, translate_note
from frontend.app import main


@pytest.fixture
def mock_streamlit():
    """Set up Streamlit mocks."""
    # Create mock session state
    mock_session_state = {}
    
    # Setup the st.session_state mock using a dict as a proxy
    class SessionStateProxy(dict):
        def __setitem__(self, key, value):
            mock_session_state[key] = value
        
        def __getitem__(self, key):
            return mock_session_state.get(key)
            
        def get(self, key, default=None):
            return mock_session_state.get(key, default)
            
        def __contains__(self, key):
            return key in mock_session_state
            
        def __delitem__(self, key):
            if key in mock_session_state:
                del mock_session_state[key]
    
    # Patch all required Streamlit functions
    with patch('streamlit.session_state', SessionStateProxy()), \
         patch('streamlit.set_page_config'), \
         patch('streamlit.title'), \
         patch('streamlit.sidebar'), \
         patch('streamlit.form'), \
         patch('streamlit.text_input', return_value=None), \
         patch('streamlit.form_submit_button', return_value=False), \
         patch('streamlit.error'), \
         patch('streamlit.success'), \
         patch('streamlit.spinner'), \
         patch('streamlit.markdown'), \
         patch('streamlit.rerun') as mock_rerun, \
         patch('streamlit.container', return_value=MagicMock()), \
         patch('streamlit.columns', return_value=[MagicMock(), MagicMock(), MagicMock()]):
        
        # Create a reference to the session state for test assertions
        session_state = SessionStateProxy()
        
        yield {
            'session_state': session_state,
            'rerun': mock_rerun
        }


@pytest.fixture
def mock_api_requests():
    """Mock all API request functions."""
    with patch('frontend.services.api.api_request') as mock_request:
        # Configuration for different API endpoints
        async def mock_api_response(*args, **kwargs):
            method, path = args[0], args[1]
            
            # Login endpoint
            if method == "POST" and path == "/auth/login":
                return {
                    "access_token": "mock_token_12345",
                    "token_type": "bearer"
                }
            
            # Register endpoint
            elif method == "POST" and path == "/auth/register":
                return {
                    "id": 1,
                    "username": "testuser",
                    "email": "test@example.com",
                    "is_active": True,
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00"
                }
            
            # User info endpoint
            elif method == "GET" and path == "/auth/me":
                return {
                    "id": 1,
                    "username": "testuser",
                    "email": "test@example.com",
                    "is_active": True,
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00"
                }
            
            # Notes list endpoint
            elif method == "GET" and path == "/notes":
                return [
                    {
                        "id": 1,
                        "title": "Test Note",
                        "content": "This is a test note content",
                        "is_translated": False,
                        "original_content": None,
                        "user_id": 1,
                        "created_at": "2023-01-01T00:00:00",
                        "updated_at": "2023-01-01T00:00:00"
                    }
                ]
            
            # Create note endpoint
            elif method == "POST" and path == "/notes":
                return {
                    "id": len(mock_notes) + 1,
                    "title": kwargs.get("data", {}).get("title", "New Note"),
                    "content": kwargs.get("data", {}).get("content", "Note content"),
                    "is_translated": False,
                    "original_content": None,
                    "user_id": 1,
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00"
                }
            
            # Update note endpoint
            elif method == "PUT" and "/notes/" in path:
                note_id = int(path.split("/")[-1])
                return {
                    "id": note_id,
                    "title": kwargs.get("data", {}).get("title", "Updated Note"),
                    "content": kwargs.get("data", {}).get("content", "Updated content"),
                    "is_translated": False,
                    "original_content": None,
                    "user_id": 1,
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00"
                }
            
            # Translate note endpoint
            elif method == "POST" and "/notes/" in path and "/translate" in path:
                note_id = int(path.split("/")[-2])
                return {
                    "id": note_id,
                    "title": "Translated Note",
                    "content": "This is the translated content",
                    "is_translated": True,
                    "original_content": "Это оригинальное содержание",
                    "user_id": 1,
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00"
                }
            
            # Delete note endpoint
            elif method == "DELETE" and "/notes/" in path:
                return None
            
            return None
        
        # Mock notes data for testing
        mock_notes = []
        
        # Configure the mock
        mock_request.side_effect = mock_api_response
        yield mock_request


class TestFrontendWorkflow:
    """Test the complete frontend workflow."""
    
    @pytest.mark.asyncio
    async def test_user_registration(self, mock_streamlit, mock_api_requests):
        """Test user registration process."""
        # Simulate filling the registration form
        with patch('frontend.components.auth.st.session_state', {
            'reg_username': 'testuser',
            'reg_email': 'test@example.com',
            'reg_password': 'SecurePassword123',
            '_register_form_submitted': True
        }):
            # Call the registration function
            result = await register('testuser', 'test@example.com', 'SecurePassword123')
            
            # Verify the API was called correctly
            mock_api_requests.assert_called_once()
            args, kwargs = mock_api_requests.call_args
            assert args[0] == "POST"
            assert args[1] == "/auth/register"
            assert kwargs["data"] == {
                "username": "testuser", 
                "email": "test@example.com", 
                "password": "SecurePassword123"
            }
            
            # Verify the result
            assert result is True
    
    @pytest.mark.asyncio
    async def test_user_login(self, mock_streamlit, mock_api_requests):
        """Test user login process."""
        # Simulate filling the login form
        with patch('frontend.services.auth_service.st.session_state', {}):
            # Call the login function
            result, _ = await login('testuser', 'SecurePassword123')
            
            # Verify the API was called correctly
            args, kwargs = mock_api_requests.call_args
            assert args[0] == "POST"
            assert args[1] == "/auth/login"
            assert kwargs["data"] == {
                "username": "testuser", 
                "password": "SecurePassword123"
            }
            
            # Verify the result
            assert result is True
    
    @pytest.mark.asyncio
    async def test_note_creation(self, mock_streamlit, mock_api_requests):
        """Test note creation process."""
        # Set up session state with a token
        with patch('frontend.services.notes_service.st.session_state', {'token': 'mock_token_12345'}):
            # Call the create note function
            result = await create_note("Test Note", "This is a test note content")
            
            # Verify the API was called correctly
            args, kwargs = mock_api_requests.call_args
            assert args[0] == "POST"
            assert args[1] == "/notes"
            assert kwargs["data"] == {
                "title": "Test Note",
                "content": "This is a test note content"
            }
            assert kwargs["token"] == "mock_token_12345"
            
            # Verify the result
            assert result is True
    
    @pytest.mark.asyncio
    async def test_note_update(self, mock_streamlit, mock_api_requests):
        """Test note update process."""
        # Set up session state with a token
        with patch('frontend.services.notes_service.st.session_state', {'token': 'mock_token_12345'}):
            # Call the update note function
            result = await update_note(1, "Updated Note", "Updated note content")
            
            # Verify the API was called correctly
            args, kwargs = mock_api_requests.call_args
            assert args[0] == "PUT"
            assert args[1] == "/notes/1"
            assert kwargs["data"] == {
                "title": "Updated Note",
                "content": "Updated note content"
            }
            assert kwargs["token"] == "mock_token_12345"
            
            # Verify the result
            assert result is True
    
    @pytest.mark.asyncio
    async def test_note_deletion(self, mock_streamlit, mock_api_requests):
        """Test note deletion process."""
        # Set up session state with a token
        with patch('frontend.services.notes_service.st.session_state', {'token': 'mock_token_12345'}):
            # Call the delete note function
            result = await delete_note(1)
            
            # Verify the API was called correctly
            args, kwargs = mock_api_requests.call_args
            assert args[0] == "DELETE"
            assert args[1] == "/notes/1"
            assert kwargs["token"] == "mock_token_12345"
            
            # Verify the result
            assert result is True
    
    @pytest.mark.asyncio
    async def test_note_translation(self, mock_streamlit, mock_api_requests):
        """Test note translation process."""
        # Set up session state with a token
        with patch('frontend.services.notes_service.st.session_state', {'token': 'mock_token_12345'}):
            # Call the translate note function
            result = await translate_note(1)
            
            # Verify the API was called correctly
            args, kwargs = mock_api_requests.call_args
            assert args[0] == "POST"
            assert args[1] == "/notes/1/translate"
            assert kwargs["token"] == "mock_token_12345"
            
            # Verify the result
            assert result is True
    
    @pytest.mark.asyncio
    async def test_complete_frontend_workflow(self, mock_streamlit, mock_api_requests):
        """Test the complete frontend workflow."""
        # 1. Register a new user
        with patch('frontend.services.auth_service.st.session_state', {}):
            reg_result = await register('testuser', 'test@example.com', 'SecurePassword123')
            assert reg_result is True
        
        # 2. Login with the new user
        with patch('frontend.services.auth_service.st.session_state', {}) as session_state:
            login_result, _ = await login('testuser', 'SecurePassword123')
            assert login_result is True
            
            # Verify token was stored in session state
            mock_api_requests.assert_called()  # Reset call count
        
        # 3. Create a note
        with patch('frontend.services.notes_service.st.session_state', {'token': 'mock_token_12345'}):
            create_result = await create_note("Test Note", "This is a test note content")
            assert create_result is True
        
        # 4. Update the note
        with patch('frontend.services.notes_service.st.session_state', {'token': 'mock_token_12345'}):
            update_result = await update_note(1, "Updated Note", "Updated note content")
            assert update_result is True
        
        # 5. Delete the note
        with patch('frontend.services.notes_service.st.session_state', {'token': 'mock_token_12345'}):
            delete_result = await delete_note(1)
            assert delete_result is True
        
        # 6. Create a new note with Russian content
        with patch('frontend.services.notes_service.st.session_state', {'token': 'mock_token_12345'}):
            create_russian_result = await create_note(
                "Русская заметка", 
                "Это заметка на русском языке, которую мы переведем."
            )
            assert create_russian_result is True
        
        # 7. Translate the note
        with patch('frontend.services.notes_service.st.session_state', {'token': 'mock_token_12345'}):
            translate_result = await translate_note(2)  # Using ID 2 for the second note
            assert translate_result is True
            
            # Verify the translation API was called
            args, kwargs = mock_api_requests.call_args
            assert args[0] == "POST"
            assert "/translate" in args[1] 