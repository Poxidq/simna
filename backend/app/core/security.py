"""
Security utilities.

This module provides security-related functions such as password hashing,
JWT token creation and verification.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union, cast

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError, PyJWTError
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.database import get_db
from backend.app.db.models import User

# Setup logging
logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def hash_password(password: str) -> str:
    """
    Hash a password for secure storage.

    Args:
        password: The plaintext password to hash

    Returns:
        str: The hashed password as a string
    """
    # Generate a salt
    salt = bcrypt.gensalt()
    
    # Hash the password with the salt
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    
    # Return the hashed password as a string
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: The plaintext password to check
        hashed_password: The hashed password to check against

    Returns:
        bool: True if the password matches, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time delta

    Returns:
        str: The encoded JWT token
    """
    to_encode: Dict[str, Any] = data.copy()
    
    # Convert 'sub' to string if it exists and is not already a string
    if 'sub' in to_encode and not isinstance(to_encode['sub'], str):
        to_encode['sub'] = str(to_encode['sub'])
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    
    if settings.DEBUG:
        logger.debug(f"Creating token with payload: {to_encode}")
        
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    
    if settings.DEBUG:
        # Log the first 10 characters of the token
        logger.debug(f"Generated token: {encoded_jwt[:10]}...")
        
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token.

    Args:
        token: The JWT token to decode

    Returns:
        Dict[str, Any]: The decoded token data

    Raises:
        HTTPException: If the token is invalid
    """
    try:
        # Log token for debugging
        if settings.DEBUG:
            logger.debug(f"Decoding token: {token[:10]}... with algorithm {settings.ALGORITHM}")
            logger.debug(f"SECRET_KEY used for verification: {settings.SECRET_KEY[:5]}...")
            
        payload: Dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        
        if settings.DEBUG:
            logger.debug(f"Successfully decoded token payload: {payload}")
            
        return payload
    except jwt.ExpiredSignatureError as e:
        logger.error(f"Token expired: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except PyJWTError as e:
        logger.error(f"PyJWT error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during token decoding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user.

    Args:
        token: JWT token
        db: Database session

    Returns:
        User: The current authenticated user

    Raises:
        HTTPException: If the token is invalid or the user doesn't exist
    """
    try:
        # Log the token being processed if in debug mode
        if settings.DEBUG:
            logger.debug(f"Processing token in get_current_user: {token[:10]}...")
            
        payload: Dict[str, Any] = decode_token(token)
        user_id_str: Optional[str] = payload.get("sub")
        
        if settings.DEBUG:
            logger.debug(f"Extracted user_id from token: {user_id_str}")
        
        if user_id_str is None:
            logger.error("Token payload doesn't contain 'sub' (user_id)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials - missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Convert user_id to int if it's a string (necessary since we store it as a string in the token)
        user_id: int
        if isinstance(user_id_str, str):
            try:
                user_id = int(user_id_str)
            except ValueError:
                logger.error(f"Failed to convert user_id '{user_id_str}' to integer")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user ID format",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            # This shouldn't happen, but just in case
            user_id = cast(int, user_id_str)
            
    except HTTPException as e:
        logger.error(f"HTTP exception in get_current_user: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Query the database for the user
    if settings.DEBUG:
        logger.debug(f"Querying database for user with ID: {user_id}")
        
    user: Optional[User] = db.query(User).filter(User.id == user_id).first()
    
    if settings.DEBUG:
        if user is None:
            logger.debug(f"User with ID {user_id} not found in database")
        else:
            logger.debug(f"Found user: {user.username} (ID: {user.id})")
        
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.debug(f"User {user.username} (ID: {user.id}) is inactive")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user 