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
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="color: var(--primary-color);">Notes App</h1>
            <p>Please log in to continue</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Create a centered form with columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form(key="login_form", clear_on_submit=False):
            st.text_input("Username", key="username", placeholder="Enter your username")
            st.text_input("Password", key="password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.form_submit_button("Login", on_click=lambda: setattr(st.session_state, "_login_form_submitted", True), use_container_width=True)
            with col2:
                st.form_submit_button("Register", on_click=lambda: switch_to_register(), use_container_width=True)


def render_register_form() -> None:
    """
    Render registration form.
    """
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="color: var(--primary-color);">Register Account</h1>
            <p>Create a new account</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Create a centered form with columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form(key="register_form", clear_on_submit=True):
            st.text_input("Username", key="reg_username", placeholder="Choose a username")
            st.text_input("Email", key="reg_email", placeholder="Enter your email")
            
            # Password with strength requirements
            st.text_input("Password", key="reg_password", type="password", placeholder="Choose a password")
            st.markdown(
                """
                <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 5px;">
                    Password must:
                    <ul>
                        <li>Be at least 8 characters long</li>
                        <li>Contain at least one uppercase letter</li>
                        <li>Contain at least one lowercase letter</li>
                        <li>Contain at least one number</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.form_submit_button("Register", on_click=lambda: setattr(st.session_state, "_register_form_submitted", True), use_container_width=True)
            with col2:
                st.form_submit_button("Back to Login", on_click=lambda: switch_to_login(), use_container_width=True)


def switch_to_register() -> None:
    """Switch to the registration form."""
    st.session_state.show_login = False
    st.session_state.show_register = True


def switch_to_login() -> None:
    """Switch to the login form."""
    st.session_state.show_login = True
    st.session_state.show_register = False


def render_top_nav() -> None:
    """Render the top navigation bar for authenticated users."""
    # Get current user info and ensure it's not None
    user_info = st.session_state.get("user", {}) or {}
    username = user_info.get("username", "User")
    
    # Create a clean layout using Streamlit native components
    col1, col2, col3 = st.columns([4, 1, 1])
    
    with col1:
        st.markdown("<h3 style='color: var(--primary-color); margin: 0;'>Notes App</h3>", unsafe_allow_html=True)
    
    with col2:
        if st.button("📝 Notes", key="notes_btn", use_container_width=True):
            st.session_state.current_note = None
            st.session_state.show_create_note = False
            st.session_state.show_profile = False
            st.rerun()
    
    with col3:
        # Create a dropdown menu using expander
        with st.expander(f"👤 {username}", expanded=False):
            st.button("👤 Profile", key="profile_btn", use_container_width=True, 
                      on_click=lambda: setattr(st.session_state, "show_profile", True))
            st.button("🚪 Logout", key="logout_btn", use_container_width=True, 
                      on_click=lambda: logout_user())
    
    # Add a separator
    st.divider()
    
    # Handle profile view if needed
    if st.session_state.get("show_profile", False):
        render_profile_view()


def logout_user() -> None:
    """Helper function to handle logout via the auth service."""
    from frontend.services.auth_service import logout
    logout()


def render_profile_view() -> None:
    """Render the user profile view."""
    user_info = st.session_state.get("user", {}) or {}
    username = user_info.get("username", "")
    email = user_info.get("email", "")
    
    # Profile card
    st.markdown("""
    <style>
    .profile-card {
        background-color: var(--secondary-bg-color);
        border-radius: 10px;
        padding: 20px;
        border: 1px solid var(--border-color);
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a profile card
    with st.container():
        st.markdown("<div class='profile-card'>", unsafe_allow_html=True)
        st.markdown("### User Profile", unsafe_allow_html=True)
        
        # User information
        st.markdown(f"**Username:** {username}")
        st.markdown(f"**Email:** {email}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Notes", key="back_to_notes", use_container_width=True):
            st.session_state.show_profile = False
            st.rerun()
    
    with col2:
        if st.button("Logout", key="profile_logout", use_container_width=True):
            logout_user() 