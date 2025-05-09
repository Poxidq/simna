"""
Authentication service.

This module provides authentication related functions.
"""
import datetime as dt
import logging
import os
import secrets
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

import jwt
import streamlit as st

from frontend.services.api import api_request

# Configure logging
logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG_MODE", "False").lower() == "true" else logging.INFO)
logger = logging.getLogger(__name__)

# Debug mode setting
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

# Check if in production environment
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"

# Load secrets from streamlit secrets.toml if available
def get_secret(key: str, default: Any = None) -> Any:
    """Get a secret from Streamlit's secrets or environment variables."""
    try:
        return st.secrets[key]
    except (KeyError, AttributeError):
        return os.getenv(key, default)

# Generate a secure random key for cookie encryption
def generate_secure_key(length: int = 32) -> str:
    """Generate a cryptographically secure random key of specified length."""
    return secrets.token_hex(length)

# Cookie settings
COOKIE_NAME = "notes_auth"
DEFAULT_KEY = "notes_app_cookie_key"
# Get cookie key from secrets or environment
COOKIE_KEY_FROM_CONFIG = get_secret("cookie_key", os.getenv("COOKIE_KEY"))

# Check if we need to generate a key or stop execution in production
if IS_PRODUCTION:
    if not COOKIE_KEY_FROM_CONFIG or COOKIE_KEY_FROM_CONFIG == DEFAULT_KEY:
        # In production, either generate a secure key or stop execution
        if get_secret("allow_generate_cookie_key", "False").lower() == "true":
            # Generate a secure random key
            COOKIE_KEY = generate_secure_key()
            logger.warning("SECURITY WARNING: Generated a random cookie key for this session. "
                           "Consider setting a permanent key in your secrets.toml file or environment variables.")
        else:
            # Stop execution with an error message
            error_msg = (
                "\n\n🔐 SECURITY ERROR: No secure cookie key provided in production.\n"
                "Please set a strong, unique cookie key using one of the following methods:\n"
                "1. Add 'cookie_key = \"your-secure-key\"' to .streamlit/secrets.toml\n"
                "2. Set the COOKIE_KEY environment variable\n"
                "3. Set 'allow_generate_cookie_key = true' in secrets.toml to auto-generate a key (not recommended)\n\n"
                "A strong key should be at least 32 characters long and not be the default value.\n"
            )
            logger.error(error_msg)
            st.error(error_msg)
            sys.exit(1)
    else:
        # Use the provided key
        COOKIE_KEY = COOKIE_KEY_FROM_CONFIG
else:
    # In development, use the configured key or default with a warning
    COOKIE_KEY = COOKIE_KEY_FROM_CONFIG or DEFAULT_KEY
    if COOKIE_KEY == DEFAULT_KEY:
        logger.warning("Using default cookie key in development. This is not secure for production.")

COOKIE_EXPIRY_DAYS = int(get_secret("cookie_expiry_days", os.getenv("COOKIE_EXPIRY_DAYS", "30")))
JWT_ALGORITHM = get_secret("jwt_algorithm", "HS256")


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
    # Include current page state in the token if available
    view_state = {}
    if "current_note" in st.session_state and st.session_state.current_note:
        # If viewing a note, store its ID
        if isinstance(st.session_state.current_note, dict) and "id" in st.session_state.current_note:
            view_state["current_note_id"] = st.session_state.current_note["id"]
    
    if "show_create_note" in st.session_state:
        view_state["show_create_note"] = st.session_state.show_create_note
        
    return jwt.encode(
        {
            "token": token,
            "name": user_info.get("username", ""),
            "user_id": user_info.get("id", ""),
            "email": user_info.get("email", ""),
            "exp_date": exp_date.timestamp(),
            "view_state": view_state  # Add view state to token
        },
        COOKIE_KEY,
        algorithm=JWT_ALGORITHM,
    )


