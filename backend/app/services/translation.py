"""
Translation service.

This module provides functionality for translating text from Russian to English.
"""
import json
import re
from typing import Dict, Optional, Any, TypedDict, Union, cast

import httpx
from fastapi import HTTPException, status

from backend.app.core.config import settings


# Define a TypedDict for translation response
class TranslationResponse(TypedDict):
    """Type definition for translation response."""
    translated_text: str
    original_text: str
    source_language: str
    target_language: str


def is_russian_text(text: str) -> bool:
    """
    Check if text contains Russian characters.

    Args:
        text: The text to check

    Returns:
        bool: True if the text contains Russian characters
    """
    # Russian alphabet pattern
    russian_pattern = re.compile(r'[а-яА-ЯёЁ]')
    return bool(russian_pattern.search(text))


async def translate_text(
    text: str, 
    source_lang: str = "ru", 
    target_lang: str = "en",
    _mock_response: Optional[str] = None  # Added for testing
) -> TranslationResponse:
    """
    Translate text from Russian to English.

    Args:
        text: The text to translate
        source_lang: The source language code (default: ru)
        target_lang: The target language code (default: en)
        _mock_response: Mock response for testing (internal use only)

    Returns:
        TranslationResponse: Dictionary containing the translated text and metadata

    Raises:
        HTTPException: If translation fails
    """
    import logging
    logger = logging.getLogger(__name__)
    
    text_preview = text[:30] + "..." if len(text) > 30 else text
    logger.info(f"Translation requested: '{text_preview}' from {source_lang} to {target_lang}")
    
    # Handle empty text case
    if not text.strip():
        logger.info("Empty text, skipping translation")
        return {
            "translated_text": text,
            "original_text": text,
            "source_language": source_lang,
            "target_language": target_lang
        }
    
    # Skip translation if text doesn't contain Russian
    if not is_russian_text(text):
        logger.info("Text does not contain Russian characters, skipping translation")
        return {
            "translated_text": text,
            "original_text": text,
            "source_language": source_lang,
            "target_language": target_lang
        }

    # For testing: if a mock response is provided, return it immediately
    if _mock_response is not None:
        logger.info("Using mock response for translation")
        return {
            "translated_text": _mock_response,
            "original_text": text,
            "source_language": source_lang,
            "target_language": target_lang
        }
        
    # For development/testing purposes, mock translation if no API key or mock is enabled
    if settings.USE_MOCK_TRANSLATION or not settings.TRANSLATION_API_KEY or settings.TESTING:
        logger.info("Using simplified mock translation (USE_MOCK_TRANSLATION=True or missing API key)")
        # This is a simplified mock for development/testing only
        mock_translation = f"[Translated from {source_lang} to {target_lang}]: {text}"
        return {
            "translated_text": mock_translation,
            "original_text": text,
            "source_language": source_lang,
            "target_language": target_lang
        }
    
    # Prepare request to RapidAPI translation endpoint
    url: str = settings.TRANSLATION_API_URL
    logger.debug(f"Translation API URL: {url}")
    
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "x-rapidapi-key": settings.TRANSLATION_API_KEY[:5] + "..." if settings.TRANSLATION_API_KEY else None,
        "x-rapidapi-host": settings.RAPIDAPI_HOST,
    }
    
    payload: Dict[str, str] = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
    }
    
    logger.debug(f"Making translation API request with payload length: {len(text)}")
    
    try:
        # Make the API call
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.debug("Sending request to translation API")
            response: httpx.Response = await client.post(url, json=payload, headers=headers)
            logger.debug(f"Translation API response status: {response.status_code}")
            
            if response.status_code != 200:
                # Log the error details
                error_detail: str = f"Translation API error: {response.status_code}"
                try:
                    # Make sure to await the JSON response
                    error_body: Dict[str, Any] = await response.json()
                    if isinstance(error_body, dict):
                        error_detail += f" - {error_body.get('message', 'Unknown error')}"
                except Exception:
                    error_detail += f" - {response.text[:100]}"
                
                logger.error(error_detail)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Translation service unavailable: {error_detail}"
                )
            
            # Make sure to await the JSON response
            logger.debug("Parsing translation API response")
            result: Dict[str, Any] = await response.json()
            
            # Parse the RapidAPI response format
            translated_text: str = result.get("data", {}).get("translations", {}).get("translatedText", "")
            
            if not translated_text:
                logger.error("Failed to parse translation response")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to parse translation response"
                )
            
            logger.info("Translation successful")
            return {
                "translated_text": translated_text,
                "original_text": text,
                "source_language": source_lang,
                "target_language": target_lang
            }
    except httpx.TimeoutException:
        logger.error("Translation API timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Translation service timeout"
        )
    except httpx.RequestError as e:
        logger.error(f"Translation API request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Translation service unavailable: {str(e)}"
        ) 