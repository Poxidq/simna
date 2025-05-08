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
                <div style="margin: 0 auto; width: 150px;">
                    <button onclick="document.querySelector('#btn_add_first_note').click()" 
                            style="background-color: var(--primary-color); color: white; 
                                  border: none; padding: 10px 20px; border-radius: 4px; 
                                  cursor: pointer; width: 100%;">
                        Create Your First Note
                    </button>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        # Hidden button that will be clicked by JS
        if st.button("Create First Note", key="btn_add_first_note", help="Create your first note", 
                    type="primary", use_container_width=False):
            st.session_state.show_create_note = True
            st.rerun()
        
        # Hide the button with CSS
        st.markdown(
            """
            <style>
            #btn_add_first_note {
                display: none;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        return
    
    # Create a container for the notes with grid layout
    st.markdown(
        """
        <style>
        .notes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 16px;
            margin-top: 20px;
        }
        .note-card {
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .note-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }
        .translated-badge {
            display: inline-block;
            background-color: rgba(255, 107, 0, 0.1);
            color: var(--primary-color);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.7rem;
            margin-top: 8px;
        }
        </style>
        <div class="notes-grid">
        """, 
        unsafe_allow_html=True
    )
    
    # Display each note as a card
    for note in notes:
        note_id = note.get("id")
        title = note.get("title", "Untitled")
        content = note.get("content", "")
        is_translated = note.get("is_translated", False)
        
        # Truncate content for display
        preview = content[:100] + "..." if len(content) > 100 else content
        
        # Create a container for the note
        st.markdown(
            f"""
            <div class="note-card" onclick="parent.postMessage({{'type': 'note_click', 'note_id': {note_id}}}, '*')">
                <div class="note-card-title">{title}</div>
                <div class="note-card-content">{preview}</div>
                {"<div class='translated-badge'>🔄 Translated</div>" if is_translated else ""}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Close the notes container
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Handle note click via JavaScript
    st.markdown(
        """
        <script>
        window.addEventListener('message', function(e) {
            if (e.data.type === 'note_click') {
                const note_id = e.data.note_id;
                
                // Use Streamlit's setComponentValue to update session state
                if (window.Streamlit) {
                    window.Streamlit.setComponentValue({note_id: note_id});
                }
            }
        });
        </script>
        """,
        unsafe_allow_html=True
    )
    
    # Component to capture note clicks
    clicked_note = st.empty()
    note_click_value = clicked_note.text_input("", 
                                             label_visibility="collapsed", 
                                             key="_note_clicked_input")
    if note_click_value:
        try:
            # Parse the JSON value
            import json
            note_data = json.loads(note_click_value.replace("'", '"'))
            note_id = note_data.get("note_id")
            if note_id:
                # Find the note by ID
                selected_note = next((n for n in notes if n.get("id") == note_id), None)
                if selected_note:
                    st.session_state.current_note = selected_note
                    st.rerun()
        except Exception as e:
            # Silently handle parsing errors
            pass
    
    # Hide the input field with CSS
    st.markdown(
        """
        <style>
        [data-testid="stText"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True
    )


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
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.show_create_note = False
                st.rerun()
    
    return submit


def render_note_detail(note: Dict[str, Any]) -> None:
    """Render the detail view of a note.
    
    Args:
        note: The note to display.
    """
    note_id = note.get("id")
    title = note.get("title", "Untitled")
    content = note.get("content", "")
    is_translated = note.get("translated", False)
    
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
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.edit_mode = False
                    st.rerun()
    else:
        # Note detail view
        # Header with back button
        col1, col2, col3 = st.columns([1, 5, 1])
        
        # Note content
        st.markdown(
            f"""
            <div style="margin-bottom: 20px;">
                <h2>{title}</h2>
            </div>
            <div style="white-space: pre-wrap; margin-bottom: 30px;">
                {content}
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Display translated badge if applicable
        if is_translated:
            st.markdown(
                """
                <div style="margin-bottom: 20px; padding: 10px; border: 1px solid var(--primary-color); border-radius: 4px;">
                    <span style="color: var(--primary-color);">✓ This note has been translated from Russian to English</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Action buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("📝 Edit", use_container_width=True):
                st.session_state.edit_mode = True
                st.rerun()
        
        with col2:
            if not is_translated:
                if st.button("🔄 Translate", use_container_width=True, key="btn_translate"):
                    st.session_state._translate_note_requested = True
                    st.rerun()
        
        with col3:
            if st.button("🗑️ Delete", use_container_width=True):
                st.session_state._confirm_delete = True
        
        with col4:
            if st.button("◀️ Back", use_container_width=True):
                st.session_state.current_note = None
                st.rerun()
        
        # Delete confirmation dialog
        if st.session_state.get("_confirm_delete", False):
            st.warning("Are you sure you want to delete this note? This action cannot be undone.")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Yes, delete it", key="btn_confirm_delete", use_container_width=True):
                    st.session_state._delete_note_confirmed = True
                    st.session_state._confirm_delete = False
                    st.rerun()
            with col2:
                if st.button("Cancel", key="btn_cancel_delete", use_container_width=True):
                    st.session_state._confirm_delete = False
                    st.rerun() 