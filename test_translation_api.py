#!/usr/bin/env python
"""
Translation API Test Script.

This script tests the translation service with a real API key.
It sends requests directly to the translation API to verify functionality.
"""
import asyncio
import os
import sys
from typing import Dict, Any, List, Tuple

import httpx
import json

# Add the project root to sys.path to make imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the necessary modules from the application
from backend.app.services.translation import translate_text, is_russian_text
from backend.app.core.config import settings

# Sample texts for testing
TEST_TEXTS = [
    ("Привет, мир!", "Simple greeting"),
    ("Как дела? Что нового?", "Conversational phrase"),
    ("Это тестирование API перевода.", "Technical statement"),
    ("В Советском Союзе программирование программировало вас!", "Humor with cultural reference"),
    ("Длинный текст для проверки обработки больших объемов текста. " * 3, "Long text"),
]

# Mixed language text
MIXED_LANGUAGE_TEXT = "This is English text с небольшим количеством Russian words для тестирования."

# Non-Russian text
NON_RUSSIAN_TEXT = "This is pure English text without any Russian characters."

# Special characters
SPECIAL_CHARS_TEXT = "Привет! Как дела? 123 @#$%^&*()_+"


async def test_translation() -> None:
    """Run the translation tests with real API key."""
    print("\n=== Translation API Test ===\n")
    
    # Check if API key is set
    api_key = settings.RAPIDAPI_KEY
    if not api_key:
        print("❌ Error: RAPIDAPI_KEY is not set. Please provide an API key.")
        sys.exit(1)
    
    print(f"API URL: {settings.TRANSLATION_API_URL}")
    print(f"API Host: {settings.RAPIDAPI_HOST}")
    
    # Disable mock translation for this test
    os.environ["USE_MOCK_TRANSLATION"] = "False"
    os.environ["TESTING"] = "False"
    
    # Make sure we have the API key in the environment
    os.environ["RAPIDAPI_KEY"] = api_key
    
    print("\nRunning translation tests with real API...\n")
    
    # Test each sample text
    results = []
    for i, (text, description) in enumerate(TEST_TEXTS):
        print(f"Test {i+1}: {description}")
        print(f"  Original: {text}")
        
        try:
            response = await translate_text(text)
            print(f"  Translated: {response['translated_text']}")
            print(f"  Status: ✅ Success\n")
            results.append((True, description))
        except Exception as e:
            print(f"  Error: {str(e)}")
            print(f"  Status: ❌ Failed\n")
            results.append((False, description))
    
    # Test mixed language
    print("Test: Mixed Language")
    print(f"  Original: {MIXED_LANGUAGE_TEXT}")
    try:
        response = await translate_text(MIXED_LANGUAGE_TEXT)
        print(f"  Translated: {response['translated_text']}")
        print(f"  Status: ✅ Success\n")
        results.append((True, "Mixed language"))
    except Exception as e:
        print(f"  Error: {str(e)}")
        print(f"  Status: ❌ Failed\n")
        results.append((False, "Mixed language"))
    
    # Test non-Russian
    print("Test: Non-Russian Text")
    print(f"  Original: {NON_RUSSIAN_TEXT}")
    try:
        response = await translate_text(NON_RUSSIAN_TEXT)
        is_unchanged = response["translated_text"] == NON_RUSSIAN_TEXT
        print(f"  Translated: {response['translated_text']}")
        print(f"  Text unchanged: {is_unchanged}")
        print(f"  Status: ✅ Success\n")
        results.append((True, "Non-Russian"))
    except Exception as e:
        print(f"  Error: {str(e)}")
        print(f"  Status: ❌ Failed\n")
        results.append((False, "Non-Russian"))
    
    # Test special characters
    print("Test: Special Characters")
    print(f"  Original: {SPECIAL_CHARS_TEXT}")
    try:
        response = await translate_text(SPECIAL_CHARS_TEXT)
        print(f"  Translated: {response['translated_text']}")
        print(f"  Status: ✅ Success\n")
        results.append((True, "Special characters"))
    except Exception as e:
        print(f"  Error: {str(e)}")
        print(f"  Status: ❌ Failed\n")
        results.append((False, "Special characters"))
    
    # Test direct API call
    print("Test: Direct API Call")
    url = settings.TRANSLATION_API_URL
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": settings.RAPIDAPI_HOST,
    }
    payload = {
        "q": "Это прямой вызов API перевода.",
        "source": "ru",
        "target": "en",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                translated = result.get("data", {}).get("translations", {}).get("translatedText", "")
                
                print(f"  Original: {payload['q']}")
                print(f"  Translated: {translated}")
                print(f"  Status: ✅ Success\n")
                results.append((True, "Direct API call"))
            else:
                print(f"  Status Code: {response.status_code}")
                print(f"  Response: {response.text}")
                print(f"  Status: ❌ Failed\n")
                results.append((False, "Direct API call"))
    except Exception as e:
        print(f"  Error: {str(e)}")
        print(f"  Status: ❌ Failed\n")
        results.append((False, "Direct API call"))
    
    # Print summary
    success_count = sum(1 for result, _ in results if result)
    print("\n=== Summary ===")
    print(f"Total tests: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(results) - success_count}")
    
    for i, (success, description) in enumerate(results):
        status = "✅" if success else "❌"
        print(f"{status} {description}")
    
    print("\nTest completed.")


if __name__ == "__main__":
    asyncio.run(test_translation()) 