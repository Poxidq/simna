"""
API service.

This module provides functions for communicating with the backend API.
"""

import os
import json
import logging
from typing import Dict, Optional, Tuple, List, Any, Union, TypeVar, cast, NoReturn

import httpx
import streamlit as st


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_service")

# Get secrets from Streamlit's secrets or environment variables
def get_secret(key: str, default: Any = None) -> Any:
    """Get a secret from Streamlit's secrets or environment variables."""
    try:
        return st.secrets[key]
    except (KeyError, AttributeError):
        return os.getenv(key, default)

# API configuration
API_BASE_URL = get_secret("api_base_url", os.getenv("API_BASE_URL", "http://localhost:8000/api/v1"))
DEBUG_MODE = get_secret("debug", os.getenv("DEBUG_MODE", "False").lower() == "true")

# TypeVar for generic API response
T = TypeVar("T")


def handle_api_error(error: httpx.HTTPStatusError) -> None:
    """
    Handle API errors and display appropriate error messages.

    Args:
        error: The HTTP status error from httpx
    """
    response = error.response
    status_code: int = response.status_code

    if DEBUG_MODE:
        logging.error(f"API Error {status_code}: {response.text}")

    try:
        # Try to parse error response as JSON
        error_data: Dict[str, Any] = response.json()

        # Check for different error formats
        if isinstance(error_data, dict):
            if "detail" in error_data:
                detail: Union[str, List[Dict[str, Any]]] = error_data["detail"]
                # Handle both string and list formats
                if isinstance(detail, list):
                    # Format validation errors
                    error_messages: List[str] = []
                    for error_item in detail:
                        if (
                            isinstance(error_item, dict)
                            and "loc" in error_item
                            and "msg" in error_item
                        ):
                            field = ".".join(
                                [
                                    str(loc_part)
                                    for loc_part in error_item["loc"]
                                    if loc_part != "body"
                                ]
                            )

                            # More user-friendly messages for common validation errors
                            if "password" in field:
                                if "at least one digit" in error_item["msg"]:
                                    error_messages.append(
                                        "Password must contain at least one digit"
                                    )
                                elif (
                                    "at least one uppercase letter" in error_item["msg"]
                                ):
                                    error_messages.append(
                                        "Password must contain at least one uppercase letter"
                                    )
                                elif (
                                    "at least one lowercase letter" in error_item["msg"]
                                ):
                                    error_messages.append(
                                        "Password must contain at least one lowercase letter"
                                    )
                                elif (
                                    "at least 8 characters" in error_item["msg"]
                                    or "shorter than" in error_item["msg"]
                                ):
                                    error_messages.append(
                                        "Password must be at least 8 characters long"
                                    )
                                else:
                                    error_messages.append(
                                        f"Password: {error_item['msg']}"
                                    )
                            elif "email" in field:
                                error_messages.append(
                                    "Please enter a valid email address"
                                )
                            elif "username" in field:
                                error_messages.append(f"Username: {error_item['msg']}")
                            else:
                                error_messages.append(f"{field}: {error_item['msg']}")
                        else:
                            error_messages.append(str(error_item))
                    error_message: str = " • ".join(error_messages)
                # else:
                # Handle common string error messages
                # error_message = str(detail)
                # if "username already registered" in error_message.lower():
                #     error_message = "This username is already taken"
                # elif "email already registered" in error_message.lower():
                #     error_message = "An account with this email already exists"

                # st.error(error_message)
                # return None
            else:
                # Just use the first key-value pair as the error
                first_key = next(iter(error_data))
                error_message = f"{first_key}: {error_data[first_key]}"
                st.error(error_message)
                return None

    except (json.JSONDecodeError, ValueError):
        # If it's not valid JSON, use the text content
        pass

    # Default error messages based on status code
    if status_code == 401:
        st.error("Authentication failed. Please log in again.")
        # Clear authentication state
        if "token" in st.session_state:
            del st.session_state.token
        if "user" in st.session_state:
            del st.session_state.user
    elif status_code == 403:
        st.error("You don't have permission to perform this action.")
    elif status_code == 404:
        st.error("The requested resource was not found.")
    elif status_code == 422:
        st.error("The request contains invalid data. Please check your input.")
    elif status_code >= 500:
        st.error("The server encountered an error. Please try again later.")
    else:
        pass
        # st.error(f"An error occurred: {response.text}")

    return None  # Explicit return


