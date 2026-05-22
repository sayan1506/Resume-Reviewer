"""Unit tests for find_or_create_oauth_user in oauth_service.py."""

import pytest
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

from db.postgres import Base
from db.models import User
from schemas.auth_schema import GoogleUserInfo
from services.oauth_service import find_or_create_oauth_user
from fastapi import HTTPException


# In-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestSession = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create only the users table (avoids JSONB incompatibility with SQLite)."""
    User.__table__.create(bind=engine, checkfirst=True)
    yield
    User.__table__.drop(bind=engine, checkfirst=True)


@pytest.fixture
def db():
    """Provide a test database session."""
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


class TestValidation:
    """Test input validation (HTTPException 400)."""

    def test_raises_400_when_google_id_is_empty(self, db):
        google_info = GoogleUserInfo(
            email="test@example.com",
            google_id="",
            name="Test User",
            avatar_url="https://example.com/avatar.png",
        )
        with pytest.raises(HTTPException) as exc_info:
            find_or_create_oauth_user(google_info, db)
        assert exc_info.value.status_code == 400
        assert "missing required information" in exc_info.value.detail.lower()


class TestNewUserCreation:
    """Test creating a new user when no matching email or google_id exists."""

    def test_creates_new_user_with_correct_fields(self, db):
        google_info = GoogleUserInfo(
            email="newuser@example.com",
            google_id="google123",
            name="New User",
            avatar_url="https://example.com/pic.png",
        )
        user = find_or_create_oauth_user(google_info, db)

        assert user.email == "newuser@example.com"
        assert user.google_id == "google123"
        assert user.avatar_url == "https://example.com/pic.png"
        assert user.auth_provider == "google"
        assert user.password is None

    def test_new_user_is_persisted_in_db(self, db):
        google_info = GoogleUserInfo(
            email="persist@example.com",
            google_id="google456",
        )
        find_or_create_oauth_user(google_info, db)

        found = db.query(User).filter(User.email == "persist@example.com").first()
        assert found is not None
        assert found.google_id == "google456"


class TestExistingGoogleUser:
    """Test returning existing user when google_id matches."""

    def test_returns_existing_user_by_google_id(self, db):
        # Pre-create a user with google_id
        existing = User(
            email="existing@example.com",
            google_id="existing_gid",
            auth_provider="google",
            password=None,
        )
        db.add(existing)
        db.commit()
        db.refresh(existing)

        google_info = GoogleUserInfo(
            email="existing@example.com",
            google_id="existing_gid",
        )
        user = find_or_create_oauth_user(google_info, db)

        assert user.id == existing.id
        assert user.email == "existing@example.com"


class TestAccountLinking:
    """Test linking Google account to existing email user."""

    def test_links_google_to_existing_email_user(self, db):
        # Pre-create an email-only user
        existing = User(
            email="emailuser@example.com",
            password="hashed_password_123",
            auth_provider="email",
        )
        db.add(existing)
        db.commit()
        db.refresh(existing)
        original_id = existing.id
        original_password = existing.password

        google_info = GoogleUserInfo(
            email="emailuser@example.com",
            google_id="link_gid",
            avatar_url="https://example.com/linked.png",
        )
        user = find_or_create_oauth_user(google_info, db)

        assert user.id == original_id
        assert user.google_id == "link_gid"
        assert user.avatar_url == "https://example.com/linked.png"
        assert user.auth_provider == "google"
        assert user.password == original_password  # Password preserved

    def test_raises_409_when_google_id_conflicts(self, db):
        # User A already has a different google_id
        user_a = User(
            email="usera@example.com",
            google_id="gid_a",
            auth_provider="google",
        )
        db.add(user_a)
        db.commit()

        # Try to link a different google_id to user A's email
        google_info = GoogleUserInfo(
            email="usera@example.com",
            google_id="gid_different",
        )
        with pytest.raises(HTTPException) as exc_info:
            find_or_create_oauth_user(google_info, db)
        assert exc_info.value.status_code == 409
        assert "already linked" in exc_info.value.detail.lower()
