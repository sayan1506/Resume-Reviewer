"""Property-based test for incomplete Google profile rejection.

Feature: google-oauth, Property 7: Incomplete Google Profile Rejection
Validates: Requirements 2.5
"""

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from db.models import User
from schemas.auth_schema import GoogleUserInfo
from services.oauth_service import find_or_create_oauth_user


# In-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestSession = sessionmaker(bind=engine)


def get_fresh_session():
    """Create a fresh DB session for each Hypothesis example."""
    return TestSession()


@pytest.fixture(autouse=True)
def setup_db():
    """Create only the users table for each test."""
    User.__table__.create(bind=engine, checkfirst=True)
    yield
    User.__table__.drop(bind=engine, checkfirst=True)


# Strategy: generate valid-looking emails for use with model_construct
valid_emails = st.from_regex(r"[a-z]{3,10}@[a-z]{3,8}\.[a-z]{2,4}", fullmatch=True)

# Strategy: generate non-empty google_ids
valid_google_ids = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=1,
    max_size=50,
)

# Strategy: generate empty-ish values (empty string, None)
empty_or_none_strings = st.sampled_from(["", None])


class TestIncompleteProfileRejection:
    """Property 7: Incomplete Google Profile Rejection

    For any GoogleUserInfo where email is None/empty OR google_id is None/empty,
    calling find_or_create_oauth_user SHALL raise an HTTP 400 error indicating
    incomplete profile data, and no user record SHALL be created or modified.

    **Validates: Requirements 2.5**
    """

    @given(
        email=valid_emails,
        bad_google_id=empty_or_none_strings,
        name=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        avatar_url=st.one_of(st.none(), st.just("https://example.com/pic.png")),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_empty_or_none_google_id_raises_400(self, setup_db, email, bad_google_id, name, avatar_url):
        """GoogleUserInfo with None/empty google_id raises HTTPException(400).

        **Validates: Requirements 2.5**
        """
        db = get_fresh_session()
        try:
            # Use model_construct to bypass Pydantic validation and set google_id to None/empty
            google_info = GoogleUserInfo.model_construct(
                email=email,
                google_id=bad_google_id,
                name=name,
                avatar_url=avatar_url,
            )

            user_count_before = db.query(User).count()

            with pytest.raises(HTTPException) as exc_info:
                find_or_create_oauth_user(google_info, db)

            assert exc_info.value.status_code == 400
            assert "missing required information" in exc_info.value.detail.lower()

            # Verify no DB changes occurred
            user_count_after = db.query(User).count()
            assert user_count_after == user_count_before
        finally:
            db.close()

    @given(
        bad_email=empty_or_none_strings,
        google_id=valid_google_ids,
        name=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        avatar_url=st.one_of(st.none(), st.just("https://example.com/pic.png")),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_empty_or_none_email_raises_400(self, setup_db, bad_email, google_id, name, avatar_url):
        """GoogleUserInfo with None/empty email raises HTTPException(400).

        **Validates: Requirements 2.5**
        """
        db = get_fresh_session()
        try:
            # Use model_construct to bypass Pydantic EmailStr validation
            google_info = GoogleUserInfo.model_construct(
                email=bad_email,
                google_id=google_id,
                name=name,
                avatar_url=avatar_url,
            )

            user_count_before = db.query(User).count()

            with pytest.raises(HTTPException) as exc_info:
                find_or_create_oauth_user(google_info, db)

            assert exc_info.value.status_code == 400
            assert "missing required information" in exc_info.value.detail.lower()

            # Verify no DB changes occurred
            user_count_after = db.query(User).count()
            assert user_count_after == user_count_before
        finally:
            db.close()

    @given(
        bad_email=empty_or_none_strings,
        bad_google_id=empty_or_none_strings,
        name=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        avatar_url=st.one_of(st.none(), st.just("https://example.com/pic.png")),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_both_email_and_google_id_missing_raises_400(self, setup_db, bad_email, bad_google_id, name, avatar_url):
        """GoogleUserInfo with both email and google_id None/empty raises HTTPException(400).

        **Validates: Requirements 2.5**
        """
        db = get_fresh_session()
        try:
            google_info = GoogleUserInfo.model_construct(
                email=bad_email,
                google_id=bad_google_id,
                name=name,
                avatar_url=avatar_url,
            )

            user_count_before = db.query(User).count()

            with pytest.raises(HTTPException) as exc_info:
                find_or_create_oauth_user(google_info, db)

            assert exc_info.value.status_code == 400
            assert "missing required information" in exc_info.value.detail.lower()

            # Verify no DB changes occurred
            user_count_after = db.query(User).count()
            assert user_count_after == user_count_before
        finally:
            db.close()

    @given(
        email=valid_emails,
        bad_google_id=empty_or_none_strings,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_existing_users_not_modified_on_rejection(self, setup_db, email, bad_google_id):
        """Existing users in DB are not modified when incomplete profile is rejected.

        **Validates: Requirements 2.5**
        """
        db = get_fresh_session()
        try:
            # Check if user already exists (Hypothesis runs multiple examples per test)
            existing_user = db.query(User).filter(User.email == "existing@example.com").first()
            if not existing_user:
                existing_user = User(
                    email="existing@example.com",
                    google_id="existing_gid_123",
                    auth_provider="google",
                    password=None,
                )
                db.add(existing_user)
                db.commit()
                db.refresh(existing_user)

            original_id = existing_user.id
            original_google_id = existing_user.google_id
            original_email = existing_user.email

            # Attempt with incomplete profile
            google_info = GoogleUserInfo.model_construct(
                email=email,
                google_id=bad_google_id,
                name="Some Name",
                avatar_url=None,
            )

            with pytest.raises(HTTPException) as exc_info:
                find_or_create_oauth_user(google_info, db)

            assert exc_info.value.status_code == 400

            # Verify existing user was not modified
            db.refresh(existing_user)
            assert existing_user.id == original_id
            assert existing_user.google_id == original_google_id
            assert existing_user.email == original_email
        finally:
            db.close()
