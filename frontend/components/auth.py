"""
Authentication components.

This module contains authentication UI components.
"""
import os
from typing import Tuple, Dict, Any, Optional

import streamlit as st

from frontend.state.app_state import AppState
from frontend.services.auth_service import logout as auth_logout


def render_login_form() -> None:
    """
    Render login form.
    """
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 30px; padding-top: 20px;">
            <h1>📝 Notes App</h1>
            <p>Securely manage your notes with translation capabilities</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Create a simple form with consistent styling
    with st.container():
        # Center the form
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form", clear_on_submit=False):
                st.text_input("Username", key="username", placeholder="Enter your username")
                st.text_input("Password", type="password", key="password", placeholder="Enter your password")
                
                st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                
                submit = st.form_submit_button("Login", use_container_width=True)
                
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                
                register_button = st.form_submit_button(
                    "Need an account? Register", 
                    use_container_width=True
                )
                
        if register_button:
            st.session_state.show_login = False
            st.session_state.show_register = True
            st.rerun()
        
        if submit:
            st.session_state._login_form_submitted = True
            st.rerun()


def render_register_form() -> None:
    """
    Render registration form.
    """
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 30px; padding-top: 20px;">
            <h1>📝 Notes App</h1>
            <p>Create an account to get started</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Create a simple form with consistent styling
    with st.container():
        # Center the form
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("register_form", clear_on_submit=False):
                st.text_input("Username", key="reg_username",
                            help="Choose a username (letters, numbers, and underscores only)",
                            placeholder="Choose a username")
                st.text_input("Email", key="reg_email",
                            help="Enter a valid email address",
                            placeholder="Enter your email")
                password_input = st.text_input("Password", type="password", key="reg_password",
                            help="At least 8 characters with digits, uppercase and lowercase letters",
                            placeholder="Choose a secure password")
                
                # Password strength hints
                if password_input:
                    password_strength = []
                    has_min_length = len(password_input) >= 8
                    has_digit = any(c.isdigit() for c in password_input)
                    has_upper = any(c.isupper() for c in password_input)
                    has_lower = any(c.islower() for c in password_input)
                    
                    password_strength.append("✅ At least 8 characters" if has_min_length else "❌ At least 8 characters")
                    password_strength.append("✅ At least one number" if has_digit else "❌ At least one number")
                    password_strength.append("✅ At least one uppercase letter" if has_upper else "❌ At least one uppercase letter")
                    password_strength.append("✅ At least one lowercase letter" if has_lower else "❌ At least one lowercase letter")
                    
                    st.caption("Password strength:")
                    for hint in password_strength:
                        st.caption(hint)
                
                st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                
                submit = st.form_submit_button("Register", use_container_width=True)
                
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                
                login_button = st.form_submit_button(
                    "Already have an account? Login", 
                    use_container_width=True
                )
        
        if login_button:
            st.session_state.show_register = False
            st.session_state.show_login = True
            st.rerun()
        
        if submit:
            if (not st.session_state.reg_username or 
                not st.session_state.reg_email or 
                not st.session_state.reg_password):
                st.error("Please fill out all fields")
            else:
                # Validate password requirements before submitting
                password = st.session_state.reg_password
                has_min_length = len(password) >= 8
                has_digit = any(c.isdigit() for c in password)
                has_upper = any(c.isupper() for c in password)
                has_lower = any(c.islower() for c in password)
                
                if not (has_min_length and has_digit and has_upper and has_lower):
                    error_msgs = []
                    if not has_min_length:
                        error_msgs.append("Password must be at least 8 characters")
                    if not has_digit:
                        error_msgs.append("Password must contain at least one digit")
                    if not has_upper:
                        error_msgs.append("Password must contain at least one uppercase letter")
                    if not has_lower:
                        error_msgs.append("Password must contain at least one lowercase letter")
                    
                    st.error(" • ".join(error_msgs))
                else:
                    st.session_state._register_form_submitted = True
                    st.rerun()


def render_top_nav() -> None:
    """Render the top navigation bar."""
    # Create a container for the top navigation
    with st.container():
        col1, col2, col3 = st.columns([6, 1, 1])
        
        # App logo in the left column
        with col1:
            st.markdown("<h3>📝 Notes App</h3>", unsafe_allow_html=True)
        
        # Notes button
        with col2:
            if st.button("📋 Notes", key="top_nav_notes", use_container_width=True):
                st.session_state.current_note = None
                st.session_state.show_create_note = False
                st.session_state.edit_mode = False
                st.rerun()
        
        # Logout button
        with col3:
            if st.button("🚪 Logout", key="top_nav_logout", use_container_width=True):
                # Clear user session state
                if "token" in st.session_state:
                    del st.session_state.token
                if "user" in st.session_state:
                    del st.session_state.user
                st.session_state.show_login = True
                auth_logout()
                st.rerun()
        
    # Add a separator
    st.divider() 