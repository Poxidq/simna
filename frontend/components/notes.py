"""
Notes UI components.

This module contains UI components for displaying and interacting with notes.
"""
import asyncio
import json
import logging
import os
import time
from functools import wraps
from typing import Any, Dict, List, Optional

import httpx
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG_MODE", "False").lower() == "true" else logging.INFO)
logger = logging.getLogger(__name__)

# Import services at the module level
from frontend.services import notes_service
from frontend.services.api import api_request

# State keys for better organization
STATE_KEYS = {
    "TRANSLATION": {
        "IN_PROGRESS": "_translation_in_progress",
        "COMPLETE": "_translation_complete",
        "ERROR": "_translation_error",
        "REQUESTED": "_translate_note_requested",
    },
    "PREVIEW": {
        "VISIBLE": "_show_live_translation",
        "LOADING": "_translation_preview_loading",
        "RESULT": "_translation_preview_result",
        "ERROR": "_translation_preview_error",
    }
}

def check_auth(func):
    """Decorator to check authentication before executing a function."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get token from session state
        token = st.session_state.get("token")
        if not token:
            logger.error("Operation attempted without auth token")
            # Redirect to login
            st.session_state["show_login"] = True
            return None
        
        # Add token to kwargs and call function
        kwargs["token"] = token
        return await func(*args, **kwargs)
    return wrapper

@check_auth
async def get_translation_preview(note_id: Optional[int] = None, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a translation preview for a note.
    
    Args:
        note_id: ID of the note to translate
        token: Authentication token
        
    Returns:
        Dict containing translation result or error
    """
    result = {
        "success": False,
        "translated_text": None,
        "error": None
    }
    
    try:
        # Validate note ID
        if not note_id:
            note_id = st.session_state.get("current_note", {}).get("id")
            
        if not note_id:
            logger.error("No note ID available for translation preview")
            result["error"] = "No note selected"
            return result
        
        # Get API base URL from environment or use default
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
        
        # Use the correct endpoint with preview parameter
        url = f"{api_base_url}/notes/{note_id}/translate?preview=true"
        
        # Set up headers with authorization
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token
        }
        
        logger.info(f"Making translation preview request to: {url}")
        
        # Make async request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers)
            
            if response.status_code == 401:
                # Token is invalid or expired
                logger.error("Authentication failed during translation preview")
                result["error"] = "Authentication failed. Please log in again."
                # Clear token and redirect to login
                if "token" in st.session_state:
                    del st.session_state["token"]
                if "user" in st.session_state:
                    del st.session_state["user"]
                st.session_state["show_login"] = True
                return result
                
            if response.status_code == 200:
                # Parse the response
                response_data = response.json()
                logger.info(f"Translation preview successful, received response with fields: {list(response_data.keys())}")
                
                # Get the translated text from the response
                if "translated_text" in response_data:
                    result["translated_text"] = response_data["translated_text"]
                    result["success"] = True
                else:
                    logger.error("Translation preview response missing translated_text field")
                    result["error"] = "Invalid response from translation service"
            else:
                error_message = f"Translation preview failed with status code: {response.status_code}"
                logger.error(error_message)
                try:
                    error_detail = response.json()
                    logger.error(f"Error details: {error_detail}")
                    result["error"] = error_detail.get("detail", error_message)
                except:
                    error_detail = response.text[:100]
                    logger.error(f"Error response: {error_detail}")
                    result["error"] = error_message
    except Exception as e:
        error_message = f"Error during translation preview: {str(e)}"
        logger.exception(error_message)
        result["error"] = error_message
            
    return result

