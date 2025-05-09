"""
Notes service.

This module provides functions for note operations.
"""
import os
import logging
import streamlit as st
from typing import Dict, List, Any, Optional, Union, Tuple, cast

from frontend.services.api import api_request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notes_service")

# Debug mode setting
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"


async def get_notes() -> bool:
    """
    Get all notes for the current user.
    
    Returns:
        bool: Success status
    """
    # Get auth token from session_state
    if "token" not in st.session_state:
        st.error("Authentication token is missing")
        return False
    
    token: str = st.session_state.token
    
    try:
        # Use Any type for the response and cast to the proper type after verification
        response = await api_request("GET", "/notes", token=token)
        
        if response:
            # Verify that the response is a list before assigning
            if isinstance(response, list):
                st.session_state.notes = response
                # Debug info
                if DEBUG_MODE:
                    logging.debug(f"Loaded {len(response)} notes")
                return True
            else:
                # Handle case where response isn't a list as expected
                # st.error("Unexpected response format from API")
                if DEBUG_MODE:
                    logging.error(f"Expected list response, got: {type(response)}")
                return False
        else:
            # st.error("Failed to fetch notes")
            if DEBUG_MODE:
                logging.error("Error fetching notes: No data returned")
            return False
    except Exception as e:
        # st.error(f"Error fetching notes: {str(e)}")
        if DEBUG_MODE:
            logging.exception("Error in get_notes")
        return False


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
            await get_notes()
            # st.success("Note created successfully!")
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
            # Refresh notes list
            await get_notes()
            
            # Update current note if it's the one being edited
            if "current_note" in st.session_state and st.session_state.current_note and st.session_state.current_note.get("id") == note_id:
                st.session_state.current_note = response
                
            st.success("Note updated successfully!")
            
            # Debug info
            if DEBUG_MODE:
                logging.debug(f"Updated note: {response}")
                
            return True
        else:
            st.error("Failed to update note")
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
        # Make the DELETE request
        response = await api_request(
            "DELETE", 
            f"/notes/{note_id}", 
            token=token
        )
        
        # For DELETE requests, a 204 response will return None
        # which is a successful deletion (not an error)
        # Clear current note if it's the one being deleted
        if "current_note" in st.session_state and st.session_state.current_note and st.session_state.current_note.get("id") == note_id:
            st.session_state.current_note = None
            
        # Refresh notes list
        await get_notes()
        
        # Debug info
        if DEBUG_MODE:
            logging.debug(f"Deleted note ID: {note_id}")
            
        # Always return success since HTTPStatusError would be caught if the deletion failed
        return True
    except Exception as e:
        st.error(f"Error deleting note: {str(e)}")
        if DEBUG_MODE:
            logging.exception("Error in delete_note")
        return False


async def get_translation_preview(note_id: int):
    """Get a preview of the translated note content without saving to database.
    
    Args:
        note_id: The ID of the note to translate
    
    Returns:
        tuple: (success, translation) where translation is the translated text or error message
    """
    # Check if token is in session state
    if "token" not in st.session_state:
        logger.warning("Translation preview attempted without auth token")
        return False, "Authentication required"
    
    token = st.session_state.token
    
    try:
        logger.info(f"Requesting translation preview for note_id={note_id}")
        
        # Use preview query parameter in request
        response = await api_request(
            f"/notes/{note_id}/translate",
            method="POST",
            token=token,
            params={"preview": "true"}
        )
        
        if response and "translated_text" in response:
            # Log a truncated version of the translation for debugging
            preview_text = response["translated_text"][:50] + "..." if len(response["translated_text"]) > 50 else response["translated_text"]
            logger.debug(f"Translation preview response received: {preview_text}")
            return True, response["translated_text"]
        elif response:
            logger.error(f"Translation preview response missing translated_text: {response}")
            return False, "Error: Invalid response format"
        else:
            logger.error("No response received for translation preview")
            return False, "Error: No response from server"
            
    except Exception as e:
        logger.exception(f"Error getting translation preview: {str(e)}")
        return False, f"Error: {str(e)}"


async def translate_note(note_id: int) -> bool:
    """
    Translate a note.

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
        response: Optional[Dict[str, Any]] = await api_request(
            "POST", 
            f"/notes/{note_id}/translate", 
            token=token
        )
        
        if response:
            # Refresh notes list
            await get_notes()
            
            # Update current note if it's the one being translated
            if "current_note" in st.session_state and st.session_state.current_note and st.session_state.current_note.get("id") == note_id:
                st.session_state.current_note = response
                
            st.success("Note translated successfully!")
            
            # Debug info
            if DEBUG_MODE:
                logging.debug(f"Translated note: {response}")
                
            return True
        else:
            st.error("Failed to translate note")
            if DEBUG_MODE:
                logging.error("Error translating note: No data returned")
            return False
    except Exception as e:
        st.error(f"Error translating note: {str(e)}")
        if DEBUG_MODE:
            logging.exception("Error in translate_note")
        return False 