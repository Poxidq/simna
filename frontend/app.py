"""
Main Streamlit application file.

This module contains the main application logic.
"""
import streamlit as st
import asyncio
import extra_streamlit_components as stx

# Import page configuration and apply at the very beginning, before any other Streamlit calls
from frontend.utils.theme import get_page_config, apply_theme
# Set page config as the first Streamlit command
st.set_page_config(**get_page_config())

from frontend.components.auth import (
    render_login_form, 
    render_register_form, 
    render_top_nav
)
from frontend.components.notes import (
    render_notes_list,
    render_create_note_form,
    render_note_detail
)
from frontend.services.auth_service import (
    login, 
    register, 
    logout, 
    get_current_user,
    cookie_is_valid,
    COOKIE_NAME
)
from frontend.services.notes_service import (
    create_note, 
    get_notes, 
    get_note,
    update_note,
    delete_note,
    translate_note
)
from frontend.utils.validators import validate_note_form, validate_login_form, validate_register_form


async def main() -> None:
    """Main application function."""
    # Initialize the cookie manager for persistent login
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager()
    
    # Check if we have a valid auth cookie first (for persistent login)
    if not st.session_state.get("token") and "cookie_manager" in st.session_state:
        cookie_valid = cookie_is_valid(st.session_state.cookie_manager)
        if cookie_valid:
            st.success("Welcome back! You've been automatically logged in.")
            # Force a rerun to update UI with authenticated state
            st.rerun()
    
    # Initialize session state variables if they don't exist
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "current_note" not in st.session_state:
        st.session_state.current_note = None
    if "show_login" not in st.session_state:
        st.session_state.show_login = True
    if "show_register" not in st.session_state:
        st.session_state.show_register = False
    if "show_create_note" not in st.session_state:
        st.session_state.show_create_note = False
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
    
    # Apply theme (page config is already set at the beginning of the file)
    apply_theme()
    
    # Check if user is logged in, if not show login/register form
    if not st.session_state.token:
        # Process login form submission
        if st.session_state.get("_login_form_submitted", False):
            username = st.session_state.get("username", "")
            password = st.session_state.get("password", "")
            
            # Validate inputs
            if validate_login_form(username, password):
                with st.spinner("Logging in..."):
                    success, error_msg = await login(username, password)
                    
                    if success:
                        # Token is already stored in session state by the login function
                        success_user, _ = await get_current_user()
                        if success_user:
                            st.session_state.show_login = False
                            st.rerun()
                    # else: don't show error message 
                        # st.error(error_msg or "Invalid username or password")
            
            # Reset form submission flag
            st.session_state._login_form_submitted = False
        
        # Process registration form submission
        if st.session_state.get("_register_form_submitted", False):
            username = st.session_state.get("reg_username", "")
            email = st.session_state.get("reg_email", "")
            password = st.session_state.get("reg_password", "")
            
            # Validate inputs
            if validate_register_form(username, email, password):
                with st.spinner("Creating your account..."):
                    success = await register(username, email, password)
                    
                    if success:
                        st.success("Registration successful! Please log in.")
                        st.session_state.show_register = False
                        st.session_state.show_login = True
                        st.rerun()
                    else:
                        st.error("Registration failed. Username or email may already be in use.")
            
            # Reset form submission flag
            st.session_state._register_form_submitted = False
        
        # Show login or register form
        if st.session_state.show_login:
            render_login_form()
        elif st.session_state.show_register:
            render_register_form()
    else:
        # If user is logged in, render the top navigation instead of sidebar
        render_top_nav()
        
        # Handle main content area
        await main_content()


async def main_content() -> None:
    """Render the main content area."""
    if st.session_state.get("show_create_note", False):
        # Show create note form
        create_note_submitted = render_create_note_form()
        
        if create_note_submitted:
            title = st.session_state.get("note_title", "")
            content = st.session_state.get("note_content", "")
            
            # Validate inputs
            if validate_note_form(title, content):
                with st.spinner("Creating note..."):
                    note = await create_note(title, content)
                    
                    if note:
                        st.success("Note created successfully!")
                        st.session_state.current_note = note
                        st.session_state.show_create_note = False
                        st.rerun()
                    else:
                        st.error("Failed to create note.")
    elif st.session_state.get("current_note"):
        # Show note detail
        note = st.session_state.get("current_note")
        
        # Make sure note is a dictionary before proceeding
        if isinstance(note, dict):
            # Handle edit form submission
            if st.session_state.get("_edit_note_submitted", False):
                updated_title = st.session_state.get("edit_note_title", "")
                updated_content = st.session_state.get("edit_note_content", "")
                
                # Validate inputs
                if validate_note_form(updated_title, updated_content):
                    with st.spinner("Updating note..."):
                        updated_note = await update_note(
                            note.get("id"), 
                            updated_title, 
                            updated_content
                        )
                        
                        if updated_note:
                            st.success("Note updated successfully!")
                            st.session_state.current_note = updated_note
                            st.session_state.edit_mode = False
                        else:
                            st.error("Failed to update note.")
                
                # Reset submission flag
                st.session_state._edit_note_submitted = False
            
            # Handle translate request
            if st.session_state.get("_translate_note_requested", False):
                with st.spinner("Translating note..."):
                    translated_note = await translate_note(note.get("id"))
                    
                    if translated_note:
                        st.success("Note translated successfully!")
                        st.session_state.current_note = translated_note
                    else:
                        st.error("Failed to translate note.")
                
                # Reset request flag
                st.session_state._translate_note_requested = False
            
            # Handle delete confirmation
            if st.session_state.get("_delete_note_confirmed", False):
                with st.spinner("Deleting note..."):
                    success = await delete_note(note.get("id"))
                    
                    if success:
                        st.success("Note deleted successfully!")
                        st.session_state.current_note = None
                        st.rerun()
                    else:
                        st.error("Failed to delete note.")
                
                # Reset confirmation flag
                st.session_state._delete_note_confirmed = False
            
            # Render note detail view
            render_note_detail(note)
        else:
            # Handle invalid note object
            st.error("Invalid note data. Returning to notes list.")
            st.session_state.current_note = None
            st.rerun()
    else:
        # Show notes list
        with st.spinner("Loading notes..."):
            success = await get_notes()
            notes = st.session_state.get("notes", [])
            
            if success and isinstance(notes, list):
                # Render notes list
                render_notes_list(notes)
            else:
                st.error("Failed to load notes.")


if __name__ == "__main__":
    asyncio.run(main()) 