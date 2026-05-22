"""Property-based test for duplicate Google ID conflict detection.

Feature: google-oauth, Property 5: Duplicate Google ID Conflict Detection
Validates: Requirements 3.5

For any two distinct user records where one already has a google_id set,
when find_or_create_oauth_user is called with a GoogleUserInfo containing
that same google_id but a different email matching the second user, the
operation SHALL raise an HTTP 409 error.
"""

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from db.postgres import Base
from db.models import User
from schemas.auth_schema import GoogleUserInfo
from services.oauth_service import find_or_create_oauth_user


# In-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestSession = sessionmaker(bind=engine)


# Strategy: generate valid email-like strings
email_local_parts = st.from_regex(r"[a-z][a-z0-9]{2,10}", fullmatch=True)
email_domains = st.sampled_from([
    "example.com", "test.org", "mail.io", "user.dev",
    "company.co", "service.net", "app.xyz", "domain.com",
])
email_strategy = st.builds(
    lambda local, domain: f"{local}@{domain}",
    email_local_parts,
    email_domains,
)

# Strategy: generate non-empty google_id strings (numeric, mimicking real Google sub IDs)
google_id_strategy = st.from_regex(r"[0-9]{5,25}", fullmatch=True)


class TestDuplicateGoogleIdConflict:
    """Property 5: Duplicate Google ID Conflict Detection.

    For any two distinct user records where one already has a google_id set,
    when find_or_create_oauth_user is called with a GoogleUserInfo containing
    that same google_id but a different email matching the second user, the
    operation SHALL raise an HTTP 409 error.

    **Validates: Requirements 3.5**
    """

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Create the users table before each test method and drop after."""
        User.__table__.create(bind=engine, checkfirst=True)
        yield
        User.__table__.drop(bind=engine, checkfirst=True)

    @given(
        email_a=email_strategy,
        email_b=email_strategy,
        shared_google_id=google_id_strategy,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_duplicate_google_id_raises_409(
        self, email_a, email_b, shared_google_id, setup_db
    ):
        """When User A already has a google_id, calling find_or_create_oauth_user
        with that same google_id but User B's email SHALL raise HTTP 409.

        Scenario:
        - User A exists with google_id="X" and email="a@test.com"
        - User B exists with email="b@test.com" (no google_id)
        - Call find_or_create_oauth_user with google_id="X" and email="b@test.com"
        - Expected: HTTPException with status_code=409

        **Validates: Requirements 3.5**
        """
        # Ensure the two emails are distinct
        assume(email_a != email_b)

        session = TestSession()
        try:
            # Clean slate for this iteration
            session.query(User).delete()
            session.commit()

            # Create User A with a google_id already set
            user_a = User(
                email=email_a,
                google_id=shared_google_id,
                auth_provider="google",
                password=None,
            )
            session.add(user_a)
            session.commit()

            # Create User B with a different email and no google_id
            user_b = User(
                email=email_b,
                google_id=None,
                auth_provider="email",
                password="hashed_password_placeholder",
            )
            session.add(user_b)
            session.commit()

            # Attempt to call find_or_create_oauth_user with User A's google_id
            # but User B's email — this should trigger 409 because the google_id
            # is already associated with a different user (User A)
            google_info = GoogleUserInfo(
                email=email_b,
                google_id=shared_google_id,
            )

            with pytest.raises(HTTPException) as exc_info:
                find_or_create_oauth_user(google_info, session)

            assert exc_info.value.status_code == 409
            assert "already linked" in exc_info.value.detail.lower()
        finally:
            session.rollback()
            session.close()