def cookie_is_valid(cookie_manager) -> bool:
    """
    Check if the authentication cookie is valid.
    
    Args:
        cookie_manager: The cookie manager instance
        
    Returns:
        bool: True if the cookie is valid, False otherwise
    """
    try:
        # Get the cookie value
        cookies = cookie_manager.get_all(key="cookie_validation")
        if COOKIE_NAME not in cookies:
            if DEBUG_MODE:
                logging.debug("No auth cookie found")
            return False
            
        token_data = cookies[COOKIE_NAME]
        if not token_data:
            if DEBUG_MODE:
                logging.debug("Empty auth cookie")
            return False
        
        # Decode the JWT - handle all possible JWT errors explicitly
        try:
            token_info = jwt.decode(token_data, COOKIE_KEY, algorithms=[JWT_ALGORITHM])
            
            if DEBUG_MODE:
                logging.debug(f"Successfully decoded JWT token from cookie")
                if "exp_date" in token_info:
                    exp_time = dt.datetime.fromtimestamp(token_info["exp_date"]).strftime('%Y-%m-%d %H:%M:%S')
                    logging.debug(f"Token expiration date: {exp_time}")
                
        except jwt.ExpiredSignatureError:
            if DEBUG_MODE:
                logging.debug("JWT token has expired")
            # Delete the expired cookie
            try:
                cookie_manager.delete(COOKIE_NAME)
                if DEBUG_MODE:
                    logging.debug("Deleted expired cookie")
            except Exception as e:
                if DEBUG_MODE:
                    logging.debug(f"Failed to delete expired cookie: {str(e)}")
            return False
        except jwt.InvalidTokenError as e:
            if DEBUG_MODE:
                logging.debug(f"Invalid JWT token format: {str(e)}")
            try:
                cookie_manager.delete(COOKIE_NAME)
                if DEBUG_MODE:
                    logging.debug("Deleted invalid cookie")
            except Exception as delete_e:
                if DEBUG_MODE:
                    logging.debug(f"Failed to delete invalid cookie: {str(delete_e)}")
            return False
        except jwt.PyJWTError as e:
            if DEBUG_MODE:
                logging.debug(f"PyJWT error while decoding token: {str(e)}")
            try:
                cookie_manager.delete(COOKIE_NAME)
                if DEBUG_MODE:
                    logging.debug("Deleted invalid cookie")
            except Exception as delete_e:
                if DEBUG_MODE:
                    logging.debug(f"Failed to delete invalid cookie: {str(delete_e)}")
            return False
        except Exception as e:
            if DEBUG_MODE:
                logging.debug(f"Unexpected error decoding JWT: {str(e)}")
            return False
        
        # Check required token fields
        required_fields = ["token", "exp_date", "name", "user_id"]
        missing_fields = [field for field in required_fields if field not in token_info]
        
        if missing_fields:
            if DEBUG_MODE:
                logging.debug(f"JWT missing required fields: {', '.join(missing_fields)}")
            return False
        
        # Check expiration
        current_time = dt.datetime.now(dt.UTC).timestamp()
        if token_info["exp_date"] < current_time:
            if DEBUG_MODE:
                logging.debug(f"JWT expired: {token_info['exp_date']} < {current_time}")
                exp_time = dt.datetime.fromtimestamp(token_info["exp_date"]).strftime('%Y-%m-%d %H:%M:%S')
                now_time = dt.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
                logging.debug(f"Expired at {exp_time}, current time: {now_time}")
            
            # Delete the expired cookie
            try:
                cookie_manager.delete(COOKIE_NAME)
                if DEBUG_MODE:
                    logging.debug("Deleted expired cookie")
            except Exception as e:
                if DEBUG_MODE:
                    logging.debug(f"Failed to delete expired cookie: {str(e)}")
            return False
            
        # Set token in session state
        st.session_state.token = token_info["token"]
        
        # Store basic user info in session state
        if "user" not in st.session_state:
            st.session_state.user = {
                "id": token_info.get("user_id"),
                "username": token_info.get("name"),
                "email": token_info.get("email")
            }
        
        # When a valid cookie is found, ensure authentication UI state is correct
        # This guarantees the user won't see login/register forms
        st.session_state.show_login = False
        st.session_state.show_register = False
        
        # Restore view state if available
        if "view_state" in token_info and isinstance(token_info["view_state"], dict):
            view_state = token_info["view_state"]
            
            # Restore create note view if that's where they were
            if "show_create_note" in view_state:
                st.session_state.show_create_note = view_state["show_create_note"]
                
            # Restore current note if they were viewing one
            if "current_note_id" in view_state and view_state["current_note_id"]:
                # We'll need to fetch the note data on the next page load
                # Just marking that we need to restore this note
                st.session_state._restore_note_id = view_state["current_note_id"]
                
            if DEBUG_MODE:
                logging.debug(f"Restored view state from cookie: {view_state}")
                
        if DEBUG_MODE:
            logging.debug(f"Successfully restored session from cookie for user: {token_info.get('name', 'unknown')}")
        
        return True
    except Exception as e:
        if DEBUG_MODE:
            logging.exception(f"Unexpected cookie validation error: {str(e)}")
        # Be conservative - don't delete the cookie on unexpected errors
        # It might still be valid and the error could be transient
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
                # Store token in session state
                st.session_state.token = response["access_token"]
                
                # Clear any login errors
                if "login_error" in st.session_state:
                    del st.session_state.login_error
                
                # Get user details
                user_success, error = await get_current_user()
                if user_success:
                    logger.info(f"User logged in successfully: {st.session_state.get('user', {}).get('username', 'unknown')}")
                    return True, None
                else:
                    logger.error(f"Failed to fetch user details after login: {error}")
                    return False, error
            else:
                error_msg = "Invalid username or password"
                st.session_state.login_error = error_msg
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Login error: {str(e)}"
            logger.error(error_msg)
            st.session_state.login_error = error_msg
            return False, error_msg


