"""
Authentication service.

This module provides functions for user authentication and management.
"""
import os
import logging
import streamlit as st
from typing import Dict, Tuple, Any, Optional, Union, List, cast, TypeVar, Callable
from frontend.services.api import api_request


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth_service")

# Debug mode setting
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"


async def login(username: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Authenticate user and store token in session state.
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        Tuple[bool, Optional[str]]: Success status and optional error message
    """
    if not username or not password:
        st.error("Please enter both username and password")
        return False, "Please enter both username and password"
    
    with st.spinner("Logging in..."):
        try:
            response: Optional[Dict[str, Any]] = await api_request(
                "POST",
                "/auth/login",
                data={"username": username, "password": password}
            )
            
            if response and "access_token" in response:
                token: str = response["access_token"]
                
                if DEBUG_MODE:
                    token_preview = token[:10] + "..." if len(token) > 10 else token
                    logging.debug(f"Login successful. Token received: {token_preview}")
                
                # Store token in session state
                st.session_state.token = token
                
                # Get current user
                success, error_msg = await get_current_user()
                if success:
                    st.success("Login successful!")
                    return True, None
                else:
                    error_message = "Login successful, but couldn't fetch user information."
                    if DEBUG_MODE:
                        logging.error(f"Failed to get current user after login: {error_msg}")
                    
                    # Even though we can't get user info, we still have a token, so consider it a success
                    # but warn the user
                    st.warning(error_message)
                    return True, error_message
            
            # Handle failed login
            else:
                error_message = "Login failed. Please check your credentials."
                if DEBUG_MODE:
                    logging.error(f"Login failed. Response: {response}")
                # st.error(error_message)
                return False, error_message
                
        except Exception as e:
            error_message = f"Error during login: {str(e)}"
            if DEBUG_MODE:
                logging.exception("Login exception")
            # st.error(error_message)
            return False, error_message


async def register(username: str, email: str, password: str) -> bool:
    """
    Register a new user.

    Args:
        username: Username
        email: Email
        password: Password

    Returns:
        bool: Success status
    """
    try:
        with st.spinner("Creating your account..."):
            response: Optional[Dict[str, Any]] = await api_request(
                "POST", 
                "/auth/register", 
                data={"username": username, "email": email, "password": password}
            )
            
            if response:
                st.success("Registration successful! You can now log in.")
                # Debug info
                if DEBUG_MODE:
                    logger.debug(f"Registration success: {response}")
                return True
            else:
                # Registration failed, api_request has already displayed an error
                if DEBUG_MODE:
                    logger.error("Registration failed. Response was None.")
                return False
    except Exception as e:
        st.error(f"An unexpected error occurred")
        if DEBUG_MODE:
            logger.exception(f"Registration exception: {str(e)}")
        return False


async def get_current_user() -> Tuple[bool, Optional[str]]:
    """
    Get the current authenticated user.
    
    Returns:
        Tuple[bool, Optional[str]]: Success status and optional error message
    """
    if "token" not in st.session_state:
        if DEBUG_MODE:
            logging.debug("No token found in session state")
        return False, None
        
    token: str = st.session_state.token
    
    if DEBUG_MODE:
        # Only show first few chars for security
        token_preview = token[:10] + "..." if len(token) > 10 else token
        logging.debug(f"Using token for auth: {token_preview}")
    
    try:
        response: Optional[Dict[str, Any]] = await api_request(
            "GET", 
            "/auth/me", 
            token=token
        )
        
        if response and "email" in response:
            st.session_state.user = response
            return True, None
        else:
            if DEBUG_MODE:
                logging.debug(f"Failed to get user details. Response: {response}")
            return False, "Could not retrieve user details"
            
    except Exception as e:
        error_msg: str = str(e)
        if "401" in error_msg:
            # Token is likely expired or invalid
            if DEBUG_MODE:
                logging.debug(f"Authentication error (401): {error_msg}")
            # Clear the invalid token
            if "token" in st.session_state:
                del st.session_state.token
            if "user" in st.session_state:
                del st.session_state.user
            return False, "Your session has expired. Please log in again."
        
        if DEBUG_MODE:
            logging.debug(f"Error getting current user: {error_msg}")
        return False, f"Error fetching user data: {error_msg}"


def logout() -> None:
    """
    Logout the current user.
    
    Returns:
        None
    """
    if "token" in st.session_state:
        del st.session_state.token
    if "user" in st.session_state:
        del st.session_state.user
    
    # Debug info
    if DEBUG_MODE:
        logger.debug("User logged out")
    
    st.success("You have been logged out successfully.")
    
    # Force a rerun to update the UI
    st.rerun() 