@check_auth
async def translate_note_async(note_id: Optional[int] = None, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Translate a note and save the result.
    
    Args:
        note_id: ID of the note to translate
        token: Authentication token
        
    Returns:
        Dict containing translation result or error
    """
    result = {
        "success": False,
        "note": None,
        "error": None
    }
    
    try:
        # Validate note ID
        if not note_id:
            note_id = st.session_state.get("current_note", {}).get("id")
            
        if not note_id:
            logger.error("No note ID available for translation")
            result["error"] = "No note selected"
            return result
        
        # Get API base URL from environment or use default
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
        
        # Call translation endpoint (without preview param for full translation)
        url = f"{api_base_url}/notes/{note_id}/translate"
        
        # Set up headers with authorization
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token
        }
        
        logger.info(f"Making full translation request to: {url}")
        
        # Make async request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers)
            
            if response.status_code == 401:
                # Token is invalid or expired
                logger.error("Authentication failed during translation")
                result["error"] = "Authentication failed. Please log in again."
                # Clear token and redirect to login
                if "token" in st.session_state:
                    del st.session_state["token"]
                if "user" in st.session_state:
                    del st.session_state["user"]
                st.session_state["show_login"] = True
                return result
                
            if response.status_code == 200:
                # Parse the response
                response_data = response.json()
                logger.info(f"Translation successful, received response with fields: {list(response_data.keys())}")
                
                # Return the updated note
                result["note"] = response_data
                result["success"] = True
            else:
                error_message = f"Translation failed with status code: {response.status_code}"
                logger.error(error_message)
                try:
                    error_detail = response.json()
                    logger.error(f"Error details: {error_detail}")
                    result["error"] = error_detail.get("detail", error_message)
                except:
                    error_detail = response.text[:100]
                    logger.error(f"Error response: {error_detail}")
                    result["error"] = error_message
    except Exception as e:
        error_message = f"Error during translation: {str(e)}"
        logger.exception(error_message)
        result["error"] = error_message
            
    return result

@check_auth
async def refresh_notes_async(token: Optional[str] = None) -> Dict[str, Any]:
    """
    Refresh the notes list.
    
    Args:
        token: Authentication token
        
    Returns:
        Dict containing notes or error
    """
    result = {
        "success": False,
        "notes": [],
        "error": None
    }
    
    try:
        # Get API base URL from environment or use default
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
        
        # Notes API endpoint
        url = f"{api_base_url}/notes"
        
        # Set up headers with authorization
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token
        }
        
        logger.info(f"Refreshing notes from: {url}")
        
        # Make async request
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 401:
                # Token is invalid or expired
                logger.error("Authentication failed while refreshing notes")
                result["error"] = "Authentication failed. Please log in again."
                # Clear token and redirect to login
                if "token" in st.session_state:
                    del st.session_state["token"]
                if "user" in st.session_state:
                    del st.session_state["user"]
                st.session_state["show_login"] = True
                return result
                
            if response.status_code == 200:
                # Parse the response
                notes = response.json()
                logger.info(f"Successfully fetched {len(notes)} notes")
                
                # Update result
                result["notes"] = notes
                result["success"] = True
            else:
                error_message = f"Failed to refresh notes with status code: {response.status_code}"
                logger.error(error_message)
                try:
                    error_detail = response.json()
                    logger.error(f"Error details: {error_detail}")
                    result["error"] = error_detail.get("detail", error_message)
                except:
                    error_detail = response.text[:100]
                    logger.error(f"Error response: {error_detail}")
                    result["error"] = error_message
    except Exception as e:
        error_message = f"Error refreshing notes: {str(e)}"
        logger.exception(error_message)
        result["error"] = error_message
            
    return result

def contains_russian(text: Optional[str]) -> bool:
    """
    Check if a text contains Russian characters.
    
    Args:
        text: Text to check
        
    Returns:
        bool: True if text contains Russian characters, False otherwise
    """
    if not text:
        return False
        
    # Russian Unicode range: U+0400 to U+04FF
    for char in text:
        if 0x0400 <= ord(char) <= 0x04FF:
            return True
    return False

def render_notes_list(notes: List[Dict[str, Any]]) -> None:
    """Render the list of notes."""
    # Header with button to create a new note
    col1, col2 = st.columns([8, 2])
    
    with col1:
        st.markdown("## Your Notes")
    
    with col2:
        if st.button("✏️ New Note", key="new_note_btn", use_container_width=True):
            st.session_state._create_note = True
            st.rerun()
    
    # If no notes, show message
    if not notes:
        st.info("You don't have any notes yet. Create one to get started!")
        return
    
    # Display each note as a card
    for i, note in enumerate(notes):
        note_id = note.get("id")
        title = note.get("title", "Untitled")
        content = note.get("content", "")
        is_translated = note.get("is_translated", False)
        
        # Truncate content for display
        preview = content[:100] + "..." if len(content) > 100 else content
        
        # Check if the note contains Russian text
        has_russian = contains_russian(content)
        
        # Create a card for the note
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"### {title}")
                st.markdown(preview)
                
                # Display translated badge or translation button
                if is_translated:
                    st.markdown("<span style='background-color: rgba(255, 107, 0, 0.1); color: var(--primary-color); padding: 2px 6px; border-radius: 3px; font-size: 0.8rem;'>🔄 Translated</span>", unsafe_allow_html=True)
                elif has_russian:
                    # Show translation button for notes with Russian text
                    if st.button("🔄 Translate", key=f"translate_note_{i}", type="secondary", help="Translate Russian text to English"):
                        # Store the note to translate and set translation flag
                        st.session_state.current_note = note
                        st.session_state[STATE_KEYS["TRANSLATION"]["REQUESTED"]] = True
                        st.rerun()
            with col2:
                if st.button("View", key=f"view_note_{i}", use_container_width=True):
                    st.session_state.current_note = note
                    st.rerun()
            st.divider()

def render_create_note_form() -> bool:
    """
    Render the form for creating a new note.
    
    Returns:
        bool: True if a note was created, False otherwise
    """
    st.markdown("## Create a New Note")
    
    with st.form(key="create_note_form"):
        title = st.text_input("Title", key="note_title")
        content = st.text_area("Content", key="note_content", height=200)
        
        col1, col2 = st.columns([1, 5])
        with col1:
            submitted = st.form_submit_button("Save", use_container_width=True)
        with col2:
            if st.form_submit_button("Cancel", use_container_width=True, type="secondary"):
                st.session_state._create_note = False
                st.rerun()
                return False
                
    if submitted:
        if not title or not content:
            st.error("Please provide both title and content for your note.")
            return False
            
        with st.spinner("Saving note..."):
            success = notes_service.create_note(title, content)
            
        if success:
            st.success("Note created successfully!")
            st.session_state._create_note = False
            
            # Force refresh notes
            notes = notes_service.get_notes()
            if notes:
                st.session_state.notes = notes
                
            st.rerun()
            return True
        else:
            st.error("Failed to create note. Please try again.")
            return False
            
    return False

def render_note_detail(note: Dict[str, Any]) -> None:
    """Render the detail view of a note."""
    # Extract note data
    note_id = note.get("id")
    title = note.get("title", "Untitled")
    content = note.get("content", "")
    is_translated = note.get("is_translated", False)
    original_content = note.get("original_content", "")
    
    # Back button
    if st.button("← Back to Notes", key="back_btn"):
        st.session_state.current_note = None
        
        # Clear any translation state
        for key in STATE_KEYS["PREVIEW"].values():
            if key in st.session_state:
                del st.session_state[key]
                
        st.rerun()
    
    # Show side by side view if requested
    if st.session_state.get("_show_side_by_side", False):
        st.markdown("## Side by Side Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Original (Russian)")
            st.markdown(original_content)
            
        with col2:
            st.markdown("### Translated (English)")
            st.markdown(content)
            
        if st.button("← Back to Note", key="back_to_note_btn"):
            st.session_state._show_side_by_side = False
            st.rerun()
    else:
        # Note detail view
        st.markdown(f"## {title}")
        
        # Handle translated content display
        if is_translated:
            # Create tabs for translated and original content
            tab_translated, tab_original = st.tabs(["📝 Translated (English)", "🇷🇺 Original (Russian)"])
            
            with tab_translated:
                st.markdown(f"{content}")
                st.markdown("""
                <div style="margin-top: 10px; padding: 8px; background-color: rgba(255, 107, 0, 0.05); 
                border-radius: 4px; display: flex; align-items: center;">
                    <span style="color: var(--primary-color); margin-right: 5px;">🔄</span>
                    <span style="font-size: 0.9rem; color: var(--text-color);">Translated from Russian to English</span>
                </div>
                """, unsafe_allow_html=True)
            
            with tab_original:
                st.markdown(f"{original_content}")
                
            # Add a button to show side-by-side view
            if st.button("📊 Side-by-Side View", key="side_by_side_btn"):
                st.session_state._show_side_by_side = True
                st.rerun()
        else:
            # Show regular content if not translated
            st.markdown(f"{content}")
            
            # Show live translation button for Russian text
            if contains_russian(content):
                if not st.session_state.get("_live_translation_visible", False):
                    col_opt1, col_opt2 = st.columns([1, 3])
                    with col_opt1:
                        translation_options = st.button("🔄 Show Translation Options", key="show_translation_options")
                        if translation_options:
                            st.session_state._live_translation_visible = True
                            st.rerun()
                else:
                    # Show translation options
                    st.markdown("### Translation Options")
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        if st.button("🔄 Quick Translate", key="quick_translate_btn", help="Show a quick translation without saving"):
                            # Initialize translation state
                            st.session_state[STATE_KEYS["PREVIEW"]["VISIBLE"]] = True
                            st.session_state[STATE_KEYS["PREVIEW"]["LOADING"]] = True
                            st.session_state[STATE_KEYS["PREVIEW"]["RESULT"]] = None
                            st.session_state[STATE_KEYS["PREVIEW"]["ERROR"]] = None
                            
                            st.rerun()
                    
                    with col2:
                        if st.button("💾 Translate & Save", key="translate_save_btn", help="Translate and save the note"):
                            st.session_state[STATE_KEYS["TRANSLATION"]["IN_PROGRESS"]] = True
                            st.session_state[STATE_KEYS["TRANSLATION"]["REQUESTED"]] = True
                            st.rerun()
                    
                    with col3:
                        if st.button("❌ Hide Options", key="hide_translation_options"):
                            st.session_state["_live_translation_visible"] = False
                            # Clear any translation preview
                            for key in STATE_KEYS["PREVIEW"].values():
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.rerun()
                            
                    # Show translation popup if requested
                    if st.session_state.get(STATE_KEYS["PREVIEW"]["VISIBLE"], False):
                        # Create a container for the translation
                        with st.container():
                            st.markdown("""
                            <div style="margin: 20px 0; padding: 15px; background-color: rgba(255, 107, 0, 0.05); 
                            border: 1px solid rgba(255, 107, 0, 0.2); border-radius: 8px;">
                            <h4 style="color: var(--primary-color); margin-top: 0;">Quick Translation Preview</h4>
                            """, unsafe_allow_html=True)
                            
                            # Create a placeholder for the translation result
                            translation_placeholder = st.empty()
                            
                            # Check if we have an error
                            if st.session_state.get(STATE_KEYS["PREVIEW"]["ERROR"]):
                                translation_placeholder.error(st.session_state[STATE_KEYS["PREVIEW"]["ERROR"]])
                                # Reset the error state
                                del st.session_state[STATE_KEYS["PREVIEW"]["ERROR"]]
                            # Check if we have a result
                            elif st.session_state.get(STATE_KEYS["PREVIEW"]["RESULT"]):
                                translation_placeholder.markdown(st.session_state[STATE_KEYS["PREVIEW"]["RESULT"]])
                            # Show loading state - will be replaced after async operation
                            elif st.session_state.get(STATE_KEYS["PREVIEW"]["LOADING"], True):
                                translation_placeholder.info("Loading translation...")
                            
                            st.markdown("""
                            <div style="display: flex; justify-content: flex-end; margin-top: 10px;">
                            <small style="color: var(--text-color); opacity: 0.7;">This is a preview only and won't be saved</small>
                            </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # If we're loading, trigger the async translation
                            if st.session_state.get(STATE_KEYS["PREVIEW"]["LOADING"], False):
                                # Clear the loading state
                                st.session_state[STATE_KEYS["PREVIEW"]["LOADING"]] = False
                                
                                # Run the translation preview in the background
                                st.cache_data(ttl=300)(get_translation_preview_wrapper)()
                                
def get_translation_preview_wrapper():
    """Wrapper for async translation preview to use with st.cache_data."""
    if "current_note" not in st.session_state:
        return
        
    note_id = st.session_state["current_note"].get("id")
    if not note_id:
        return
    
    try:
        # Use synchronous API call instead of creating a new event loop
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
        token = st.session_state.get("token")
        
        if not token:
            st.session_state[STATE_KEYS["PREVIEW"]["ERROR"]] = "Authentication required. Please log in."
            return
            
        # Set up headers with authorization
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token
        }
        
        # Use the correct endpoint with preview parameter
        url = f"{api_base_url}/notes/{note_id}/translate?preview=true"
        logger.info(f"Making translation preview request to: {url}")
        
        # Make synchronous request instead of async
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers)
            
            if response.status_code == 401:
                # Token is invalid or expired
                logger.error("Authentication failed during translation preview")
                st.session_state[STATE_KEYS["PREVIEW"]["ERROR"]] = "Authentication failed. Please log in again."
                
                # Clear token and redirect to login
                if "token" in st.session_state:
                    del st.session_state["token"]
                if "user" in st.session_state:
                    del st.session_state["user"]
                st.session_state["show_login"] = True
                return
                
            if response.status_code == 200:
                # Parse the response
                response_data = response.json()
                logger.info(f"Translation preview successful, received response with fields: {list(response_data.keys())}")
                
                # The translated text is in the content field of the note object
                if "content" in response_data:
                    st.session_state[STATE_KEYS["PREVIEW"]["RESULT"]] = response_data["content"]
                    logger.info("Successfully extracted translated content from response")
                # For backwards compatibility, also check for translated_text field
                elif "translated_text" in response_data:
                    st.session_state[STATE_KEYS["PREVIEW"]["RESULT"]] = response_data["translated_text"]
                    logger.info("Using translated_text field from response")
                else:
                    logger.error(f"Translation preview response missing content field. Available fields: {list(response_data.keys())}")
                    st.session_state[STATE_KEYS["PREVIEW"]["ERROR"]] = "Could not find translated text in response"
            else:
                error_message = f"Translation preview failed with status code: {response.status_code}"
                logger.error(error_message)
                try:
                    error_detail = response.json()
                    logger.error(f"Error details: {error_detail}")
                    st.session_state[STATE_KEYS["PREVIEW"]["ERROR"]] = error_detail.get("detail", error_message)
                except:
                    error_detail = response.text[:100]
                    logger.error(f"Error response: {error_detail}")
                    st.session_state[STATE_KEYS["PREVIEW"]["ERROR"]] = error_message
            
        # Rerun to update UI
        st.rerun()
    except Exception as e:
        st.session_state[STATE_KEYS["PREVIEW"]["ERROR"]] = f"Translation preview failed: {str(e)}"
        st.rerun()

