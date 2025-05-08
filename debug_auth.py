#!/usr/bin/env python
"""
Debug script for testing JWT token authentication.

This script logs in a user, extracts the JWT token, and tests the /auth/me endpoint.
"""
import os
import sys
import json
import time
import requests
import jwt
import logging
from base64 import b64decode

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# API configuration
API_URL = "http://localhost:8000/api/v1"

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 50)
    print(f" {title} ")
    print("=" * 50 + "\n")

def decode_jwt_segments(token):
    """Decode each segment of a JWT token without verification."""
    segments = token.split('.')
    
    if len(segments) != 3:
        logger.error(f"Invalid token format: expected 3 segments, got {len(segments)}")
        return None
    
    # Add padding if necessary
    def add_padding(segment):
        # Add padding characters
        mod = len(segment) % 4
        if mod:
            segment += '=' * (4 - mod)
        return segment
    
    try:
        # Decode header
        header_segment = segments[0]
        header_padding = add_padding(header_segment)
        header_bytes = b64decode(header_padding)
        header = json.loads(header_bytes)
        
        # Decode payload 
        payload_segment = segments[1]
        payload_padding = add_padding(payload_segment)
        payload_bytes = b64decode(payload_padding)
        payload = json.loads(payload_bytes)
        
        # Signature (just show raw)
        signature = segments[2]
        
        return {
            "header": header,
            "payload": payload,
            "signature": signature[:10] + "..." if len(signature) > 10 else signature
        }
    except Exception as e:
        logger.error(f"Error decoding JWT segments: {str(e)}")
        return None

def register_user(username, email, password):
    """Register a new user."""
    print_section("REGISTERING USER")
    
    url = f"{API_URL}/auth/register"
    data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    logger.info(f"Request URL: {url}")
    logger.info(f"Request data: {data}")
    
    try:
        response = requests.post(url, json=data)
        logger.info(f"Status code: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 201:
            logger.info("User registered successfully!")
            user_data = response.json()
            logger.info(f"User ID: {user_data.get('id')}")
            return user_data
        else:
            logger.error("Registration failed")
            try:
                logger.error(f"Response: {response.json()}")
            except json.JSONDecodeError:
                logger.error(f"Response text: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        return None

def login_user(username, password):
    """Login a user and get the JWT token."""
    print_section("LOGGING IN")
    
    url = f"{API_URL}/auth/login"
    data = {
        "username": username,
        "password": password
    }
    
    logger.info(f"Request URL: {url}")
    logger.info(f"Request data: {data}")
    
    try:
        response = requests.post(url, json=data)
        logger.info(f"Status code: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            logger.info("Login successful!")
            token_data = response.json()
            access_token = token_data.get("access_token")
            token_type = token_data.get("token_type")
            logger.info(f"Token type: {token_type}")
            logger.info(f"Raw token: {access_token}")
            
            # Detailed token inspection
            try:
                # Decode JWT segments
                jwt_details = decode_jwt_segments(access_token)
                if jwt_details:
                    logger.info(f"JWT Header: {json.dumps(jwt_details['header'], indent=2)}")
                    logger.info(f"JWT Payload: {json.dumps(jwt_details['payload'], indent=2)}")
                    logger.info(f"JWT Signature: {jwt_details['signature']}")
                    
                    # Additional payload details
                    payload = jwt_details['payload']
                    if 'sub' in payload:
                        logger.info(f"Subject (user ID): {payload['sub']}")
                    if 'exp' in payload:
                        exp_time = time.ctime(payload['exp'])
                        logger.info(f"Expiration: {exp_time} (timestamp: {payload['exp']})")
                        current_time = time.time()
                        logger.info(f"Current time: {time.ctime(current_time)} (timestamp: {int(current_time)})")
                        time_left = payload['exp'] - current_time
                        logger.info(f"Time until expiration: {int(time_left)} seconds")
                
                # Also decode with PyJWT for comparison
                decoded = jwt.decode(access_token, options={"verify_signature": False})
                logger.info(f"PyJWT decoded payload: {json.dumps(decoded, indent=2)}")
            except Exception as e:
                logger.error(f"Error inspecting token: {str(e)}")
                
            return access_token
        else:
            logger.error("Login failed")
            try:
                logger.error(f"Response: {response.json()}")
            except json.JSONDecodeError:
                logger.error(f"Response text: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return None

def get_current_user(token):
    """Get current user information using the JWT token."""
    print_section("GETTING CURRENT USER")
    
    url = f"{API_URL}/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    logger.info(f"Request URL: {url}")
    logger.info(f"Authorization header: Bearer {token[:10]}...")
    logger.debug(f"Full request headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
        logger.info(f"Status code: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            logger.info("User information retrieved successfully!")
            user_data = response.json()
            logger.info(f"User data: {json.dumps(user_data, indent=2)}")
            return user_data
        else:
            logger.error("Failed to get user information")
            logger.error(f"WWW-Authenticate header: {response.headers.get('www-authenticate', 'N/A')}")
            try:
                error_data = response.json()
                logger.error(f"Error response: {json.dumps(error_data, indent=2)}")
                return None
            except json.JSONDecodeError:
                logger.error(f"Response text: {response.text}")
                return None
    except Exception as e:
        logger.error(f"Error getting user information: {str(e)}")
        return None

def main():
    """Main function."""
    # User credentials
    username = "debuguser2"
    email = "debug2@example.com"
    password = "DebugPassword123"
    
    # Create a new user
    register_user(username, email, password)
    
    # Login and get token
    token = login_user(username, password)
    
    if token:
        # Try to get current user information
        get_current_user(token)
    else:
        logger.error("Cannot proceed without a valid token")
        sys.exit(1)

if __name__ == "__main__":
    main() 