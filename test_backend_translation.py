#!/usr/bin/env python
"""
Backend Translation API Integration Test.

This script tests the note translation functionality through the backend API.
It creates a user, logs in, creates notes with Russian text, and tests the translation endpoint.
"""
import os
import sys
import json
import asyncio
import random
import string
import httpx
from typing import Dict, Any, Optional, List, Tuple

# Add the project root to sys.path to make imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import configuration settings
from backend.app.core.config import settings

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 10.0  # seconds

# Sample Russian texts for testing
RUSSIAN_TEXTS = [
    "Привет, мир! Это тестовая заметка.",
    "В этой заметке содержится русский текст, который должен быть переведен.",
    "Тестирование API перевода через backend endpoint.",
    "Проверка работы перевода с API ключом."
]


async def register_user() -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Register a test user."""
    print("\nRegistering test user...")
    
    # Generate random username and email
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    user_data = {
        "username": f"test_user_{random_suffix}",
        "email": f"test{random_suffix}@example.com",
        "password": "TestPassword123"
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{API_BASE_URL}/auth/register", json=user_data)
            
            if response.status_code == 201:
                user_info = response.json()
                print(f"✅ User registered: {user_info['username']}")
                return True, user_data
            else:
                print(f"❌ Registration failed: {response.status_code}")
                try:
                    print(f"Error: {response.json()}")
                except Exception:
                    print(f"Response: {response.text}")
                return False, None
    except Exception as e:
        print(f"❌ Registration failed with exception: {str(e)}")
        return False, None


async def login_user(username: str, password: str) -> Tuple[bool, Optional[str]]:
    """Login and get authentication token."""
    print("\nLogging in...")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{API_BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                token_data = response.json()
                token = token_data["access_token"]
                print("✅ Login successful")
                return True, token
            else:
                print(f"❌ Login failed: {response.status_code}")
                try:
                    print(f"Error: {response.json()}")
                except Exception:
                    print(f"Response: {response.text}")
                return False, None
    except Exception as e:
        print(f"❌ Login failed with exception: {str(e)}")
        return False, None


async def create_note(token: str, title: str, content: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Create a new note."""
    print(f"\nCreating note: {title}")
    
    note_data = {
        "title": title,
        "content": content
    }
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{API_BASE_URL}/notes", json=note_data, headers=headers)
            
            if response.status_code == 201:
                note_info = response.json()
                print(f"✅ Note created: {note_info['id']}")
                return True, note_info
            else:
                print(f"❌ Note creation failed: {response.status_code}")
                try:
                    print(f"Error: {response.json()}")
                except Exception:
                    print(f"Response: {response.text}")
                return False, None
    except Exception as e:
        print(f"❌ Note creation failed with exception: {str(e)}")
        return False, None


async def translate_note(token: str, note_id: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Translate a note."""
    print(f"\nTranslating note: {note_id}")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{API_BASE_URL}/notes/{note_id}/translate", headers=headers)
            
            if response.status_code == 200:
                translated_note = response.json()
                print(f"✅ Note translated")
                return True, translated_note
            else:
                print(f"❌ Translation failed: {response.status_code}")
                try:
                    print(f"Error: {response.json()}")
                except Exception:
                    print(f"Response: {response.text}")
                return False, None
    except Exception as e:
        print(f"❌ Translation failed with exception: {str(e)}")
        return False, None


async def test_backend_translation() -> None:
    """Run the backend translation test."""
    print("\n=== Backend Translation API Test ===\n")
    
    # Check if API key is set
    api_key = settings.RAPIDAPI_KEY
    if not api_key:
        print("❌ Error: RAPIDAPI_KEY is not set. Please provide an API key.")
        sys.exit(1)
    
    # Configure environment for the test
    os.environ["USE_MOCK_TRANSLATION"] = "False"
    os.environ["TESTING"] = "False"
    os.environ["RAPIDAPI_KEY"] = api_key
    
    # Start the backend test flow
    # 1. Register a user
    success, user_data = await register_user()
    if not success or not user_data:
        print("❌ Test failed at user registration step")
        return
    
    # 2. Login to get token
    success, token = await login_user(user_data["username"], user_data["password"])
    if not success or not token:
        print("❌ Test failed at login step")
        return
    
    # Store results for summary
    translation_results = []
    
    # 3. Create notes with Russian text and translate them
    for i, text in enumerate(RUSSIAN_TEXTS):
        # Create note
        note_title = f"Russian Note {i+1}"
        success, note_data = await create_note(token, note_title, text)
        if not success or not note_data:
            print(f"❌ Failed to create note {i+1}")
            translation_results.append((False, f"Note {i+1}"))
            continue
        
        # Print original content
        print(f"Original content: {note_data['content']}")
        
        # Translate note
        success, translated_note = await translate_note(token, note_data["id"])
        if not success or not translated_note:
            print(f"❌ Failed to translate note {i+1}")
            translation_results.append((False, f"Note {i+1}"))
            continue
        
        # Print translated content
        print(f"Translated content: {translated_note['content']}")
        
        # Verify translation worked
        if translated_note['is_translated'] and translated_note['content'] != text:
            print("✅ Translation verified")
            translation_results.append((True, f"Note {i+1}"))
        else:
            print("❌ Translation not verified")
            translation_results.append((False, f"Note {i+1}"))
    
    # Print summary
    success_count = sum(1 for result, _ in translation_results if result)
    print("\n=== Summary ===")
    print(f"Total tests: {len(translation_results)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(translation_results) - success_count}")
    
    for i, (success, description) in enumerate(translation_results):
        status = "✅" if success else "❌"
        print(f"{status} {description}")
    
    print("\nTest completed.")


if __name__ == "__main__":
    asyncio.run(test_backend_translation()) 