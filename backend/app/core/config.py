"""
Application configuration.

This module contains settings and configuration for the application.
"""
import os
from typing import Any, Dict, Optional

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings.

    This class contains all configuration variables for the application,
    with defaults and validation.
    """

    # Project information
    PROJECT_NAME: str = "Simple Notes App"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "A lightweight web-based application for note management"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./notes_app.db"
    )

    # Translation API
    TRANSLATION_API_URL: str = os.getenv(
        "TRANSLATION_API_URL", "https://deep-translate1.p.rapidapi.com/language/translate/v2"
    )
    RAPIDAPI_KEY: Optional[str] = os.getenv("RAPIDAPI_KEY")
    TRANSLATION_API_KEY: Optional[str] = RAPIDAPI_KEY
    RAPIDAPI_HOST: str = os.getenv("RAPIDAPI_HOST", "deep-translate1.p.rapidapi.com")
    
    # For testing - mock translation if True
    USE_MOCK_TRANSLATION: bool = os.getenv("USE_MOCK_TRANSLATION", "True").lower() == "true"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # Performance
    MAX_CONCURRENT_USERS: int = 20
    MAX_API_RESPONSE_TIME_MS: int = 200

    # Other
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    TESTING: bool = os.getenv("TESTING", "False").lower() == "true"

    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v: str) -> str:
        """Validate that the secret key is sufficiently strong in production."""
        # Skip validation during testing or development
        if os.getenv("TESTING", "False").lower() == "true":
            return v
            
        if os.getenv("ENVIRONMENT", "development") == "production" and v == "supersecretkey":
            raise ValueError("SECRET_KEY must be changed in production")
        
        if os.getenv("ENVIRONMENT", "development") == "production" and len(v) < 32:
            raise ValueError("SECRET_KEY should be at least 32 characters")
            
        return v

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = True


# Create a singleton settings instance
settings = Settings() 