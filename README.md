# Notes App

A lightweight web application for creating, managing, and translating notes with Russian to English translation capabilities.

## Features

- User Authentication with JWT
- Note Management (CRUD operations)
- Russian to English Translation
- Clean and modern UI

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

## Environment Variables

- `SECRET_KEY`: JWT token secret key
- `RAPIDAPI_KEY`: API key for RapidAPI translation service
- `USE_MOCK_TRANSLATION`: Set to "True" to use mock translations (default)
- `DEBUG`: Enable debug mode

## API Documentation

The API documentation is available at: http://localhost:8000/api/v1/docs