def translate_note_wrapper():
    """Wrapper for translation to use with st.cache_data."""
    if "current_note" not in st.session_state:
        return
        
    note_id = st.session_state["current_note"].get("id")
    if not note_id:
        return
        
    try:
        # Use synchronous API call instead of creating a new event loop
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
        token = st.session_state.get("token")
        
        if not token:
            st.session_state[STATE_KEYS["TRANSLATION"]["ERROR"]] = "Authentication required. Please log in."
            st.session_state[STATE_KEYS["TRANSLATION"]["IN_PROGRESS"]] = False
            return
            
        # Set up headers with authorization
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token
        }
        
        # Call translation endpoint (without preview param for full translation)
        url = f"{api_base_url}/notes/{note_id}/translate"
        logger.info(f"Making full translation request to: {url}")
        
        # Make synchronous request instead of async
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers)
            
            if response.status_code == 401:
                # Token is invalid or expired
                logger.error("Authentication failed during translation")
                st.session_state[STATE_KEYS["TRANSLATION"]["ERROR"]] = "Authentication failed. Please log in again."
                
                # Clear token and redirect to login
                if "token" in st.session_state:
                    del st.session_state["token"]
                if "user" in st.session_state:
                    del st.session_state["user"]
                st.session_state["show_login"] = True
                st.session_state[STATE_KEYS["TRANSLATION"]["IN_PROGRESS"]] = False
                return
                
            if response.status_code == 200:
                # Parse the response - expect a complete note object
                response_data = response.json()
                logger.info(f"Translation successful, received response with fields: {list(response_data.keys())}")
                
                # Update current note with the fully translated note
                if "id" in response_data and "content" in response_data:
                    st.session_state["current_note"] = response_data
                    logger.info(f"Successfully updated note with translated content")
                    
                    # Refresh notes list using synchronous request
                    notes_url = f"{api_base_url}/notes"
                    notes_response = client.get(notes_url, headers=headers)
                    if notes_response.status_code == 200:
                        st.session_state["notes"] = notes_response.json()
                    
                    # Set success flag
                    st.session_state[STATE_KEYS["TRANSLATION"]["COMPLETE"]] = True
                else:
                    logger.error(f"Translation response missing expected fields. Available fields: {list(response_data.keys())}")
                    st.session_state[STATE_KEYS["TRANSLATION"]["ERROR"]] = "Incomplete translation data received"
            else:
                error_message = f"Translation failed with status code: {response.status_code}"
                logger.error(error_message)
                try:
                    error_detail = response.json()
                    logger.error(f"Error details: {error_detail}")
                    st.session_state[STATE_KEYS["TRANSLATION"]["ERROR"]] = error_detail.get("detail", error_message)
                except:
                    error_detail = response.text[:100]
                    logger.error(f"Error response: {error_detail}")
                    st.session_state[STATE_KEYS["TRANSLATION"]["ERROR"]] = error_message
    except Exception as e:
        st.session_state[STATE_KEYS["TRANSLATION"]["ERROR"]] = f"Translation failed: {str(e)}"
    finally:
        # Clear flag
        st.session_state[STATE_KEYS["TRANSLATION"]["IN_PROGRESS"]] = False
        st.rerun()

