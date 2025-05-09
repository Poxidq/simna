"""
Notes service.

This module provides functions for note operations.
"""
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import streamlit as st

from frontend.services.api import api_request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notes_service")

# Debug mode setting
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"


async def get_notes() -> List[Dict[str, Any]]:
    """
    Get all notes for the current user.
    
    Returns:
        List[Dict[str, Any]]: List of notes or empty list if error
    """
    # Get auth token from session_state
    if "token" not in st.session_state:
        st.error("Authentication token is missing")
        return []
    
    token: str = st.session_state.token
    
    try:
        # Use Any type for the response and cast to the proper type after verification
        response = await api_request("GET", "/notes", token=token)
        
        if response:
            # Verify that the response is a list before assigning
            if isinstance(response, list):
                # Store notes in session state
                st.session_state.notes = response
                # Debug info
                if DEBUG_MODE:
                    logging.debug(f"Loaded {len(response)} notes")
                return response
            else:
                # Handle case where response isn't a list as expected
                if DEBUG_MODE:
                    logging.error(f"Expected list response, got: {type(response)}")
                return []
        else:
            # st.error("Failed to fetch notes")
            if DEBUG_MODE:
                logging.error("Error fetching notes: No data returned")
            return []
    except Exception as e:
        # st.error(f"Error fetching notes: {str(e)}")
        if DEBUG_MODE:
            logging.exception("Error in get_notes")
        return []


