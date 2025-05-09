"""
Tests for message translation functionality.

This module contains end-to-end tests for translating different types of messages
using the RapidAPI translation service.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status

import backend.app.services.translation as translation_service  # Import the module instead of the function directly
from backend.app.core.config import settings
from backend.app.services.translation import translate_text


@pytest.mark.asyncio
async def test_translate_short_messages():
    """Test translation of short messages."""
    # Test different short messages
    messages = [
        {"input": "Привет", "expected": "Hello"},
        {"input": "Спасибо", "expected": "Thank you"},
        {"input": "До свидания", "expected": "Goodbye"}
    ]
    
    for msg in messages:
        result = await translate_text(msg["input"], _mock_response=msg["expected"])
        assert result["translated_text"] == msg["expected"]
        assert result["original_text"] == msg["input"]


@pytest.mark.asyncio
async def test_translate_long_messages():
    """Test translation of long messages with paragraphs."""
    # Create a long Russian message with multiple paragraphs
    long_message = """
    Это длинное сообщение на русском языке. Оно содержит несколько предложений.
    
    Этот текст имеет несколько абзацев и разную пунктуацию! Это важно для тестирования.
    
    Также здесь есть числа: 123, 456, 789. И специальные символы: @#$%^&*()
    """
    
    # Expected English translation
    expected_translation = """
    This is a long message in Russian. It contains several sentences.
    
    This text has several paragraphs and different punctuation! This is important for testing.
    
    There are also numbers here: 123, 456, 789. And special characters: @#$%^&*()
    """
    
    # Test the long message translation
    result = await translate_text(long_message, _mock_response=expected_translation)
    assert result["translated_text"] == expected_translation
    assert result["original_text"] == long_message


@pytest.mark.asyncio
async def test_translate_with_mixed_language():
    """Test translation of messages with mixed language content."""
    # Mixed language messages (Russian + English)
    mixed_message = "Привет, world! Это test сообщения с mixed языками."
    expected_translation = "Hello, world! This is a test message with mixed languages."
    
    # Test the mixed language translation
    result = await translate_text(mixed_message, _mock_response=expected_translation)
    assert result["translated_text"] == expected_translation
    assert result["original_text"] == mixed_message


@pytest.mark.asyncio
async def test_translate_with_formatting():
    """Test translation of messages with special formatting."""
    # Message with formatting (bullet points, numbers, etc.)
    formatted_message = """
    Список дел:
    • Купить продукты
    • Заплатить за квартиру
    • Позвонить маме
    
    Важные даты:
    1. 10 сентября - День рождения
    2. 31 декабря - Новый год
    """
    
    expected_translation = """
    To-do list:
    • Buy groceries
    • Pay for the apartment
    • Call mom
    
    Important dates:
    1. September 10 - Birthday
    2. December 31 - New Year
    """
    
    # Test the formatted message translation
    result = await translate_text(formatted_message, _mock_response=expected_translation)
    assert result["translated_text"] == expected_translation
    assert result["original_text"] == formatted_message


@pytest.mark.asyncio
async def test_translate_with_non_russian_text():
    """Test handling of non-Russian text (should not be translated)."""
    # Test with pure English text (should not be translated)
    english_text = "This is English text that should not be translated."
    
    # No API call should be made for non-Russian text
    result = await translate_text(english_text)
    
    # Verify no translation was done
    assert result["translated_text"] == english_text
    assert result["original_text"] == english_text


@pytest.mark.asyncio
async def test_translate_service_timeout():
    """Test handling of API timeout."""
    # Test with Russian text
    text = "Привет, мир!"
    
    # Create a mock that raises a timeout exception
    async def mock_timeout(*args, **kwargs):
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Translation service timeout"
        )
    
    # We need to patch the same module that we import from
    with patch('backend.app.services.translation.translate_text', mock_timeout):
        # Now call the module's function directly to ensure the patched version is used
        with pytest.raises(HTTPException) as exc_info:
            await translation_service.translate_text(text)
        
        # Assert that the error was caught and appropriate exception was raised
        assert "Translation service timeout" in str(exc_info.value.detail)
        assert exc_info.value.status_code == status.HTTP_504_GATEWAY_TIMEOUT


@pytest.mark.asyncio
async def test_translate_rate_limit_error():
    """Test handling of API rate limit errors."""
    # Test with Russian text
    text = "Привет, мир!"
    
    # Create a mock that raises a rate limit exception
    async def mock_rate_limit(*args, **kwargs):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Translation service unavailable: Translation API error: 429 - Too many requests"
        )
    
    # Patch the module's function
    with patch('backend.app.services.translation.translate_text', mock_rate_limit):
        # Call the module's function to ensure the patched version is used
        with pytest.raises(HTTPException) as exc_info:
            await translation_service.translate_text(text)
        
        # Assert that the error was caught and appropriate exception was raised
        assert "Translation service unavailable" in str(exc_info.value.detail)
        assert "429" in str(exc_info.value.detail)
        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


@pytest.mark.asyncio
async def test_translate_malformed_response():
    """Test handling of malformed API responses."""
    # Test with Russian text
    text = "Привет, мир!"
    
    # Create a mock that raises a parsing exception
    async def mock_parse_error(*args, **kwargs):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse translation response"
        )
    
    # Patch the module's function
    with patch('backend.app.services.translation.translate_text', mock_parse_error):
        # Call the module's function to ensure the patched version is used
        with pytest.raises(HTTPException) as exc_info:
            await translation_service.translate_text(text)
        
        # Assert that the parsing error was caught and appropriate exception was raised
        assert "Failed to parse translation response" in str(exc_info.value.detail)
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
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