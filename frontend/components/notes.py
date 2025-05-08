"""
Notes UI components.

This module contains UI components for displaying and interacting with notes.
"""
from typing import List, Dict, Any, Optional

import streamlit as st


def render_notes_list(notes: List[Dict[str, Any]]) -> None:
    """Render the list of notes."""
    # Header with title and add button in the same row
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("<h2>Your Notes</h2>", unsafe_allow_html=True)
    with col2:
        if st.button("➕ New Note", key="btn_add_note", use_container_width=True):
            st.session_state.show_create_note = True
            st.rerun()
    
    # Display message if no notes
    if not notes:
        st.markdown(
            """
            <div style="text-align: center; margin-top: 50px; margin-bottom: 50px; padding: 30px; 
                        border: 1px dashed var(--border-color); border-radius: 8px;">
                <p style="margin-bottom: 20px;">You don't have any notes yet.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        if st.button("Create Your First Note", key="btn_add_first_note", type="primary", use_container_width=False):
            st.session_state.show_create_note = True
            st.rerun()
        return
    
    # Display each note as a card
    for i, note in enumerate(notes):
        note_id = note.get("id")
        title = note.get("title", "Untitled")
        content = note.get("content", "")
        is_translated = note.get("is_translated", False)
        
        # Truncate content for display
        preview = content[:100] + "..." if len(content) > 100 else content
        
        # Create a card for the note
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"### {title}")
                st.markdown(preview)
                if is_translated:
                    st.markdown("<span style='background-color: rgba(255, 107, 0, 0.1); color: var(--primary-color); padding: 2px 6px; border-radius: 3px; font-size: 0.8rem;'>🔄 Translated</span>", unsafe_allow_html=True)
            with col2:
                if st.button("View", key=f"view_note_{i}", use_container_width=True):
                    st.session_state.current_note = note
                    st.rerun()
            st.divider()


def render_create_note_form() -> bool:
    """Render the create note form.
    
    Returns:
        bool: True if the form was submitted, False otherwise.
    """
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h2>Create New Note</h2>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Create note form
    with st.form(key="create_note_form", clear_on_submit=True):
        st.text_input("Title", key="note_title", placeholder="Note title")
        st.text_area("Content", key="note_content", height=200, placeholder="Write your note here...")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("Save", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
            if cancel:
                st.session_state.show_create_note = False
                st.rerun()
    
    return submit


def contains_russian(text: str) -> bool:
    """Check if text contains Russian characters.
    
    Args:
        text: The text to check
        
    Returns:
        bool: True if the text contains Russian characters, False otherwise
    """
    # Russian alphabet pattern (Cyrillic characters)
    russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
    return any(char in russian_chars for char in text)


def render_note_detail(note: Dict[str, Any]) -> None:
    """Render the detail view of a note.
    
    Args:
        note: The note to display.
    """
    # Validate that note is a dictionary
    if not isinstance(note, dict):
        st.error("Invalid note data. Please go back to the notes list.")
        if st.button("Back to Notes", key="back_from_invalid"):
            st.session_state.current_note = None
            st.rerun()
        return
    
    note_id = note.get("id")
    title = note.get("title", "Untitled")
    content = note.get("content", "")
    is_translated = note.get("is_translated", False)
    original_content = note.get("original_content", "")
    
    # Show edit form if in edit mode
    if st.session_state.get("edit_mode", False):
        st.markdown(
            """
            <div style="margin-bottom: 20px;">
                <h2>Edit Note</h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        with st.form(key="edit_note_form", clear_on_submit=False):
            st.text_input("Title", key="edit_note_title", value=title)
            st.text_area("Content", key="edit_note_content", value=content, height=300)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button("Save Changes", use_container_width=True)
                if submit:
                    st.session_state._edit_note_submitted = True
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
                if cancel:
                    st.session_state.edit_mode = False
                    st.rerun()
    else:
        # Note detail view
        st.markdown(f"## {title}")
        
        # Display content
        st.markdown(f"{content}")
        
        # Display translated badge and original content if applicable
        if is_translated and original_content:
            with st.expander("Show Original Russian Text", expanded=False):
                st.markdown(original_content)
        
        # Action buttons in rows
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Edit", key="edit_btn", use_container_width=True):
                st.session_state.edit_mode = True
                st.rerun()
        
        with col2:
            if st.button("◀️ Back to Notes", key="back_btn", use_container_width=True):
                st.session_state.current_note = None
                st.rerun()
        
        # Translation button only if content has Russian text and not already translated
        if contains_russian(content) and not is_translated:
            if st.button("🔄 Translate from Russian", key="translate_btn", use_container_width=True):
                st.session_state._translate_note_requested = True
        
        # Delete button
        if st.button("🗑️ Delete", key="delete_btn", use_container_width=True):
            st.session_state._confirm_delete = True
        
        # Delete confirmation dialog
        if st.session_state.get("_confirm_delete", False):
            st.warning("Are you sure you want to delete this note? This action cannot be undone.")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Yes, delete it", key="btn_confirm_delete", use_container_width=True):
                    st.session_state._delete_note_confirmed = True
                    st.session_state._confirm_delete = False
            with col2:
                if st.button("Cancel", key="btn_cancel_delete", use_container_width=True):
                    st.session_state._confirm_delete = False
                    st.rerun() 