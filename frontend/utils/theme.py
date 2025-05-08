"""
Application theme configuration.

This module contains theme-related functions.
"""

import os
from typing import Dict, List, Any

import streamlit as st


def apply_custom_css() -> None:
    """Apply custom CSS to the application."""
    # Custom CSS for dark theme with orange accents
    custom_css = """
    /* Dark theme with orange accents */
    :root {
        --primary-color: #FF6B00;
        --background-color: #121212;
        --secondary-bg-color: #1E1E1E;
        --text-color: #E0E0E0;
        --border-color: #333333;
        --accent-color: #FF6B00;
        --error-color: #FF5252;
        --success-color: #4CAF50;
    }

    /* Base theme styles */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }

    /* Header styling */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-color);
    }
    
    h1 {
        color: var(--primary-color);
        font-weight: 600;
    }

    /* Button styling */
    .stButton button {
        background-color: var(--secondary-bg-color);
        color: var(--text-color);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        transition: all 0.3s ease;
    }

    .stButton button:hover {
        background-color: var(--primary-color);
        color: #FFFFFF;
        border-color: var(--primary-color);
    }

    /* Form and input styling */
    .stTextInput input, .stTextArea textarea {
        background-color: var(--secondary-bg-color);
        color: var(--text-color);
        border: 1px solid var(--border-color);
        border-radius: 4px;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--primary-color);
    }

    /* Divider styling */
    .stDivider {
        border-color: var(--border-color);
    }

    /* Card styling for notes */
    .note-card {
        background-color: var(--secondary-bg-color);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 10px;
        transition: all 0.2s ease;
    }

    .note-card:hover {
        border-color: var(--primary-color);
        box-shadow: 0 0 5px rgba(255, 107, 0, 0.3);
    }

    .note-card-title {
        color: var(--primary-color);
        font-weight: 600;
        margin-bottom: 5px;
    }

    .note-card-content {
        color: var(--text-color);
        font-size: 0.9rem;
    }

    /* Form submit button styling */
    .stForm button[type="submit"] {
        background-color: var(--primary-color);
        color: white;
        border: none;
        padding: 8px 16px;
        font-weight: 500;
        border-radius: 4px;
        transition: all 0.3s ease;
    }

    .stForm button[type="submit"]:hover {
        background-color: #FF8C00;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }
    
    /* Error messages */
    .stAlert {
        border: 1px solid var(--border-color);
        border-radius: 4px;
    }
    
    /* Widgets styling */
    .stWidgetLabel {
        color: var(--text-color) !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--secondary-bg-color);
        color: var(--text-color);
        border: 1px solid var(--border-color);
    }
    
    .streamlit-expanderContent {
        background-color: var(--secondary-bg-color);
        border: 1px solid var(--border-color);
        border-top: none;
    }
    """

    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)


def get_page_config() -> Dict[str, Any]:
    """
    Get page configuration settings.

    This function returns the configuration for st.set_page_config()
    and should be called at the very beginning of the app.

    Returns:
        Dict[str, Any]: Page configuration settings
    """
    favicon_path = os.path.join(os.path.dirname(__file__), "../assets/favicon.png")
    return {
        "page_title": "Notes App",
        "page_icon": favicon_path,
        "layout": "wide",
        "initial_sidebar_state": "expanded",
    }


def apply_theme() -> None:
    """
    Apply theme styling without setting page config.

    This function applies custom CSS, dark mode settings,
    and other theme-related configurations.
    Call this after st.set_page_config().
    """
    # Apply custom CSS
    apply_custom_css()

    # Always set dark mode in the session state
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True

    # Ensure consistent dark mode
    st.session_state.dark_mode = True

    # Disable all external connections and telemetry
    disable_external = """
    <script>
    // Block all external connections
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        // Allow only same-origin requests to go through
        if (typeof url === 'string') {
            const urlObj = new URL(url, window.location.origin);
            
            // Block any non-same-origin request
            if (urlObj.origin !== window.location.origin) {
                console.log('Blocked external connection to:', url);
                return Promise.resolve(new Response(JSON.stringify({status: 'ok'}), {
                    status: 200,
                    headers: {'Content-Type': 'application/json'}
                }));
            }
            
            // Additionally block known telemetry endpoints
            if (url.includes('fivetran') || 
                url.includes('telemetry') || 
                url.includes('analytics') ||
                url.includes('stats') ||
                url.includes('tracking') ||
                url.includes('collect') ||
                url.includes('usage') ||
                url.includes('metrics')) {
                console.log('Blocked telemetry connection to:', url);
                return Promise.resolve(new Response(JSON.stringify({status: 'ok'}), {
                    status: 200,
                    headers: {'Content-Type': 'application/json'}
                }));
            }
        }
        
        // Allow the request to proceed
        return originalFetch(url, options);
    };
    
    // Also override XMLHttpRequest
    const originalXHROpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
        // Block external XHR requests
        if (typeof url === 'string') {
            const urlObj = new URL(url, window.location.origin);
            if (urlObj.origin !== window.location.origin || 
                url.includes('fivetran') || 
                url.includes('telemetry') || 
                url.includes('analytics')) {
                console.log('Blocked XHR request to:', url);
                // Just don't open the connection
                return;
            }
        }
        return originalXHROpen.call(this, method, url, ...rest);
    };
    </script>
    """
    st.markdown(disable_external, unsafe_allow_html=True)

    # Force dark mode by injecting CSS
    force_dark_mode = """
    <style>
    /* Override light theme settings to force dark theme */
    .st-emotion-cache-j9baum, 
    .st-emotion-cache-ffhzg2,
    .st-emotion-cache-6qob1r,
    .st-emotion-cache-ue6h4q,
    .st-emotion-cache-zt5igj,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"] {
        background-color: #121212 !important;
        color: #FAFAFA !important;
    }
    
    /* Override for inputs, buttons, and other UI elements */
    input, textarea, button, select, .stTextInput, 
    .stNumberInput, .stDateInput, .stTimeInput, [data-testid="stForm"] {
        background-color: #262730 !important;
        color: #FAFAFA !important;
        border: 1px solid #4B4F5A !important;
    }
    
    /* Force all text to be light */
    p, h1, h2, h3, h4, h5, h6, span, div {
        color: #FAFAFA !important;
    }
    
    /* Orange accent for links and other elements */
    a, .stProgress > div, .stCheckbox > div {
        color: #FF6B00 !important;
    }
    </style>
    """
    st.markdown(force_dark_mode, unsafe_allow_html=True)

    # Initialize debug mode but don't show UI for it
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = (
            os.environ.get("DEBUG_MODE", "False").lower() == "true"
        )
