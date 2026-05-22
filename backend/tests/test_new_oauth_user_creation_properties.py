"""Property-based tests for new OAuth user creation.

Feature: google-oauth, Property 1: New OAuth User Creation Invariants
Validates: Requirements 1.2, 2.1, 2.2, 2.4, 4.5
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis import HealthCheck

from db.models import User, Resume
from schemas.auth_schema import GoogleUserInfo
from services.oauth_service import find_or_create_oauth_user


# In-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestSession = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create users and resumes tables for each test (resumes needed for relationship lazy-loading)."""
    User.__table__.create(bind=engine, checkfirst=True)
    Resume.__table__.create(bind=engine, checkfirst=True)
    yield
    Resume.__table__.drop(bind=engine, checkfirst=True)
    User.__table__.drop(bind=engine, checkfirst=True)


# --- Strategies ---

# Generate valid email local parts (alphanumeric, no leading/trailing dots or consecutive dots)
email_local_parts = st.from_regex(r"[a-z][a-z0-9]{0,10}[a-z0-9]", fullmatch=True)

# Generate valid email domains
email_domains = st.sampled_from([
    "example.com", "test.org", "mail.io", "user.dev",
    "company.co", "service.net", "app.xyz",
])

# Combine into valid emails
valid_emails = st.builds(
    lambda local, domain: f"{local}@{domain}",
    email_local_parts,
    email_domains,
)

# Generate non-empty google_ids (numeric strings like real Google sub IDs)
valid_google_ids = st.from_regex(r"[0-9]{5,30}", fullmatch=True)

# Generate optional names
optional_names = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=100).filter(lambda s: s.strip() != ""),
)

# Generate optional avatar URLs
optional_avatar_urls = st.one_of(
    st.none(),
    st.builds(
        lambda path: f"https://lh3.googleusercontent.com/{path}",
        st.from_regex(r"[a-zA-Z0-9_-]{5,30}", fullmatch=True),
    ),
)


@st.composite
def valid_google_user_info(draw):
    """Generate a valid GoogleUserInfo with non-empty email and google_id."""
    email = draw(valid_emails)
    google_id = draw(valid_google_ids)
    name = draw(optional_names)
    avatar_url = draw(optional_avatar_urls)

    return GoogleUserInfo(
        email=email,
        google_id=google_id,
        name=name,
        avatar_url=avatar_url,
    )


class TestNewOAuthUserCreationInvariants:
    """Property 1: New OAuth User Creation Invariants.

    For any valid GoogleUserInfo (with non-empty email and google_id) where the
    email does not exist in the database, calling find_or_create_oauth_user SHALL
    create a user record where: google_id matches the profile's google_id, email
    matches the profile's email, avatar_url matches the profile's picture URL,
    auth_provider equals "google", and password is NULL.

    **Validates: Requirements 1.2, 2.1, 2.2, 2.4, 4.5**
    """

    @given(google_info=valid_google_user_info())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_new_user_fields_match_google_profile(self, google_info, setup_db):
        """Created user's google_id, email, avatar_url, auth_provider, and password
        are set correctly for a brand new OAuth user.

        **Validates: Requirements 1.2, 2.1, 2.2, 2.4, 4.5**
        """
        db = TestSession()
        try:
            # Ensure clean state: no user with this email or google_id
            existing_email = db.query(User).filter(User.email == google_info.email).first()
            existing_gid = db.query(User).filter(User.google_id == google_info.google_id).first()
            if existing_email or existing_gid:
                # Clean up conflicting records from prior iterations
                if existing_email:
                    db.delete(existing_email)
                if existing_gid and existing_gid != existing_email:
                    db.delete(existing_gid)
                db.commit()

            user = find_or_create_oauth_user(google_info, db)

            # Property: google_id matches
            assert user.google_id == google_info.google_id, (
                f"Expected google_id '{google_info.google_id}', got '{user.google_id}'"
            )

            # Property: email matches
            assert user.email == google_info.email, (
                f"Expected email '{google_info.email}', got '{user.email}'"
            )

            # Property: avatar_url matches
            assert user.avatar_url == google_info.avatar_url, (
                f"Expected avatar_url '{google_info.avatar_url}', got '{user.avatar_url}'"
            )

            # Property: auth_provider is "google"
            assert user.auth_provider == "google", (
                f"Expected auth_provider 'google', got '{user.auth_provider}'"
            )

            # Property: password is NULL
            assert user.password is None, (
                f"Expected password to be None, got '{user.password}'"
            )

            # Cleanup for next iteration
            db.delete(user)
            db.commit()
        finally:
            db.close()

    @given(google_info=valid_google_user_info())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_new_user_is_persisted_in_database(self, google_info, setup_db):
        """Created user is actually persisted and queryable from the database.

        **Validates: Requirements 1.2, 2.1**
        """
        db = TestSession()
        try:
            # Ensure clean state
            existing_email = db.query(User).filter(User.email == google_info.email).first()
            existing_gid = db.query(User).filter(User.google_id == google_info.google_id).first()
            if existing_email or existing_gid:
                if existing_email:
                    db.delete(existing_email)
                if existing_gid and existing_gid != existing_email:
                    db.delete(existing_gid)
                db.commit()

            user = find_or_create_oauth_user(google_info, db)

            # Query the database directly to verify persistence
            persisted = db.query(User).filter(User.id == user.id).first()
            assert persisted is not None, "User was not persisted in the database"
            assert persisted.email == google_info.email
            assert persisted.google_id == google_info.google_id
            assert persisted.auth_provider == "google"
            assert persisted.password is None

            # Cleanup
            db.delete(user)
            db.commit()
        finally:
            db.close()

    @given(google_info=valid_google_user_info())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_new_user_gets_assigned_an_id(self, google_info, setup_db):
        """Created user receives a non-None primary key id.

        **Validates: Requirements 2.4, 4.5**
        """
        db = TestSession()
        try:
            # Ensure clean state
            existing_email = db.query(User).filter(User.email == google_info.email).first()
            existing_gid = db.query(User).filter(User.google_id == google_info.google_id).first()
            if existing_email or existing_gid:
                if existing_email:
                    db.delete(existing_email)
                if existing_gid and existing_gid != existing_email:
                    db.delete(existing_gid)
                db.commit()

            user = find_or_create_oauth_user(google_info, db)

            assert user.id is not None, "User should have a non-None id after creation"
            assert isinstance(user.id, int), (
                f"User id should be an integer, got {type(user.id)}"
            )

            # Cleanup
            db.delete(user)
            db.commit()
        finally:
            db.close()
