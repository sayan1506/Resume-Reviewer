"""Unit tests for password reset prevention for OAuth-only users.

Tests cover:
- OAuth-only users (auth_provider="google", password=NULL) get HTTP 400
- Linked accounts (auth_provider="google", password NOT NULL) proceed normally
- Non-existent emails get generic success response
- Email-only users proceed normally
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from db.postgres import Base
from db.models import User
from services.auth_service import request_password_reset


# In-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestSession = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create only the users table."""
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


class TestOAuthOnlyUserRejection:
    """OAuth-only users (auth_provider='google', password=NULL) should be rejected."""

    def test_rejects_oauth_only_user_with_400(self, db):
        user = User(
            email="oauth@example.com",
            password=None,
            auth_provider="google",
            google_id="google_123",
        )
        db.add(user)
        db.commit()

        with pytest.raises(HTTPException) as exc_info:
            request_password_reset("oauth@example.com", db)

        assert exc_info.value.status_code == 400
        assert "Google sign-in" in exc_info.value.detail
        assert "not available" in exc_info.value.detail

    def test_error_message_matches_spec(self, db):
        user = User(
            email="googleonly@test.com",
            password=None,
            auth_provider="google",
            google_id="gid_456",
        )
        db.add(user)
        db.commit()

        with pytest.raises(HTTPException) as exc_info:
            request_password_reset("googleonly@test.com", db)

        assert exc_info.value.detail == "This account uses Google sign-in. Password reset is not available."


class TestLinkedAccountAllowed:
    """Linked accounts (auth_provider='google', password NOT NULL) should proceed."""

    def test_allows_linked_account_password_reset(self, db):
        user = User(
            email="linked@example.com",
            password="hashed_password_value",
            auth_provider="google",
            google_id="google_789",
        )
        db.add(user)
        db.commit()

        result = request_password_reset("linked@example.com", db)

        assert "message" in result
        assert "password reset link" in result["message"].lower()


class TestNonExistentEmail:
    """Non-existent emails should get generic success response."""

    def test_returns_generic_response_for_unknown_email(self, db):
        result = request_password_reset("nonexistent@example.com", db)

        assert "message" in result
        assert "password reset link" in result["message"].lower()

    def test_does_not_reveal_account_existence(self, db):
        # Create a real user
        user = User(
            email="real@example.com",
            password="hashed_pw",
            auth_provider="email",
        )
        db.add(user)
        db.commit()

        # Response for existing user
        result_existing = request_password_reset("real@example.com", db)
        # Response for non-existing user
        result_nonexistent = request_password_reset("fake@example.com", db)

        # Both should return the same generic message
        assert result_existing == result_nonexistent


class TestEmailOnlyUserAllowed:
    """Email-only users should proceed with normal password reset."""

    def test_allows_email_only_user_password_reset(self, db):
        user = User(
            email="emailuser@example.com",
            password="hashed_password",
            auth_provider="email",
        )
        db.add(user)
        db.commit()

        result = request_password_reset("emailuser@example.com", db)

        assert "message" in result
        assert "password reset link" in result["message"].lower()
