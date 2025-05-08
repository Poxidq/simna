#!/usr/bin/env python
"""
Authentication Fix Verification Script.

This script verifies that our authentication fix is working by testing
a complete user workflow: registration, login, profile access, note creation,
and note manipulation.
"""
import os
import sys
import json
import time
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# API configuration
API_URL = "http://localhost:8000/api/v1"

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 50)
    print(f" {title} ")
    print("=" * 50 + "\n")


def register_user(username, email, password):
    """Register a new user."""
    print_section("1. REGISTERING USER")
    
    url = f"{API_URL}/auth/register"
    data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    logger.info(f"Request URL: {url}")
    logger.info(f"Request data: {data}")
    
    try:
        response = requests.post(url, json=data)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 201:
            logger.info("User registered successfully!")
            user_data = response.json()
            logger.info(f"User ID: {user_data.get('id')}")
            return user_data
        else:
            logger.error("Registration failed")
            try:
                logger.error(f"Response: {response.json()}")
            except json.JSONDecodeError:
                logger.error(f"Response text: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        return None


def login_user(username, password):
    """Login a user and get the JWT token."""
    print_section("2. LOGGING IN")
    
    url = f"{API_URL}/auth/login"
    data = {
        "username": username,
        "password": password
    }
    
    logger.info(f"Request URL: {url}")
    logger.info(f"Request data: {data}")
    
    try:
        response = requests.post(url, json=data)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Login successful!")
            token_data = response.json()
            access_token = token_data.get("access_token")
            token_type = token_data.get("token_type", "bearer")
            logger.info(f"Token type: {token_type}")
            
            # For security, only log partial token
            if access_token:
                token_preview = access_token[:10] + "..." if len(access_token) > 10 else access_token
                logger.info(f"Token: {token_preview}")
            
            return access_token
        else:
            logger.error("Login failed")
            try:
                logger.error(f"Response: {response.json()}")
            except json.JSONDecodeError:
                logger.error(f"Response text: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return None


def get_current_user(token):
    """Get current user information using the JWT token."""
    print_section("3. GETTING CURRENT USER")
    
    url = f"{API_URL}/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    logger.info(f"Request URL: {url}")
    
    # For security, only log partial token in header
    token_preview = token[:10] + "..." if len(token) > 10 else token
    logger.info(f"Authorization header: Bearer {token_preview}")
    
    try:
        response = requests.get(url, headers=headers)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("User information retrieved successfully!")
            user_data = response.json()
            logger.info(f"User data: {json.dumps(user_data, indent=2)}")
            return user_data
        else:
            logger.error("Failed to get user information")
            try:
                logger.error(f"Response: {response.json()}")
            except json.JSONDecodeError:
                logger.error(f"Response text: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting user information: {str(e)}")
        return None


def create_note(token, title, content):
    """Create a new note."""
    print_section("4. CREATING A NOTE")
    
    url = f"{API_URL}/notes"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "title": title,
        "content": content
    }
    
    logger.info(f"Request URL: {url}")
    logger.info(f"Request data: {data}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 201:
            logger.info("Note created successfully!")
            note_data = response.json()
            logger.info(f"Note ID: {note_data.get('id')}")
            logger.info(f"Note data: {json.dumps(note_data, indent=2)}")
            return note_data
        else:
            logger.error("Failed to create note")
            try:
                logger.error(f"Response: {response.json()}")
            except json.JSONDecodeError:
                logger.error(f"Response text: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error creating note: {str(e)}")
        return None


def update_note(token, note_id, updated_title, updated_content):
    """Update an existing note."""
    print_section("5. UPDATING THE NOTE")
    
    url = f"{API_URL}/notes/{note_id}"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "title": updated_title,
        "content": updated_content
    }
    
    logger.info(f"Request URL: {url}")
    logger.info(f"Request data: {data}")
    
    try:
        response = requests.put(url, json=data, headers=headers)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Note updated successfully!")
            note_data = response.json()
            logger.info(f"Updated note data: {json.dumps(note_data, indent=2)}")
            return note_data
        else:
            logger.error("Failed to update note")
            try:
                logger.error(f"Response: {response.json()}")
            except json.JSONDecodeError:
                logger.error(f"Response text: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error updating note: {str(e)}")
        return None


def delete_note(token, note_id):
    """Delete a note."""
    print_section("6. DELETING THE NOTE")
    
    url = f"{API_URL}/notes/{note_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    logger.info(f"Request URL: {url}")
    
    try:
        response = requests.delete(url, headers=headers)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 204:
            logger.info("Note deleted successfully!")
            return True
        else:
            logger.error("Failed to delete note")
            try:
                logger.error(f"Response: {response.json()}")
            except json.JSONDecodeError:
                logger.error(f"Response text: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error deleting note: {str(e)}")
        return False


def translate_note(token, note_id):
    """Translate a note."""
    print_section("7. TRANSLATING A NOTE")
    
    url = f"{API_URL}/notes/{note_id}/translate"
    headers = {"Authorization": f"Bearer {token}"}
    
    logger.info(f"Request URL: {url}")
    
    try:
        response = requests.post(url, headers=headers)
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Note translated successfully!")
            note_data = response.json()
            logger.info(f"Translated note data: {json.dumps(note_data, indent=2)}")
            return note_data
        else:
            logger.error("Failed to translate note")
            try:
                logger.error(f"Response: {response.json()}")
            except json.JSONDecodeError:
                logger.error(f"Response text: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error translating note: {str(e)}")
        return None


def main():
    """Main workflow verification function."""
    # User credentials
    username = f"verifyuser_{int(time.time())}"  # Use timestamp to ensure unique username
    email = f"{username}@example.com"
    password = "Verify123Password"
    
    print_section("AUTHENTICATION FIX VERIFICATION")
    logger.info("Starting verification of authentication workflow...")
    
    # 1. Register a new user
    user_data = register_user(username, email, password)
    if not user_data:
        logger.error("Verification failed at user registration step")
        sys.exit(1)
        
    user_id = user_data.get("id")
    logger.info(f"Registered user ID: {user_id}")
    
    # 2. Login to get a token
    token = login_user(username, password)
    if not token:
        logger.error("Verification failed at login step")
        sys.exit(1)
    
    # 3. Get user profile with token
    user_profile = get_current_user(token)
    if not user_profile:
        logger.error("Verification failed at get current user step")
        sys.exit(1)
        
    if user_profile.get("id") != user_id:
        logger.error(f"User ID mismatch: {user_profile.get('id')} != {user_id}")
        sys.exit(1)
    
    # 4. Create a note
    note_data = create_note(
        token,
        "Verification Test Note",
        "This is a test note created to verify authentication fix"
    )
    if not note_data:
        logger.error("Verification failed at note creation step")
        sys.exit(1)
        
    note_id = note_data.get("id")
    
    # 5. Update the note
    updated_note = update_note(
        token,
        note_id,
        "Updated Verification Note",
        "This note has been updated to verify the authentication workflow"
    )
    if not updated_note:
        logger.error("Verification failed at note update step")
        sys.exit(1)
    
    # 6. Create a note with Russian content for translation
    russian_note = create_note(
        token,
        "Russian Test Note",
        "Это тестовая заметка на русском языке"
    )
    if not russian_note:
        logger.error("Verification failed at Russian note creation step")
        sys.exit(1)
        
    russian_note_id = russian_note.get("id")
    
    # 7. Translate the Russian note
    translated_note = translate_note(token, russian_note_id)
    if not translated_note:
        logger.error("Verification failed at note translation step")
        sys.exit(1)
    
    # 8. Delete the notes
    if not delete_note(token, note_id):
        logger.error("Verification failed at note deletion step")
        sys.exit(1)
        
    if not delete_note(token, russian_note_id):
        logger.error("Verification failed at Russian note deletion step")
        sys.exit(1)
    
    print_section("VERIFICATION COMPLETE")
    logger.info("Authentication fix verification completed successfully!")
    logger.info("All tests passed - the fix is confirmed to be working")


if __name__ == "__main__":
    main() 