def render_notes_view() -> None:
    """
    Render the appropriate notes view based on the current state.
    
    This function:
    1. Handles translation requests if present
    2. Renders the appropriate view (note detail or notes list)
    """
    # Check if user is authenticated
    if "token" not in st.session_state:
        st.warning("Please log in to view your notes")
        st.session_state["show_login"] = True
        return
        
    # Get notes from state
    notes = st.session_state.get("notes", [])
    
    # Make sure notes is actually a list, not a coroutine
    if not isinstance(notes, list):
        # If it's not a list, use an empty list instead to avoid errors
        logger.error(f"Expected notes to be a list, got {type(notes)} instead")
        notes = []
    
    # Check if a note is being created
    creating_note = st.session_state.get("_create_note", False)
    
    # Check if translation is requested for saving
    if st.session_state.get(STATE_KEYS["TRANSLATION"]["REQUESTED"], False) and st.session_state.get("current_note"):
        # Set translation in progress flag
        st.session_state[STATE_KEYS["TRANSLATION"]["IN_PROGRESS"]] = True
        
        # Reset the translation request flag
        st.session_state[STATE_KEYS["TRANSLATION"]["REQUESTED"]] = False
        
        # Run the translation in the background
        st.cache_data(ttl=300)(translate_note_wrapper)()
    
    # Handle translation completion
    if st.session_state.get(STATE_KEYS["TRANSLATION"]["COMPLETE"], False):
        st.success("Translation completed successfully!")
        st.session_state[STATE_KEYS["TRANSLATION"]["COMPLETE"]] = False
    
    # Handle translation errors
    if st.session_state.get(STATE_KEYS["TRANSLATION"]["ERROR"], None):
        error_msg = st.session_state[STATE_KEYS["TRANSLATION"]["ERROR"]]
        st.error(error_msg)
        del st.session_state[STATE_KEYS["TRANSLATION"]["ERROR"]]
    
    # Render the appropriate view
    if creating_note:
        render_create_note_form()
    elif "current_note" in st.session_state and st.session_state["current_note"]:
        # Show detail view
        render_note_detail(st.session_state["current_note"])
    else:
        # Show notes list
        render_notes_list(notes) 