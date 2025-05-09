"""
Main Streamlit application file.

This module contains the main application logic for the Notes App:
1. User authentication with JWT token cookies
2. Automatic re-authentication when users return to the app
3. Maintaining view state across page refreshes
4. Note management (create, view, edit, delete, translate)

The application uses persistent authentication cookies to keep users logged in
between sessions, ensuring a seamless experience where they don't have to log in
every time they open the app.
"""
import os
import streamlit as st
import asyncio
import extra_streamlit_components as stx
import datetime as dt
import logging

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
    render_note_detail,
    render_notes_view
)
from frontend.services.auth_service import (
    login, 
    register, 
    logout, 
    get_current_user,
    cookie_is_valid,
    COOKIE_NAME,
    get_secret,
    token_encode,
    COOKIE_EXPIRY_DAYS
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


# Check if in production environment
IS_PRODUCTION = get_secret("environment", os.getenv("ENVIRONMENT", "development")).lower() == "production"
DEBUG_MODE = get_secret("debug", os.getenv("DEBUG_MODE", "False").lower() == "true")

# Production warnings
if IS_PRODUCTION and DEBUG_MODE:
    st.warning("⚠️ Warning: Debug mode is enabled in production environment. This is not recommended for security reasons.")


async def main() -> None:
    """Main application function."""
    # Add debug logging for page loads and cookie state
    if DEBUG_MODE:
        # Initialize cookie manager early for logging
        if "cookie_manager" not in st.session_state:
            st.session_state.cookie_manager = stx.CookieManager()
        cookies = st.session_state.cookie_manager.get_all(key="debug_log_cookies")
        has_auth_cookie = COOKIE_NAME in cookies
        
        logging.debug(f"============ PAGE LOADED ============")
        logging.debug(f"Has auth cookie: {has_auth_cookie}")
        logging.debug(f"Has token in session: {'token' in st.session_state}")
        if has_auth_cookie:
            cookie_length = len(cookies.get(COOKIE_NAME, ""))
            logging.debug(f"Auth cookie length: {cookie_length}")
        logging.debug(f"======================================")
    
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
    if "auth_checked" not in st.session_state:
        st.session_state.auth_checked = False
    
    # Initialize the cookie manager for persistent login - do this before anything else
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager()
    
    # Apply theme (page config is already set at the beginning of the file)
    apply_theme()
    
    # Check for a valid auth cookie if no token is present
    # This ensures we always check for valid cookies on page refresh
    if not st.session_state.get("token"):
        # Cookie validation - try to authenticate from cookie if available
        cookie_valid = cookie_is_valid(st.session_state.cookie_manager)
        if cookie_valid:
            # Verify the restored token with the backend
            # This ensures the token is still valid and not revoked
            try:
                verify_success, _ = await get_current_user()
                
                if not verify_success:
                    # Token from cookie is no longer valid
                    if DEBUG_MODE:
                        logging.debug("Token from cookie failed backend verification")
                    # Clear token and show login form
                    st.session_state.token = None
                    st.session_state.user = None
                    st.session_state.show_login = True
                    # Remove the invalid cookie
                    try:
                        st.session_state.cookie_manager.delete(COOKIE_NAME)
                    except Exception as e:
                        if DEBUG_MODE:
                            logging.debug(f"Failed to delete invalid cookie: {str(e)}")
                    st.warning("Your session has expired. Please log in again.")
                else:
                    # Mark as checked to differentiate initial login from refresh
                    st.session_state.auth_checked = True
                    
                    # Only show welcome message if this is first authentication (not on refresh)
                    if not st.session_state.get("auth_checked_welcomed") and verify_success:
                        st.success("Welcome back! You've been automatically logged in.")
                        st.session_state.auth_checked_welcomed = True
                    
                    # Ensure login flags are properly set
                    st.session_state.show_login = False
                    st.session_state.show_register = False
            except Exception as e:
                if DEBUG_MODE:
                    logging.error(f"Error verifying token from cookie: {str(e)}")
                # Don't clear token or cookie here - let's be conservative
                # The cookie might still be valid even if backend verification failed temporarily
                pass
    
    # Check if user is logged in via token, or if we have a valid cookie
    # We check for cookies directly here as a fallback in case verification failed 
    cookies = st.session_state.cookie_manager.get_all(key="auth_flow_cookies")
    has_auth_cookie = COOKIE_NAME in cookies
    
    if st.session_state.token or has_auth_cookie:
        # User is authenticated or has auth cookie - show main UI
        
        # After authentication, check if we need to restore a specific note
        # This happens when user refreshes while viewing a note
        if st.session_state.get("token") and st.session_state.get("_restore_note_id") and not st.session_state.get("current_note"):
            note_id = st.session_state.get("_restore_note_id")
            if DEBUG_MODE:
                logging.debug(f"Restoring note with ID: {note_id}")
            
            # Fetch the note data
            with st.spinner("Loading note..."):
                restored_note = await get_note(note_id)
                if restored_note:
                    st.session_state.current_note = restored_note
                    # Clear the restoration flag
                    del st.session_state._restore_note_id
                    if DEBUG_MODE:
                        logging.debug(f"Successfully restored note: {restored_note.get('title', 'Untitled')}")
                else:
                    # If we can't restore the note, clear the flag and show the notes list
                    if "_restore_note_id" in st.session_state:
                        del st.session_state._restore_note_id
                    st.warning("Could not restore the note you were viewing. Showing notes list instead.")
        
        # If user is logged in, render the top navigation instead of sidebar
        render_top_nav()
        
        # Handle main content area
        await main_content()
        
        # Update the auth cookie with current view state (to persist across refreshes)
        if "cookie_manager" in st.session_state and "user" in st.session_state and st.session_state.token:
            try:
                # Set expiration date for the cookie
                exp_date = dt.datetime.now(dt.UTC) + dt.timedelta(days=COOKIE_EXPIRY_DAYS)
                user_info = st.session_state.get("user", {})
                
                # Create JWT for the cookie with current view state
                cookie_token = token_encode(st.session_state.token, exp_date, user_info)
                
                # Set the cookie with the JWT
                st.session_state.cookie_manager.set(
                    COOKIE_NAME,
                    cookie_token,
                    expires_at=exp_date
                )
            except Exception as e:
                if DEBUG_MODE:
                    logging.error(f"Failed to update view state in auth cookie: {str(e)}")
    else:
        # No token and no auth cookie - show login/register forms
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
    else:
        # Handle edit form submission
        if st.session_state.get("_edit_note_submitted", False) and st.session_state.get("current_note"):
            note = st.session_state.get("current_note")
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
        
        # Handle delete confirmation
        if st.session_state.get("_delete_note_confirmed", False) and st.session_state.get("current_note"):
            note = st.session_state.get("current_note")
            with st.spinner("Deleting note..."):
                success = await delete_note(note.get("id"))
                
                if success:
                    # Set a flag to show success message after redirecting to notes list
                    st.session_state._show_delete_success = True
                    st.session_state.current_note = None
                    st.rerun()
                else:
                    st.error("Failed to delete note.")
            
            # Reset confirmation flag
            st.session_state._delete_note_confirmed = False
        
        # Show notes list or load notes if needed
        if st.session_state.get("notes") is None:
            with st.spinner("Loading notes..."):
                success = await get_notes()
        
        # Show delete success message if flag is set
        if st.session_state.pop("_show_delete_success", False):
            st.success("Note deleted successfully!")
        
        # Use the consolidated notes view component
        render_notes_view()


if __name__ == "__main__":
    asyncio.run(main()) 