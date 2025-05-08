"""
Form validators.

This module provides functions for validating form inputs.
"""
import re
import streamlit as st
from typing import Optional, Union, Tuple, Any


def validate_note_form(title: str, content: str) -> bool:
    """
    Validate note form inputs.
    
    Args:
        title: Note title
        content: Note content
        
    Returns:
        bool: True if inputs are valid
    """
    if not title or not title.strip():
        st.error("Title is required")
        return False
    
    if len(title) > 100:
        st.error("Title must be 100 characters or less")
        return False
    
    if not content or not content.strip():
        st.error("Content is required")
        return False
    
    return True


def validate_login_form(username: str, password: str) -> bool:
    """
    Validate login form inputs.
    
    Args:
        username: Username
        password: Password
        
    Returns:
        bool: True if inputs are valid
    """
    if not username or not username.strip():
        st.error("Login > Username is required")
        return False
    
    if not password:
        st.error("Password is required")
        return False
    
    return True


def validate_register_form(username: str, email: str, password: str) -> bool:
    """
    Validate registration form inputs.
    
    Args:
        username: Username
        email: Email
        password: Password
        
    Returns:
        bool: True if inputs are valid
    """
    # Username validation
    if not username or not username.strip():
        st.error("Register > Username is required")
        return False
    
    if len(username) < 3:
        st.error("Username must be at least 3 characters")
        return False
    
    if len(username) > 50:
        st.error("Username must be 50 characters or less")
        return False
    
    # Username format (letters, numbers, underscores)
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        st.error("Username can only contain letters, numbers, and underscores")
        return False
    
    # Email validation
    if not email or not email.strip():
        st.error("Email is required")
        return False
    
    # Simple email format check
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        st.error("Please enter a valid email address")
        return False
    
    # Password validation
    if not password:
        st.error("Password is required")
        return False
    
    # Password strength requirements
    if len(password) < 8:
        st.error("Password must be at least 8 characters")
        return False
    
    if not any(c.isdigit() for c in password):
        st.error("Password must contain at least one digit")
        return False
    
    if not any(c.isupper() for c in password):
        st.error("Password must contain at least one uppercase letter")
        return False
    
    if not any(c.islower() for c in password):
        st.error("Password must contain at least one lowercase letter")
        return False
    
    return True 