# Notes App

A lightweight web application for creating, managing, and translating notes with Russian to English translation capabilities.

## Features

- User Authentication with JWT and Persistent Login via Cookies
- Note Management (CRUD operations)
- Russian to English Translation
- Clean and modern UI with dark and orange theme

## Authentication Features

The app now supports persistent authentication using JWT cookies, allowing users to:
- Stay logged in across browser sessions
- Securely authenticate without needing to re-enter credentials
- Access user profile information
- Safely logout and clear authentication state

## Environment Variables

- `SECRET_KEY`: JWT token secret key
- `COOKIE_KEY`: Secret key for JWT cookie encryption (defaults to "notes_app_cookie_key" if not set)
- `COOKIE_EXPIRY_DAYS`: Number of days until authentication cookies expire (defaults to 30 days)
- `RAPIDAPI_KEY`: API key for RapidAPI translation service
- `USE_MOCK_TRANSLATION`: Set to "True" to use mock translations (default)
- `DEBUG`: Enable debug mode

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/notes_app.git
cd notes_app

# Start with Docker Compose
docker-compose up -d

# Access the application
# Backend API: http://localhost:8000
# Frontend: http://localhost:8501
```

### Manual Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/notes_app.git
cd notes_app

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend (in one terminal)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Start the frontend (in another terminal)
streamlit run frontend/app.py
```

## Testing

Run the tests with:

```bash
# Run all tests
python -m pytest backend/app/tests/

# Run specific test modules
python -m pytest backend/app/tests/test_auth.py
python -m pytest backend/app/tests/test_notes.py
python -m pytest backend/app/tests/test_translation.py

# Run user flow test (requires backend to be running)
./test_user_flow.sh
```

## Security Notes

- Set a strong, unique `COOKIE_KEY` in your environment variables or secrets.toml file
- The JWT cookie authentication is designed to enhance user experience while maintaining security
- All authentication tokens are validated with the backend on each page load

## API Documentation

The API documentation is available at: http://localhost:8000/api/v1/docs

