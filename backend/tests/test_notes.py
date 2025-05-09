import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, Note

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYpR1IOBYyGqK8y"  # "testpass"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_note(db_session, test_user):
    note = Note(
        title="Test Note",
        content="This is a test note",
        user_id=test_user.id
    )
    db_session.add(note)
    db_session.commit()
    return note

def test_create_note(client, test_user):
    # First login to get token
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Create a new note
    response = client.post(
        "/api/v1/notes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "New Test Note",
            "content": "This is a new test note"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Test Note"
    assert data["content"] == "This is a new test note"

def test_get_notes(client, test_user, test_note):
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Get notes
    response = client.get(
        "/api/v1/notes",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Note"

def test_translate_note(client, test_user, test_note):
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Translate note
    response = client.post(
        f"/api/v1/notes/{test_note.id}/translate",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "translated_text" in data 