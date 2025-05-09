from locust import HttpUser, task, between
import random

class NotesAppUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login at the start of each user session
        response = self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            self.token = None
    
    @task(3)
    def get_notes(self):
        if self.token:
            self.client.get(
                "/api/v1/notes",
                headers={"Authorization": f"Bearer {self.token}"}
            )
    
    @task(2)
    def create_note(self):
        if self.token:
            self.client.post(
                "/api/v1/notes",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "title": f"Test Note {random.randint(1, 1000)}",
                    "content": "This is a test note content."
                }
            )
    
    @task(1)
    def translate_note(self):
        if self.token:
            # First get a list of notes
            response = self.client.get(
                "/api/v1/notes",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if response.status_code == 200:
                notes = response.json()
                if notes:
                    # Pick a random note to translate
                    note = random.choice(notes)
                    self.client.post(
                        f"/api/v1/notes/{note['id']}/translate",
                        headers={"Authorization": f"Bearer {self.token}"}
                    ) 