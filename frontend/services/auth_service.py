"""
Authentication service.

This module provides functions for user authentication and management.
"""
import os
import logging
import streamlit as st
import datetime as dt
import jwt
from typing import Dict, Tuple, Any, Optional, Union, List, cast, TypeVar, Callable
from frontend.services.api import api_request


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth_service")

# Debug mode setting
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

# Cookie settings
COOKIE_NAME = "notes_app_auth"
COOKIE_KEY = os.getenv("COOKIE_KEY", "notes_app_cookie_key")
COOKIE_EXPIRY_DAYS = 30


def token_encode(token: str, exp_date: dt.datetime, user_info: Dict[str, Any]) -> str:
    """
    Encodes a JSON Web Token (JWT) containing user session data for passwordless
    reauthentication.
    
    Args:
        token: The original API token
        exp_date: The expiration date of the JWT
        user_info: User information to store in the cookie
        
    Returns:
        str: The encoded JWT cookie string for reauthentication
    """
    return jwt.encode(
        {
            "token": token,
            "name": user_info.get("username", ""),
            "user_id": user_info.get("id", ""),
            "exp_date": exp_date.timestamp(),
        },
        COOKIE_KEY,
        algorithm="HS256",
    )


def cookie_is_valid(cookie_manager) -> bool:
    """
    Check if the reauthentication cookie is valid and, if it is, update the session state.
    
    Args:
        cookie_manager: A cookie manager instance
        
    Returns:
        bool: True if the cookie is valid and the session state is updated successfully
    """
    try:
        token_data = cookie_manager.get(COOKIE_NAME)
        if token_data is None:
            if DEBUG_MODE:
                logging.debug("No auth cookie found")
            return False
        
        # Decode the JWT
        token_info = jwt.decode(token_data, COOKIE_KEY, algorithms=["HS256"])
        
        # Check expiration
        if token_info["exp_date"] < dt.datetime.now(dt.UTC).timestamp():
            if DEBUG_MODE:
                logging.debug("Auth cookie expired")
            return False
        
        # Update session state
        st.session_state.token = token_info["token"]
        
        # Attempt to validate the token with a backend call
        success, _ = get_current_user()
        if success:
            if DEBUG_MODE:
                logging.debug("Successfully authenticated via cookie")
            return True
        else:
            if DEBUG_MODE:
                logging.debug("Cookie token is invalid on backend")
            return False
    except Exception as e:
        if DEBUG_MODE:
            logging.debug(f"Cookie validation error: {str(e)}")
        return False


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
                    # If login was successful, store the token in a cookie for persistent login
                    if "cookie_manager" in st.session_state:
                        try:
                            exp_date = dt.datetime.now(dt.UTC) + dt.timedelta(days=COOKIE_EXPIRY_DAYS)
                            user_info = st.session_state.get("user", {})
                            cookie_token = token_encode(token, exp_date, user_info)
                            
                            st.session_state.cookie_manager.set(
                                COOKIE_NAME,
                                cookie_token,
                                expires_at=exp_date
                            )
                            
                            if DEBUG_MODE:
                                logging.debug(f"Set auth cookie, expires: {exp_date}")
                        except Exception as cookie_e:
                            if DEBUG_MODE:
                                logging.error(f"Failed to set auth cookie: {str(cookie_e)}")
                    
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
            
            # Clear cookie if it exists since token is invalid
            if "cookie_manager" in st.session_state:
                try:
                    st.session_state.cookie_manager.delete(COOKIE_NAME)
                    if DEBUG_MODE:
                        logging.debug("Deleted invalid auth cookie")
                except Exception as cookie_e:
                    if DEBUG_MODE:
                        logging.error(f"Failed to delete auth cookie: {str(cookie_e)}")
                        
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
                
            # Clear cookie if it exists
            if "cookie_manager" in st.session_state:
                try:
                    st.session_state.cookie_manager.delete(COOKIE_NAME)
                    if DEBUG_MODE:
                        logging.debug("Deleted expired auth cookie")
                except Exception as cookie_e:
                    if DEBUG_MODE:
                        logging.error(f"Failed to delete auth cookie: {str(cookie_e)}")
                        
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
    
    # Delete the authentication cookie if it exists
    if "cookie_manager" in st.session_state:
        try:
            st.session_state.cookie_manager.delete(COOKIE_NAME)
            if DEBUG_MODE:
                logger.debug("Deleted auth cookie during logout")
        except Exception as e:
            if DEBUG_MODE:
                logger.error(f"Failed to delete auth cookie: {str(e)}")
    
    # Debug info
    if DEBUG_MODE:
        logger.debug("User logged out")
    
    st.success("You have been logged out successfully.")
    
    # Force a rerun to update the UI
    st.rerun() 