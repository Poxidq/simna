import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
from frontend.components.notes import (
    render_notes_list,
    render_note_detail,
    render_create_note_form,
    contains_russian
)

@pytest.fixture
def mock_session_state():
    with patch('streamlit.session_state') as mock:
        yield mock

@pytest.fixture
def mock_streamlit():
    with patch('streamlit') as mock:
        yield mock

def test_contains_russian():
    assert contains_russian("Привет мир") == True
    assert contains_russian("Hello world") == False
    assert contains_russian("") == False
    assert contains_russian(None) == False

def test_render_notes_list(mock_streamlit, mock_session_state):
    # Mock notes data
    notes = [
        {
            "id": 1,
            "title": "Test Note",
            "content": "This is a test note",
            "is_translated": False
        }
    ]
    
    # Mock streamlit functions
    mock_streamlit.columns.return_value = [MagicMock(), MagicMock()]
    mock_streamlit.button.return_value = False
    
    # Test rendering
    render_notes_list(notes)
    
    # Verify streamlit calls
    mock_streamlit.markdown.assert_called()
    mock_streamlit.columns.assert_called()

def test_render_note_detail(mock_streamlit, mock_session_state):
    # Mock note data
    note = {
        "id": 1,
        "title": "Test Note",
        "content": "This is a test note",
        "is_translated": False
    }
    
    # Mock streamlit functions
    mock_streamlit.columns.return_value = [MagicMock(), MagicMock()]
    mock_streamlit.button.return_value = False
    
    # Test rendering
    render_note_detail(note)
    
    # Verify streamlit calls
    mock_streamlit.markdown.assert_called()
    mock_streamlit.columns.assert_called()

def test_render_create_note_form(mock_streamlit, mock_session_state):
    # Mock streamlit functions
    mock_streamlit.form.return_value.__enter__.return_value = MagicMock()
    mock_streamlit.form_submit_button.return_value = False
    
    # Test rendering
    result = render_create_note_form()
    
    # Verify result
    assert result == False
    
    # Verify streamlit calls
    mock_streamlit.form.assert_called()
    mock_streamlit.form_submit_button.assert_called() 