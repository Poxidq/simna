"""
Main application entry point.

This module configures and runs the FastAPI application.
"""
import time
from typing import Any, Dict

from fastapi import Depends, FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from backend.app.api.api import api_router
from backend.app.core.config import settings
from backend.app.db.database import engine, get_db
from backend.app.db.models import Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Configure CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Middleware for request timing (performance monitoring)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Any) -> Any:
    """
    Middleware to measure and log request processing time.

    Args:
        request: The incoming request
        call_next: The next middleware or endpoint handler

    Returns:
        Response: The processed response
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    
    # Log if response time exceeds threshold
    if process_time > settings.MAX_API_RESPONSE_TIME_MS:
        print(f"SLOW API RESPONSE: {request.url.path} took {process_time:.2f}ms")
    
    return response


# Health check endpoint
@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Health check endpoint to verify API and database connectivity.

    Args:
        db: Database session

    Returns:
        dict: Health status information
    """
    try:
        # Execute a simple query to verify database connection
        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service is not healthy: {str(e)}"
        )


# Root endpoint
@app.get("/")
def root() -> Dict[str, str]:
    """
    Root endpoint.

    Returns:
        dict: Basic API information
    """
    return {
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=4,
    ) 