async def get_note(note_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific note by ID.
    
    Args:
        note_id: ID of the note to retrieve
        
    Returns:
        Optional[Dict[str, Any]]: Note data or None if retrieval fails
    """
    # Get auth token from session_state
    if "token" not in st.session_state:
        if DEBUG_MODE:
            logging.debug("Cannot get note: No authentication token available")
        return None
    
    token: str = st.session_state.token
    
    try:
        # Special handling when restoring notes after page refresh
        is_restore = st.session_state.get("_restore_note_id") == note_id
        
        if DEBUG_MODE:
            if is_restore:
                logging.debug(f"Attempting to restore note with ID: {note_id}")
            else:
                logging.debug(f"Fetching note with ID: {note_id}")
        
        response: Optional[Dict[str, Any]] = await api_request(
            "GET", 
            f"/notes/{note_id}", 
            token=token
        )
        
        if response:
            # Debug info
            if DEBUG_MODE:
                if is_restore:
                    logging.debug(f"Successfully restored note: {response.get('title', 'Untitled')}")
                else:
                    logging.debug(f"Retrieved note: {response}")
            return response
        else:
            # Use a more targeted approach for error messages
            if not is_restore:
                # Only show error to user if this is a direct request, not a restoration
                st.error("Failed to retrieve note")
            
            if DEBUG_MODE:
                logging.error(f"Error retrieving note {note_id}: No data returned")
            return None
    except Exception as e:
        # Again, only show errors directly if not restoring
        if not st.session_state.get("_restore_note_id") == note_id:
            st.error(f"Error retrieving note: {str(e)}")
        
        if DEBUG_MODE:
            logging.exception(f"Error in get_note for note_id={note_id}")
        return None


async def create_note(title: str, content: str) -> bool:
    """
    Create a new note.

    Args:
        title: Note title
        content: Note content

    Returns:
        bool: Success status
    """
    # Get auth token from session_state
    if "token" not in st.session_state:
        st.error("Authentication token is missing")
        return False
    
    token: str = st.session_state.token
    
    try:
        response: Optional[Dict[str, Any]] = await api_request(
            "POST", 
            "/notes", 
            data={"title": title, "content": content},
            token=token
        )
        
        if response:
            # Refresh notes list
            notes = await get_notes()
            # Set the notes in session state
            st.session_state.notes = notes
            
            # Debug info
            if DEBUG_MODE:
                logging.debug(f"Created note: {response}")
            return True
        else:
            # st.error("Failed to create note")
            if DEBUG_MODE:
                logging.error("Error creating note: No data returned")
            return False
    except Exception as e:
        st.error(f"Error creating note: {str(e)}")
        if DEBUG_MODE:
            logging.exception("Error in create_note")
        return False


async def update_note(note_id: int, title: Optional[str], content: Optional[str]) -> bool:
    """
    Update a note.

    Args:
        note_id: Note ID
        title: Note title
        content: Note content

    Returns:
        bool: Success status
    """
    # Get auth token from session_state
    if "token" not in st.session_state:
        st.error("Authentication token is missing")
        return False
    
    token: str = st.session_state.token
    
    update_data: Dict[str, str] = {}
    if title:
        update_data["title"] = title
    if content:
        update_data["content"] = content
    
    try:
        response: Optional[Dict[str, Any]] = await api_request(
            "PUT", 
            f"/notes/{note_id}", 
            data=update_data,
            token=token
        )
        
        if response:
            # Update the current note if it's the one being edited
            if "current_note" in st.session_state and st.session_state.current_note and st.session_state.current_note.get("id") == note_id:
                st.session_state.current_note = response
            
            # Refresh notes list
            notes = await get_notes()
            # Set the notes in session state
            st.session_state.notes = notes
            
            # Debug info
            if DEBUG_MODE:
                logging.debug(f"Updated note: {response}")
            return True
        else:
            # st.error("Failed to update note")
            if DEBUG_MODE:
                logging.error("Error updating note: No data returned")
            return False
    except Exception as e:
        st.error(f"Error updating note: {str(e)}")
        if DEBUG_MODE:
            logging.exception("Error in update_note")
        return False


async def delete_note(note_id: int) -> bool:
    """
    Delete a note.

    Args:
        note_id: Note ID

    Returns:
        bool: Success status
    """
    # Get auth token from session_state
    if "token" not in st.session_state:
        st.error("Authentication token is missing")
        return False
    
    token: str = st.session_state.token
    
    try:
        # Use DELETE method to delete the note
        response = await api_request("DELETE", f"/notes/{note_id}", token=token)
        
        # Refresh notes list
        notes = await get_notes()
        # Set the notes in session state
        st.session_state.notes = notes
        
        # Clear current note if it's the one being deleted
        if "current_note" in st.session_state and st.session_state.current_note and st.session_state.current_note.get("id") == note_id:
            st.session_state.current_note = None
        
        # Debug info
        if DEBUG_MODE:
            logging.debug(f"Deleted note: {note_id}")
        
        # Always return success since HTTPStatusError would be caught if the deletion failed
        return True
    except Exception as e:
        st.error(f"Error deleting note: {str(e)}")
        if DEBUG_MODE:
            logging.exception("Error in delete_note")
        return False


async def get_translation_preview(note_id: int):
    """
    Get a translation preview for a note.
    
    Args:
        note_id: ID of the note to translate
        
    Returns:
        Dict containing translation result or None if error
    """
    # Get auth token from session_state
    if "token" not in st.session_state:
        if DEBUG_MODE:
            logging.debug("Cannot translate: No authentication token available")
        return None
    
    token: str = st.session_state.token
    
    try:
        # Use the correct endpoint with preview parameter
        response = await api_request(
            "POST", 
            f"/notes/{note_id}/translate", 
            params={"preview": "true"},
            token=token
        )
        
        if response and "translated_text" in response:
            if DEBUG_MODE:
                logging.debug(f"Translation preview successful")
            return response
        else:
            if DEBUG_MODE:
                logging.error(f"Translation preview failed: {response}")
            return None
    except Exception as e:
        if DEBUG_MODE:
            logging.exception(f"Error in get_translation_preview: {str(e)}")
        return None


async def translate_note(note_id: int) -> bool:
    """
    Translate a note and save the result.
    
    Args:
        note_id: ID of the note to translate
        
    Returns:
        bool: Success status
    """
    # Get auth token from session_state
    if "token" not in st.session_state:
        st.error("Authentication token is missing")
        return False
    
    token: str = st.session_state.token
    
    try:
        # Use POST to translate the note - no preview param for full translation
        response = await api_request(
            "POST", 
            f"/notes/{note_id}/translate",
            token=token
        )
        
        if response:
            # Update the current note if it's the one being translated
            if "current_note" in st.session_state and st.session_state.current_note and st.session_state.current_note.get("id") == note_id:
                st.session_state.current_note = response
                
            # Refresh notes list
            notes = await get_notes()
            # Update notes in session state
            st.session_state.notes = notes
            
            if DEBUG_MODE:
                logging.debug(f"Translation successful: {response}")
            return True
        else:
            if DEBUG_MODE:
                logging.error("Translation failed: No data returned")
            return False
    except Exception as e:
        if DEBUG_MODE:
            logging.exception(f"Error in translate_note: {str(e)}")
        return False 