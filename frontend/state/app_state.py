"""
Application state management.

This module contains the application state management functionality.
"""
from typing import Dict, List, Optional


class AppState:
    """Class to manage application state."""

    def __init__(self) -> None:
        """Initialize application state."""
        self.token: Optional[str] = None
        self.current_user: Optional[Dict] = None
        self.notes: List[Dict] = []
        self.current_note: Optional[Dict] = None
        self.show_new_note_form: bool = False
        self.edit_mode: bool = False
        self.show_register: bool = False 