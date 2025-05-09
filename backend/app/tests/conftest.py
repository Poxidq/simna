"""
Pytest fixtures for testing.

This module provides fixtures for testing the application.
"""
import asyncio
import json
import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
)
from backend.app.db.database import get_db
from backend.app.db.models import Base, Note, User
from backend.main import app

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a clean database session for testing.
    
    This fixture creates tables, yields a session, and drops tables after tests.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client for FastAPI application.
    
    This fixture overrides the dependency for database sessions.
    """
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass
    
    # Override the get_db dependency
    app.dependency_overrides[get_db] = _get_test_db
    
    # Create and return test client
    with TestClient(app) as c:
        yield c
    
    # Clear dependency overrides after test
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """
    Create a test user for authentication tests.
    
    This fixture creates a user in the database and returns it.
    """
    # Create test user
    hashed_password = hash_password("TestPassword123")
    db_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hashed_password
    )
    
    # Add to database
    db_session.add(db_user)
    db_session.commit()
    db_session.refresh(db_user)
    
    return db_user


@pytest.fixture(scope="function")
def test_user_token(test_user):
    """
    Create a JWT token for the test user.
    
    This fixture creates a token that can be used for authenticated requests.
    """
    # Create access token
    access_token = create_access_token(data={"sub": test_user.id})
    return access_token


@pytest.fixture(scope="function")
def authorized_client(client, test_user_token, test_user, db_session):
    """
    Create an authenticated test client.
    
    This fixture adds authorization headers to the test client and overrides the auth dependency.
    """
    # Override the get_current_user dependency to return our test user
    def override_get_current_user():
        return test_user
        
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    # Add authorization headers to client
    client.headers = {
        "Authorization": f"Bearer {test_user_token}",
        **client.headers
    }
    
    yield client
    
    # Clean up the dependency override after the test
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


@pytest.fixture(scope="function")
def test_notes(db_session, test_user):
    """
    Create test notes for the test user.
    
    This fixture creates notes in the database and returns them.
    """
    # Create test notes
    notes_data = [
        {
            "title": "Test Note 1",
            "content": "This is test content 1",
            "user_id": test_user.id
        },
        {
            "title": "Test Note 2",
            "content": "This is test content 2",
            "user_id": test_user.id
        },
        {
            "title": "Test Note 3 with Russian",
            "content": "Это тестовая заметка на русском языке",
            "user_id": test_user.id
        }
    ]
    
    # Create and add notes to database
    db_notes = []
    for note_data in notes_data:
        db_note = Note(**note_data)
        db_session.add(db_note)
        db_notes.append(db_note)
    
    db_session.commit()
    
    # Refresh notes to get IDs
    for note in db_notes:
        db_session.refresh(note)
    
    return db_notes


@pytest.fixture(scope="function")
def mock_rapidapi_translation():
    """
    Mock the RapidAPI translation service.
    
    This fixture returns a mock that simulates successful API responses.
    """
    # Save original settings
    import os
    original_mock_env = os.environ.get("USE_MOCK_TRANSLATION")
    original_test_env = os.environ.get("TESTING")
    
    # Set environment variables for testing
    os.environ["USE_MOCK_TRANSLATION"] = "False"  # Use the actual mocked httpx, not our simple mock
    os.environ["TESTING"] = "False"  # Disable testing mode to force using the API
    
    # Sample successful API response
    successful_response = {
        "data": {
            "translations": {
                "translatedText": "Hello, world!",
                "detectedSourceLanguage": "ru"
            }
        }
    }
    
    # Create a mock response with a status code
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = successful_response
    
    # Create a mock client
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post.return_value = mock_response
    
    # Apply the patch
    with patch("httpx.AsyncClient", return_value=mock_client):
        yield mock_client
    
    # Restore original environment variables
    if original_mock_env is not None:
        os.environ["USE_MOCK_TRANSLATION"] = original_mock_env
    else:
        os.environ.pop("USE_MOCK_TRANSLATION", None)
    
    if original_test_env is not None:
        os.environ["TESTING"] = original_test_env
    else:
        os.environ.pop("TESTING", None) 