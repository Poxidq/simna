"""
Tests for authentication endpoints.

This module contains tests for user registration, login, and authentication.
"""
import pytest
from fastapi import status

from backend.app.core.security import hash_password


def test_register_success(client):
    """Test successful user registration."""
    # Prepare test data
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "Password123"
    }
    
    # Send registration request
    response = client.post("/api/v1/auth/register", json=user_data)
    
    # Assert response
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_username(client, test_user):
    """Test registration with duplicate username."""
    # Prepare test data with existing username
    user_data = {
        "username": test_user.username,  # Duplicate username
        "email": "different@example.com",
        "password": "Password123"
    }
    
    # Send registration request
    response = client.post("/api/v1/auth/register", json=user_data)
    
    # Assert response
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already registered" in response.json()["detail"]


def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email."""
    # Prepare test data with existing email
    user_data = {
        "username": "differentuser",
        "email": test_user.email,  # Duplicate email
        "password": "Password123"
    }
    
    # Send registration request
    response = client.post("/api/v1/auth/register", json=user_data)
    
    # Assert response
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email already registered" in response.json()["detail"]


def test_register_invalid_password(client):
    """Test registration with invalid password."""
    # Test cases for invalid passwords
    test_cases = [
        {
            "description": "Password too short",
            "password": "Abc123",
            "expected_status": status.HTTP_422_UNPROCESSABLE_ENTITY
        },
        {
            "description": "Password without digits",
            "password": "Abcdefghij",
            "expected_status": status.HTTP_422_UNPROCESSABLE_ENTITY
        },
        {
            "description": "Password without uppercase",
            "password": "abcdefg123",
            "expected_status": status.HTTP_422_UNPROCESSABLE_ENTITY
        },
        {
            "description": "Password without lowercase",
            "password": "ABCDEFG123",
            "expected_status": status.HTTP_422_UNPROCESSABLE_ENTITY
        }
    ]
    
    for case in test_cases:
        # Prepare test data
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": case["password"]
        }
        
        # Send registration request
        response = client.post("/api/v1/auth/register", json=user_data)
        
        # Assert response
        assert response.status_code == case["expected_status"], case["description"]


def test_login_success(client, test_user):
    """Test successful login."""
    # Prepare login data
    login_data = {
        "username": test_user.username,
        "password": "TestPassword123"
    }
    
    # Send login request
    response = client.post("/api/v1/auth/login", json=login_data)
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_username(client):
    """Test login with wrong username."""
    # Prepare login data with wrong username
    login_data = {
        "username": "nonexistentuser",
        "password": "TestPassword123"
    }
    
    # Send login request
    response = client.post("/api/v1/auth/login", json=login_data)
    
    # Assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_wrong_password(client, test_user):
    """Test login with wrong password."""
    # Prepare login data with wrong password
    login_data = {
        "username": test_user.username,
        "password": "WrongPassword123"
    }
    
    # Send login request
    response = client.post("/api/v1/auth/login", json=login_data)
    
    # Assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect username or password" in response.json()["detail"]


def test_get_me(authorized_client, test_user):
    """Test getting current user information."""
    # Send request to /auth/me endpoint
    response = authorized_client.get("/api/v1/auth/me")
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id


def test_get_me_unauthorized(client):
    """Test getting current user information without authentication."""
    # Send request without authentication
    response = client.get("/api/v1/auth/me")
    
    # Assert response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 