async def api_request(
    method: str,
    path: str,
    data: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 10,
) -> Optional[Dict[str, Any]]:
    """
    Make an API request to the backend.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: API endpoint path
        data: Request data
        token: Authentication token
        params: Query parameters
        timeout: Request timeout in seconds

    Returns:
        Optional[Dict[str, Any]]: API response data or None if an error occurred
    """
    try:
        # Construct full URL
        url: str = f"{API_BASE_URL}{path}"

        # Set up headers
        headers: Dict[str, str] = {"Content-Type": "application/json"}

        # Add authorization header if token is provided
        if token:
            # Ensure token has Bearer prefix
            if not token.startswith("Bearer "):
                token = f"Bearer {token}"
            headers["Authorization"] = token

        # Special logging for authentication endpoints
        is_auth_endpoint = path.startswith("/auth/")
        
        if DEBUG_MODE:
            # Make a copy of headers to avoid modifying the original
            safe_headers: Dict[str, str] = headers.copy()
            # Mask the token for security
            if "Authorization" in safe_headers:
                auth_token = safe_headers["Authorization"]
                if len(auth_token) > 15:
                    safe_headers["Authorization"] = (
                        auth_token[:10] + "..." + auth_token[-5:]
                    )

            logging.debug(f"API Request: {method} {url}")
            logging.debug(f"Headers: {safe_headers}")

            # Show complete request data for registration to help with debugging
            if path == "/auth/register":
                logging.debug(f"Registration data: {json.dumps(data)}")
            elif path == "/auth/login":
                # For login, just log the username but not the password
                if data and "username" in data:
                    logging.debug(f"Login attempt for user: {data['username']}")
            elif path == "/auth/me":
                logging.debug("Fetching current user details")
            elif data:
                # For other requests, limit data to first 100 chars
                logging.debug(f"Data: {json.dumps(data)[:100]}...")

            if params:
                logging.debug(f"Params: {params}")

        # Make the request
        async with httpx.AsyncClient(timeout=timeout) as client:
            response: httpx.Response
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "POST":
                response = await client.post(
                    url, headers=headers, json=data, params=params
                )
            elif method == "PUT":
                response = await client.put(
                    url, headers=headers, json=data, params=params
                )
            elif method == "DELETE":
                response = await client.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        if DEBUG_MODE:
            logging.debug(f"Response status: {response.status_code}")
            
            # Enhanced logging for auth endpoints
            if is_auth_endpoint:
                logging.debug(f"Auth endpoint response headers: {dict(response.headers)}")
                
                # For detailed debugging of authentication issues
                if path == "/auth/me":
                    if response.status_code == 200:
                        user_info = response.json()
                        logging.debug(f"Successfully retrieved user details: {user_info.get('username', 'unknown')}")
                    else:
                        logging.debug(f"Failed to get user details: {response.status_code}")
                elif path == "/auth/login":
                    if response.status_code == 200:
                        logging.debug("Login successful")
                    else:
                        logging.debug(f"Login failed with status: {response.status_code}")
            else:
                logging.debug(f"Response headers: {response.headers}")

            # Log complete response for registration
            if path == "/auth/register":
                try:
                    logging.debug(f"Registration response: {response.text}")
                except Exception as e:
                    logging.debug(f"Could not log registration response: {str(e)}")

        # Check if response is successful (2xx status code)
        response.raise_for_status()

        # Parse JSON response
        if response.text:
            # Use cast to explicitly tell mypy the type
            result: Dict[str, Any] = response.json()
            return result
        return None

    except httpx.HTTPStatusError as e:
        if DEBUG_MODE:
            if is_auth_endpoint:
                logging.error(
                    f"Authentication error ({path}): {e.response.status_code} - {e.response.text}"
                )
            elif "/auth/register" in path:
                logging.error(
                    f"Registration error: {e.response.status_code} - {e.response.text}"
                )
        handle_api_error(e)
        return None
    except httpx.TimeoutException:
        st.error("Request timed out. Please try again.")
        if DEBUG_MODE:
            logging.error(f"API request timed out for {path}")
        return None
    except Exception as e:
        # st.error(f"An error occurred: {str(e)}")
        if DEBUG_MODE:
            logging.exception(f"API request failed for {path}: {str(e)}")
        return None
