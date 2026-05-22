"""Property-based tests for OAuth-only user password reset prevention.

Feature: google-oauth, Property 8: OAuth-Only User Password Reset Prevention
**Validates: Requirements 6.1**

Uses Hypothesis to generate OAuth-only users (auth_provider="google", password=NULL)
and verifies that request_password_reset raises HTTPException with status_code=400.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from db.models import User
from services.auth_service import request_password_reset


# In-memory SQLite for isolated testing
engine = create_engine("sqlite:///:memory:")
TestSession = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create and tear down the users table for each test."""
    User.__table__.create(bind=engine, checkfirst=True)
    yield
    User.__table__.drop(bind=engine, checkfirst=True)


# --- Strategies ---

# Valid email local parts: start with a letter, followed by alphanumeric/dots/underscores
email_local_parts = st.from_regex(r"[a-z][a-z0-9._]{0,15}", fullmatch=True)

# Valid email domains
email_domains = st.sampled_from([
    "example.com", "test.org", "mail.io", "user.dev",
    "company.co", "service.net", "app.xyz", "domain.com",
])

# Combine into valid emails
valid_emails = st.builds(
    lambda local, domain: f"{local}@{domain}",
    email_local_parts,
    email_domains,
)

# Non-empty google_ids (numeric strings mimicking real Google sub IDs)
valid_google_ids = st.from_regex(r"[0-9]{5,25}", fullmatch=True)


class TestOAuthOnlyPasswordResetPrevention:
    """Property 8: OAuth-Only User Password Reset Prevention.

    For any user with auth_provider="google" and password=NULL, a password reset
    request for that user's email SHALL return an HTTP 400 response indicating
    the account uses Google sign-in.

    **Validates: Requirements 6.1**
    """

    @given(
        email=valid_emails,
        google_id=valid_google_ids,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_oauth_only_user_password_reset_returns_400(self, email, google_id, setup_db):
        """Verify password reset raises HTTPException(400) for OAuth-only users.

        **Validates: Requirements 6.1**
        """
        db = TestSession()
        try:
            # Clean up any pre-existing user with this email or google_id
            # Use bulk delete to avoid lazy-loading relationships (resumes table)
            db.query(User).filter(
                (User.email == email) | (User.google_id == google_id)
            ).delete(synchronize_session="fetch")
            db.commit()

            # Create an OAuth-only user (auth_provider="google", password=None)
            oauth_user = User(
                email=email,
                password=None,
                google_id=google_id,
                auth_provider="google",
            )
            db.add(oauth_user)
            db.commit()
            db.refresh(oauth_user)

            # Act & Assert: request_password_reset should raise HTTPException(400)
            with pytest.raises(HTTPException) as exc_info:
                request_password_reset(email, db)

            assert exc_info.value.status_code == 400, (
                f"Expected status_code=400, got {exc_info.value.status_code}"
            )
            assert exc_info.value.detail == (
                "This account uses Google sign-in. Password reset is not available."
            ), f"Unexpected error detail: {exc_info.value.detail}"
        finally:
            # Cleanup using bulk delete to avoid lazy-loading relationships
            db.query(User).delete()
            db.commit()
            db.close()
