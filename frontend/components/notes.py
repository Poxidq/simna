"""
Notes UI components.

This module contains UI components for displaying and interacting with notes.
"""
from typing import List, Dict, Any, Optional
import streamlit as st
import threading
import logging
import os
import httpx
import json
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG_MODE", "False").lower() == "true" else logging.INFO)
logger = logging.getLogger(__name__)

# Import services at the module level
from frontend.services import notes_service
from frontend.services.api import api_request
from frontend.services.notes_service import get_translation_preview
from frontend.services.notes_service import translate_note

def get_translation_thread():
    """Thread function to handle translation preview requests."""
    try:
        # Get token and note_id from session state before thread starts
        token = st.session_state.get("token")
        note_id = st.session_state.get("current_note", {}).get("id")
        
        if not token:
            logger.error("Translation preview attempted without auth token")
            st.session_state["_translation_preview_error"] = "Authentication required"
            st.session_state["_translation_preview_loading"] = False
            # Redirect to login
            st.session_state["show_login"] = True
            st.rerun()
            return
            
        if not note_id:
            logger.error("No note ID available for translation")
            st.session_state["_translation_preview_error"] = "No note selected"
            st.session_state["_translation_preview_loading"] = False
            return
        
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
        
        # Make the request
        response = httpx.post(url, headers=headers, timeout=10.0)
        
        if response.status_code == 401:
            # Token is invalid or expired
            logger.error("Authentication failed during translation preview")
            st.session_state["_translation_preview_error"] = "Authentication failed. Please log in again."
            # Clear token and redirect to login
            if "token" in st.session_state:
                del st.session_state["token"]
            if "user" in st.session_state:
                del st.session_state["user"]
            st.session_state["show_login"] = True
            st.rerun()
            return
            
        if response.status_code == 200:
            # Successfully got translation preview
            response_data = response.json()
            if "translated_text" in response_data:
                st.session_state["_translation_preview_result"] = response_data["translated_text"]
                logger.info(f"Translation preview successful, received text of length: {len(response_data['translated_text'])}")
            else:
                logger.error(f"Translation preview response missing translated_text field: {list(response_data.keys())}")
                st.session_state["_translation_preview_error"] = "Invalid response from server"
        else:
            error_message = f"Translation preview failed with status code: {response.status_code}"
            logger.error(error_message)
            try:
                error_detail = response.json()
                logger.error(f"Error details: {error_detail}")
            except:
                error_detail = response.text[:100]
                logger.error(f"Error response: {error_detail}")
            
            st.session_state["_translation_preview_error"] = f"Error: {response.status_code}"
    except Exception as e:
        error_message = f"Error during translation preview: {str(e)}"
        logger.exception(error_message)
        st.session_state["_translation_preview_error"] = str(e)
    finally:
        # Mark loading as complete
        st.session_state["_translation_preview_loading"] = False
        # Try to force UI refresh
        try:
            st.rerun()
        except:
            pass

def translate_task():
    """Thread function to handle full translation requests."""
    try:
        # Get token and note_id from session state before thread starts
        token = st.session_state.get("token")
        note_id = st.session_state.get("current_note", {}).get("id")
        
        if not token:
            logger.error("Translation attempted without auth token")
            st.session_state["_translation_error"] = "Authentication required for translation"
            st.session_state["_translation_in_progress"] = False
            # Redirect to login
            st.session_state["show_login"] = True
            st.rerun()
            return
            
        if not note_id:
            logger.error("No note ID available for translation")
            st.session_state["_translation_error"] = "No note selected"
            st.session_state["_translation_in_progress"] = False
            return
        
        # Add a small delay to let UI update before starting translation
        time.sleep(0.5)
        
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
        
        # Use synchronous request in the thread to avoid asyncio issues
        response = httpx.post(url, headers=headers, timeout=30.0)
        
        if response.status_code == 401:
            # Token is invalid or expired
            logger.error("Authentication failed during translation")
            st.session_state["_translation_error"] = "Authentication failed. Please log in again."
            # Clear token and redirect to login
            if "token" in st.session_state:
                del st.session_state["token"]
            if "user" in st.session_state:
                del st.session_state["user"]
            st.session_state["show_login"] = True
            st.rerun()
            return
            
        if response.status_code == 200:
            # Parse the response
            response_data = response.json()
            logger.info(f"Translation successful, received response with fields: {list(response_data.keys())}")
            
            # Update the current note in session state
            if "current_note" in st.session_state:
                st.session_state["current_note"] = response_data
                logger.info("Updated current note with translated content")
            
            # Refresh notes list
            refresh_notes(token)
            
            # Set success flag
            st.session_state["_translation_complete"] = True
        else:
            error_message = f"Translation failed with status code: {response.status_code}"
            logger.error(error_message)
            try:
                error_detail = response.json()
                logger.error(f"Error details: {error_detail}")
            except:
                error_detail = response.text[:100]
                logger.error(f"Error response: {error_detail}")
            
            st.session_state["_translation_error"] = error_message
    except Exception as e:
        error_message = f"Error during translation: {str(e)}"
        logger.exception(error_message)
        st.session_state["_translation_error"] = error_message
    finally:
        # Always clean up
        st.session_state["_translation_in_progress"] = False
        # Try to force refresh
        try:
            st.rerun()
        except:
            pass

