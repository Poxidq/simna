"""
Performance tests using Locust.

This script tests the performance of the API endpoints under load.
Run with: locust -f backend/app/tests/performance_test.py
"""
import json
import random
from locust import HttpUser, task, between


class NotesAppUser(HttpUser):
    """
    Simulated user for load testing.
    
    This class represents a user performing typical operations
    in the Notes App.
    """
    
    # Wait between 1 and 5 seconds between tasks
    wait_time = between(1, 5)
    
    def on_start(self):
        """
        Initialize user session before starting tasks.
        
        This method registers a user and logs in to get an auth token.
        """
        # Register a new user with random username
        random_suffix = random.randint(1000, 9999)
        self.username = f"testuser{random_suffix}"
        self.password = "TestPassword123"
        self.email = f"test{random_suffix}@example.com"
        
        # Register
        self.client.post(
            "/api/v1/auth/register",
            json={
                "username": self.username,
                "email": self.email,
                "password": self.password,
            },
        )
        
        # Login and get token
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": self.username,
                "password": self.password,
            },
        )
        
        data = response.json()
        self.token = data.get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Created notes
        self.notes = []
    
    @task(2)
    def get_notes(self):
        """Get all user notes."""
        self.client.get("/api/v1/notes", headers=self.headers)
    
    @task(1)
    def create_note(self):
        """Create a new note."""
        note_num = len(self.notes) + 1
        response = self.client.post(
            "/api/v1/notes",
            headers=self.headers,
            json={
                "title": f"Test Note {note_num}",
                "content": f"This is test content for note {note_num}",
            },
        )
        
        if response.status_code == 201:
            note_data = response.json()
            self.notes.append(note_data["id"])
    
    @task(1)
    def get_single_note(self):
        """Get a specific note."""
        if self.notes:
            note_id = random.choice(self.notes)
            self.client.get(f"/api/v1/notes/{note_id}", headers=self.headers)
    
    @task(1)
    def update_note(self):
        """Update a note."""
        if self.notes:
            note_id = random.choice(self.notes)
            self.client.put(
                f"/api/v1/notes/{note_id}",
                headers=self.headers,
                json={
                    "title": f"Updated Note {note_id}",
                    "content": f"This content has been updated at {random.randint(1, 1000)}",
                },
            )
    
    @task(0.5)
    def translate_note(self):
        """Translate a note."""
        if self.notes:
            note_id = random.choice(self.notes)
            # First update the note to have Russian content
            self.client.put(
                f"/api/v1/notes/{note_id}",
                headers=self.headers,
                json={
                    "content": "Привет, мир!",
                },
            )
            # Then translate it
            self.client.post(
                f"/api/v1/notes/{note_id}/translate",
                headers=self.headers,
            )
    
    @task(0.2)
    def delete_note(self):
        """Delete a note."""
        if self.notes:
            note_id = self.notes.pop()
            self.client.delete(f"/api/v1/notes/{note_id}", headers=self.headers) 