async def register(username: str, email: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Register a new user.
    
    Args:
        username: User's username
        email: User's email
        password: User's password
        
    Returns:
        Tuple[bool, Optional[str]]: Success status and optional error message
    """
    if not username or not email or not password:
        error_msg = "Please fill in all required fields"
        st.session_state.register_error = error_msg
        return False, error_msg
    
    with st.spinner("Creating your account..."):
        try:
            response: Optional[Dict[str, Any]] = await api_request(
                "POST",
                "/auth/register",
                data={
                    "username": username,
                    "email": email,
                    "password": password
                }
            )
            
            if response and "id" in response:
                # Registration successful, now login
                st.success("Account created successfully! You may now log in.")
                return True, None
            else:
                if DEBUG_MODE:
                    logger.debug(f"Registration failed, response: {response}")
                error_msg = "Registration failed. Please try again."
                st.session_state.register_error = error_msg
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Registration error: {str(e)}"
            logger.error(error_msg)
            st.session_state.register_error = error_msg
            return False, error_msg


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
            
            # Update cookie with latest user info if we have a cookie manager
            if "cookie_manager" in st.session_state:
                try:
                    exp_date = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=COOKIE_EXPIRY_DAYS)
                    cookie_token = token_encode(token, exp_date, response)
                    # Use a unique key for this cookie operation
                    cookie_update_key = f"set_auth_cookie_{dt.datetime.now().timestamp()}"
                    st.session_state.cookie_manager.set(
                        COOKIE_NAME,
                        cookie_token,
                        expires_at=exp_date,
                        key=cookie_update_key
                    )
                    if DEBUG_MODE:
                        logging.debug(f"Updated auth cookie with expiration: {exp_date.isoformat()}")
                except Exception as e:
                    if DEBUG_MODE:
                        logging.error(f"Failed to update auth cookie: {str(e)}")
            
            return True, None
        else:
            if DEBUG_MODE:
                logging.debug(f"Failed to get user details. Response: {response}")
            
            # If we got a response but it's not what we expected, the token might be invalid
            # Clear token and cookie
            if "token" in st.session_state:
                del st.session_state.token
            if "user" in st.session_state:
                del st.session_state.user
                
            # Clear cookie if it exists since token is invalid
            if "cookie_manager" in st.session_state:
                try:
                    # Use a unique key for this cookie operation
                    cookie_delete_key = f"delete_auth_cookie_invalid_{dt.datetime.now().timestamp()}"
                    st.session_state.cookie_manager.delete(COOKIE_NAME, key=cookie_delete_key)
                    if DEBUG_MODE:
                        logging.debug("Deleted invalid auth cookie")
                except Exception as cookie_e:
                    if DEBUG_MODE:
                        logging.error(f"Failed to delete auth cookie: {str(cookie_e)}")
                        
            # Redirect to login
            st.session_state["show_login"] = True
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
                    # Use a unique key for this cookie operation
                    cookie_delete_key = f"delete_auth_cookie_expired_{dt.datetime.now().timestamp()}"
                    st.session_state.cookie_manager.delete(COOKIE_NAME, key=cookie_delete_key)
                    if DEBUG_MODE:
                        logging.debug("Deleted expired auth cookie")
                except Exception as cookie_e:
                    if DEBUG_MODE:
                        logging.error(f"Failed to delete auth cookie: {str(cookie_e)}")
            
            # Redirect to login
            st.session_state["show_login"] = True        
            return False, "Your session has expired. Please log in again."
        
        if DEBUG_MODE:
            logging.exception(f"Error getting current user: {error_msg}")
        return False, f"Error fetching user data: {error_msg}"


def logout() -> None:
    """
    Log out the current user by clearing session state and cookie.
    """
    try:
        # Clear session state
        if "token" in st.session_state:
            del st.session_state.token
        if "user" in st.session_state:
            del st.session_state.user
        if "auth_checked" in st.session_state:
            del st.session_state.auth_checked
            
        # Clear cookie
        if "cookie_manager" in st.session_state:
            try:
                # Use a unique key for this cookie operation
                cookie_delete_key = f"delete_auth_cookie_logout_{dt.datetime.now().timestamp()}"
                st.session_state.cookie_manager.delete(COOKIE_NAME, key=cookie_delete_key)
                if DEBUG_MODE:
                    logging.debug("Auth cookie deleted during logout")
            except Exception as e:
                if DEBUG_MODE:
                    logging.error(f"Failed to delete auth cookie: {str(e)}")
                    
        # Reset UI state
        st.session_state.show_login = True
        st.session_state.show_register = False
        
        # Clear any other app state
        if "notes" in st.session_state:
            del st.session_state.notes
        if "current_note" in st.session_state:
            del st.session_state.current_note
            
        if DEBUG_MODE:
            logger.debug("User logged out successfully")
        
        st.success("You have been logged out successfully.")
        st.rerun()
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return 