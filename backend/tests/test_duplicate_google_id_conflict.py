"""Property-based test for duplicate Google ID conflict detection.

Feature: google-oauth, Property 5: Duplicate Google ID Conflict Detection
Validates: Requirements 3.5
"""

import pytest
from hypothesis import given, settings, assume
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
email_strategy = st.from_regex(
    r"[a-z][a-z0-9]{2,10}@[a-z]{3,8}\.(com|org|net)", fullmatch=True
)

# Strategy: generate non-empty google_id strings
google_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=5,
    max_size=50,
).filter(lambda s: s.strip() != "")


class TestDuplicateGoogleIdConflict:
    """Property 5: Duplicate Google ID Conflict Detection.

    For any two distinct user records where one already has a google_id set,
    when find_or_create_oauth_user is called with a GoogleUserInfo containing
    that same google_id but a different email matching the second user, the
    operation SHALL raise an HTTP 409 error.

    The actual conflict scenario in the implementation: User A has email "a@x.com"
    with google_id="gid_a". When GoogleUserInfo(email="a@x.com", google_id="gid_different")
    is passed, it should raise 409 because user A already has a different google_id linked.

    **Validates: Requirements 3.5**
    """

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Create the users table before each test method and drop after."""
        User.__table__.create(bind=engine, checkfirst=True)
        yield
        User.__table__.drop(bind=engine, checkfirst=True)

    @given(
        user_email=email_strategy,
        existing_google_id=google_id_strategy,
        new_google_id=google_id_strategy,
    )
    @settings(max_examples=100)
    def test_conflict_when_email_user_has_different_google_id(
        self, user_email, existing_google_id, new_google_id
    ):
        """When a user already has a google_id linked, attempting to link a different
        google_id to the same email raises HTTP 409.

        **Validates: Requirements 3.5**
        """
        # Ensure the two google_ids are actually different
        assume(existing_google_id != new_google_id)

        # Create a fresh session for each hypothesis example
        session = TestSession()
        try:
            # Clean slate for this iteration
            session.query(User).delete()
            session.commit()

            # Create User A with an existing google_id
            user_a = User(
                email=user_email,
                google_id=existing_google_id,
                auth_provider="google",
                password=None,
            )
            session.add(user_a)
            session.commit()
            session.refresh(user_a)

            # Attempt to call find_or_create_oauth_user with the same email
            # but a different google_id — this should trigger 409
            google_info = GoogleUserInfo(
                email=user_email,
                google_id=new_google_id,
            )

            with pytest.raises(HTTPException) as exc_info:
                find_or_create_oauth_user(google_info, session)

            assert exc_info.value.status_code == 409
            assert "already linked" in exc_info.value.detail.lower()
        finally:
            session.rollback()
            session.close()
