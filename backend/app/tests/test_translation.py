"""
Tests for translation service.

This module contains tests for text translation functionality.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status

from backend.app.core.config import settings
from backend.app.services.translation import is_russian_text, translate_text


def test_is_russian_text():
    """Test detection of Russian text."""
    # Test cases
    test_cases = [
        {
            "text": "Привет, мир!",
            "expected": True,
            "description": "Simple Russian text"
        },
        {
            "text": "Hello, world!",
            "expected": False,
            "description": "English text"
        },
        {
            "text": "Привет, world!",
            "expected": True,
            "description": "Mixed Russian and English"
        },
        {
            "text": "123456",
            "expected": False,
            "description": "Numbers only"
        },
        {
            "text": "",
            "expected": False,
            "description": "Empty string"
        },
        {
            "text": "   ",
            "expected": False,
            "description": "Whitespace only"
        }
    ]
    
    for case in test_cases:
        result = is_russian_text(case["text"])
        assert result == case["expected"], case["description"]


@pytest.mark.asyncio
async def test_translate_text_russian():
    """Test translation of Russian text with mock."""
    # Enable mock translation for this test
    settings.USE_MOCK_TRANSLATION = True
    
    # Test Russian text
    text = "Привет, мир!"
    result = await translate_text(text)
    
    # Assert response structure
    assert isinstance(result, dict)
    assert "translated_text" in result
    assert "original_text" in result
    assert "source_language" in result
    assert "target_language" in result
    
    # Assert content
    assert result["original_text"] == text
    assert result["source_language"] == "ru"
    assert result["target_language"] == "en"
    assert result["translated_text"] != text  # Should be different after translation
    
    # Reset mock setting
    settings.USE_MOCK_TRANSLATION = False


@pytest.mark.asyncio
async def test_translate_text_english():
    """Test translation of English text (should return unchanged)."""
    # Test English text
    text = "Hello, world!"
    result = await translate_text(text)
    
    # Assert response
    assert result["translated_text"] == text  # Should remain unchanged
    assert result["original_text"] == text
    assert result["source_language"] == "ru"
    assert result["target_language"] == "en"


@pytest.mark.asyncio
async def test_translate_text_empty():
    """Test translation of empty text."""
    # Test empty text
    text = ""
    result = await translate_text(text)
    
    # Assert response
    assert result["translated_text"] == text
    assert result["original_text"] == text


@pytest.mark.asyncio
async def test_translate_text_special_chars():
    """Test translation of text with special characters."""
    # Enable mock translation for this test
    settings.USE_MOCK_TRANSLATION = True
    
    # Test text with special characters
    text = "Привет! Как дела? 123"
    result = await translate_text(text)
    
    # Assert response
    assert result["translated_text"] != text
    assert result["original_text"] == text
    
    # Reset mock setting
    settings.USE_MOCK_TRANSLATION = False


@pytest.mark.asyncio
async def test_translate_text_long():
    """Test translation of long text."""
    # Enable mock translation for this test
    settings.USE_MOCK_TRANSLATION = True
    
    # Test long text
    text = "Это длинный текст на русском языке. " * 10
    result = await translate_text(text)
    
    # Assert response
    assert result["translated_text"] != text
    assert result["original_text"] == text
    assert len(result["translated_text"]) > 0
    
    # Reset mock setting
    settings.USE_MOCK_TRANSLATION = False


@pytest.mark.asyncio
async def test_rapidapi_translation():
    """Test integration with RapidAPI translation service using mock response parameter."""
    # Test with Russian text
    text = "Привет, мир!"
    expected_translation = "Hello, world!"
    
    # Use the _mock_response parameter which bypasses the HTTP client
    result = await translate_text(text, _mock_response=expected_translation)
    
    # Assert that we get the expected response
    assert result["translated_text"] == expected_translation
    assert result["original_text"] == text
    assert result["source_language"] == "ru"
    assert result["target_language"] == "en"


@pytest.mark.asyncio
async def test_httpx_client_integration():
    """Test the integration with httpx client using proper mocking."""
    # Create a proper AsyncMock for the response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    # Set up the json method to return a coroutine that resolves to the mock data
    mock_response.json = AsyncMock(return_value={
        "data": {
            "translations": {
                "translatedText": "Hello, world!",
                "detectedSourceLanguage": "ru"
            }
        }
    })
    
    # Create a mock for the httpx client
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
    
    # Override settings to ensure API call is made
    original_mock = settings.USE_MOCK_TRANSLATION
    original_testing = settings.TESTING
    original_api_key = settings.TRANSLATION_API_KEY
    
    settings.USE_MOCK_TRANSLATION = False
    settings.TESTING = False
    settings.TRANSLATION_API_KEY = "dummy_api_key"  # Ensure API key is not None
    
    try:
        # Apply the mock and test
        with patch("httpx.AsyncClient", return_value=mock_client):
            # Test with Russian text
            text = "Привет, мир!"
            result = await translate_text(text)
            
            # Verify the client was called correctly
            mock_post = mock_client.__aenter__.return_value.post
            mock_post.assert_called_once()
            
            # Check the call arguments
            call_args = mock_post.call_args[1]
            assert "json" in call_args
            assert call_args["json"]["q"] == text
            assert call_args["json"]["source"] == "ru"
            assert call_args["json"]["target"] == "en"
            
            # Check result
            assert result["translated_text"] == "Hello, world!"
            assert result["original_text"] == text
    finally:
        # Restore settings
        settings.USE_MOCK_TRANSLATION = original_mock
        settings.TESTING = original_testing
        settings.TRANSLATION_API_KEY = original_api_key


@pytest.mark.asyncio
async def test_rapidapi_translation_error():
    """Test handling of RapidAPI errors."""
    # Create a mock with an error response
    mock_response = AsyncMock()
    mock_response.status_code = 400
    # Make sure the json method returns a coroutine
    mock_response.json = AsyncMock(return_value={"message": "Invalid language code"})
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
    
    # Override settings to ensure API call is made
    original_mock = settings.USE_MOCK_TRANSLATION
    original_testing = settings.TESTING
    original_api_key = settings.TRANSLATION_API_KEY
    
    settings.USE_MOCK_TRANSLATION = False
    settings.TESTING = False
    settings.TRANSLATION_API_KEY = "dummy_api_key"  # Ensure API key is not None
    
    try:
        # Apply the mock and test
        with patch("httpx.AsyncClient", return_value=mock_client):
            # Test with Russian text
            text = "Привет, мир!"
            
            # Should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await translate_text(text)
            
            # Assert that the error was caught and raised
            assert "Translation service unavailable" in str(exc_info.value.detail)
            assert exc_info.value.status_code == 503  # SERVICE_UNAVAILABLE
    finally:
        # Restore settings
        settings.USE_MOCK_TRANSLATION = original_mock
        settings.TESTING = original_testing
        settings.TRANSLATION_API_KEY = original_api_key


@pytest.mark.asyncio
@pytest.mark.skip("Enable only for real API testing")
async def test_real_rapidapi_integration():
    """
    Test integration with actual RapidAPI service.
    
    This test is skipped by default as it requires a valid API key.
    Enable it by setting the ENABLE_REAL_API_TESTS environment variable.
    """
    import os
    if os.getenv("ENABLE_REAL_API_TESTS") != "True":
        pytest.skip("Skipping real API test. Set ENABLE_REAL_API_TESTS=True to enable.")
    
    # Ensure we're not using mock translations
    original_setting = settings.USE_MOCK_TRANSLATION
    settings.USE_MOCK_TRANSLATION = False
    
    try:
        # Simple Russian text
        text = "Привет, мир!"
        result = await translate_text(text)
        
        # Check that we got a valid translation
        assert result["translated_text"] != text
        assert result["translated_text"] != ""
        assert result["original_text"] == text
        assert "Hello" in result["translated_text"].lower()
    finally:
        # Restore original setting
        settings.USE_MOCK_TRANSLATION = original_setting 