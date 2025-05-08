"""
Tests package.

This package contains test modules for the application.
"""
import os

# Set environment variables for testing
os.environ["TESTING"] = "True"
os.environ["SECRET_KEY"] = "test_secret_key"
os.environ["DATABASE_URL"] = "sqlite:///./test.db" 