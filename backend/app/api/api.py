"""
API router.

This module configures the main API router and includes all endpoint routers.
"""
from fastapi import APIRouter

from backend.app.api.endpoints import auth, notes

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router)
api_router.include_router(notes.router) 