import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import get_db, Base
from config import Settings
import os

# Test database URL
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden dependencies."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_settings():
    """Test configuration settings."""
    return Settings(
        DATABASE_URL=SQLALCHEMY_TEST_DATABASE_URL,
        SECRET_KEY="test-secret-key",
        OPENAI_API_KEY="test-openai-key",
        GROK_API_KEY="test-grok-key",
        AI_PROVIDER="grok",
        GROK_BASE_URL="https://api.x.ai/v1",
        GROK_MODEL="grok-beta"
    )

@pytest.fixture
def mock_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "department": "Engineering",
        "password": "testpassword123"
    }

@pytest.fixture
def mock_admin_data():
    """Sample admin data for testing."""
    return {
        "email": "admin@company.com", 
        "name": "Admin User",
        "department": "IT",
        "password": "admin123",
        "role": "admin"
    }