def refresh_notes(token):
    """Helper function to refresh notes list."""
    try:
        # Define the actual refresh function
        def _refresh_notes_task():
            try:
                api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
                url = f"{api_base_url}/notes"
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token
                }
                
                response = httpx.get(url, headers=headers, timeout=10.0)
                
                if response.status_code == 200:
                    notes_data = response.json()
                    st.session_state["notes"] = notes_data
                    logger.info(f"Successfully refreshed notes list, fetched {len(notes_data)} notes")
                else:
                    logger.error(f"Failed to refresh notes: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"Error refreshing notes: {str(e)}")
        
        # Run in a separate thread to avoid blocking
        refresh_thread = threading.Thread(target=_refresh_notes_task)
        refresh_thread.daemon = True
        refresh_thread.start()
    except Exception as e:
        logger.error(f"Error starting refresh thread: {str(e)}")

def render_notes_list(notes: List[Dict[str, Any]]) -> None:
    """Render the list of notes."""
    # Header with create button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("## My Notes")
    with col2:
        if st.button("➕ New Note", key="create_new_note_btn", use_container_width=True):
            st.session_state._create_note = True
            st.rerun()
    
    # Display each note as a card
    if not notes:
        st.markdown(
            """
            <div style="text-align: center; margin-top: 50px; margin-bottom: 50px; padding: 30px; 
                        border: 1px dashed var(--border-color); border-radius: 8px;">
                <p style="margin-bottom: 20px;">No notes available. Create your first note to get started!</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
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
                        st.session_state._translate_note_requested = True
                        st.rerun()
            with col2:
                if st.button("View", key=f"view_note_{i}", use_container_width=True):
                    st.session_state.current_note = note
                    st.rerun()
            st.divider()


def render_create_note_form() -> bool:
    """Render the form for creating a new note.
    
    Returns:
        bool: True if the form was submitted, False otherwise.
    """
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h2>Create New Note</h2>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    with st.form(key="create_note_form", clear_on_submit=False):
        st.text_input("Title", key="note_title")
        st.text_area("Content", key="note_content", height=300)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("Create Note", use_container_width=True)
            if submit:
                st.session_state._note_create_submitted = True
        with col2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
            if cancel:
                st.session_state._create_note = False
                st.rerun()
    
    # Return submission status            
    return st.session_state.get("_note_create_submitted", False)


def contains_russian(text: str) -> bool:
    """Check if text contains Russian characters.
    
    Args:
        text: Text to check
        
    Returns:
        bool: True if text contains Russian characters, False otherwise
    """
    if not isinstance(text, str):
        return False
    
    # Define set of Russian Cyrillic characters
    russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
                       'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
    
    # Check if any character in text is in the set of Russian characters
    return any(char in russian_chars for char in text)


def render_note_detail(note: Dict[str, Any]) -> None:
    """Render the detail view of a note.
    
    Args:
        note: The note to display.
    """
    # Validate that note is a dictionary
    if not isinstance(note, dict):
        st.error("Invalid note data. Please go back to the notes list.")
        if st.button("Back to Notes", key="back_from_invalid"):
            st.session_state.current_note = None
            st.rerun()
        return
    
    note_id = note.get("id")
    title = note.get("title", "Untitled")
    content = note.get("content", "")
    is_translated = note.get("is_translated", False)
    original_content = note.get("original_content", "")
    
    # Show edit form if in edit mode
    if st.session_state.get("edit_mode", False):
        st.markdown(
            """
            <div style="margin-bottom: 20px;">
                <h2>Edit Note</h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        with st.form(key="edit_note_form", clear_on_submit=False):
            st.text_input("Title", key="edit_note_title", value=title)
            st.text_area("Content", key="edit_note_content", value=content, height=300)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button("Save Changes", use_container_width=True)
                if submit:
                    st.session_state._edit_note_submitted = True
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
                if cancel:
                    st.session_state.edit_mode = False
                    st.rerun()
    else:
        # Note detail view
        st.markdown(f"## {title}")
        
        # Check if translation is in progress
        translation_in_progress = st.session_state.get("_translation_in_progress", False)
        
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
                
            # Show side-by-side view if requested
            if st.session_state.get("_show_side_by_side", False):
                st.markdown("### Side-by-Side Comparison")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Original (Russian)**")
                    st.markdown(f"{original_content}")
                with col2:
                    st.markdown("**Translated (English)**")
                    st.markdown(f"{content}")
                    
                # Button to hide side-by-side view
                if st.button("❌ Hide Side-by-Side View", key="hide_side_by_side_btn"):
                    st.session_state._show_side_by_side = False
                    st.rerun()
        elif translation_in_progress:
            # Show content with translation spinner
            st.markdown(f"{content}")
            with st.spinner("Translating... Please wait"):
                st.info("Translation in progress. This may take a moment.")
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
                            st.session_state["_show_live_translation"] = True
                            st.session_state["_translation_preview_loading"] = True
                            st.session_state["_translation_preview_result"] = None
                            st.session_state["_translation_preview_error"] = None
                            
                            # Start translation thread
                            thread = threading.Thread(target=get_translation_thread)
                            thread.daemon = True
                            thread.start()
                    
                    with col2:
                        if st.button("💾 Translate & Save", key="translate_save_btn", help="Translate and save the note"):
                            st.session_state["_translation_in_progress"] = True
                            st.session_state["_translate_note_requested"] = True
                            st.rerun()
                    
                    with col3:
                        if st.button("❌ Hide Options", key="hide_translation_options"):
                            st.session_state["_live_translation_visible"] = False
                            st.rerun()
                            
                    # Show translation popup if requested
                    if st.session_state.get("_show_live_translation", False):
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
                            if st.session_state.get("_translation_preview_error"):
                                translation_placeholder.error(st.session_state["_translation_preview_error"])
                                del st.session_state["_translation_preview_error"]
                            # Check if we have a result
                            elif st.session_state.get("_translation_preview_result"):
                                translation_placeholder.markdown(st.session_state["_translation_preview_result"])
                            # Show loading state
                            elif st.session_state.get("_translation_preview_loading", True):
                                translation_placeholder.info("Loading translation...")
                            
                            st.markdown("""
                            <div style="display: flex; justify-content: flex-end; margin-top: 10px;">
                            <small style="color: var(--text-color); opacity: 0.7;">This is a preview only and won't be saved</small>
                            </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Button to hide translation
                            if st.button("❌ Hide Translation", key="hide_live_translation"):
                                st.session_state["_show_live_translation"] = False
                                # Clean up the translation state
                                for key in ["_translation_preview_result", "_translation_preview_loading", "_translation_preview_error"]:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                st.rerun()
        
        # Action buttons in rows
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Edit", key="edit_btn", use_container_width=True):
                st.session_state.edit_mode = True
                # Reset any translation views when editing
                if "_show_live_translation" in st.session_state:
                    del st.session_state._show_live_translation
                if "_show_side_by_side" in st.session_state:
                    del st.session_state._show_side_by_side
                if "_live_translation_visible" in st.session_state:
                    del st.session_state._live_translation_visible
                st.rerun()
        
        with col2:
            if st.button("◀️ Back to Notes", key="back_btn", use_container_width=True):
                st.session_state.current_note = None
                # Clean up translation-related session state
                if "_show_live_translation" in st.session_state:
                    del st.session_state._show_live_translation
                if "_show_side_by_side" in st.session_state:
                    del st.session_state._show_side_by_side
                st.rerun()
        
        # Delete button
        if st.button("🗑️ Delete", key="delete_btn", use_container_width=True):
            st.session_state._confirm_delete = True
        
        # Delete confirmation dialog
        if st.session_state.get("_confirm_delete", False):
            st.warning("Are you sure you want to delete this note? This action cannot be undone.")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Yes, delete it", key="btn_confirm_delete", use_container_width=True):
                    st.session_state._delete_note_confirmed = True
                    st.session_state._confirm_delete = False
            with col2:
                if st.button("Cancel", key="btn_cancel_delete", use_container_width=True):
                    st.session_state._confirm_delete = False
                    st.rerun()


def render_notes_view() -> None:
    """
    Render the appropriate notes view based on the current state.
    
    This function:
    1. Handles translation requests if present
    2. Renders the appropriate view (note detail or notes list)
    """
    # Get notes from state
    notes = st.session_state.get("notes", [])
    
    # Check if a note is being created
    creating_note = st.session_state.get("_create_note", False)
    
    # Check if translation is requested for saving
    if st.session_state.get("_translate_note_requested", False) and st.session_state.get("current_note"):
        note_id = st.session_state["current_note"].get("id")
        if note_id:
            # Set translation in progress flag
            st.session_state["_translation_in_progress"] = True
            
            # Start translation in a thread only if not already in progress
            if not st.session_state.get("_translation_thread_running", False):
                st.session_state["_translation_thread_running"] = True
                threading.Thread(target=translate_task).start()
        
        # Reset the translation request flag
        st.session_state["_translate_note_requested"] = False
    
    # Handle translation completion
    if st.session_state.get("_translation_complete", False):
        st.success("Translation completed successfully!")
        st.session_state["_translation_complete"] = False
        st.session_state["_translation_thread_running"] = False
    
    # Handle translation errors
    if st.session_state.get("_translation_error", None):
        error_msg = st.session_state["_translation_error"]
        st.error(error_msg)
        del st.session_state["_translation_error"]
        st.session_state["_translation_thread_running"] = False
            
    # Render the appropriate view
    if st.session_state.get("current_note"):
        # Render note detail view
        render_note_detail(st.session_state["current_note"])
    elif creating_note:
        # Render create note form
        submitted = render_create_note_form()
        if submitted:
            # Reset the create note flag if form was submitted
            st.session_state["_create_note"] = False
    else:
        # Render notes list
        render_notes_list(notes) 