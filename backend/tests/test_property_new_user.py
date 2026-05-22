"""Property-based tests for new OAuth user creation.

Feature: google-oauth, Property 1: New OAuth User Creation Invariants
**Validates: Requirements 1.2, 2.1, 2.2, 2.4, 4.5**

Uses Hypothesis to generate valid GoogleUserInfo with random emails/google_ids
and verifies all fields are set correctly on created user via find_or_create_oauth_user.
Also verifies that a JWT created from the returned user decodes to contain the
new user's id as user_id.
"""

import os
import pytest
import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from db.models import User
from schemas.auth_schema import GoogleUserInfo
from services.oauth_service import find_or_create_oauth_user
from utils.jwt_handler import create_access_token


# Set JWT_SECRET for testing if not already set
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-property-tests")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

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

# Valid email local parts: start with a letter, end with alphanumeric,
# no consecutive dots, no dot before @
email_local_parts = st.from_regex(r"[a-z][a-z0-9]{0,14}[a-z0-9]", fullmatch=True)

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

# Optional names
optional_names = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=80).filter(lambda s: s.strip() != ""),
)

# Optional avatar URLs
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


class TestNewOAuthUserCreationProperty:
    """Property 1: New OAuth User Creation Invariants.

    For any valid GoogleUserInfo (with non-empty email and google_id) where the
    email does not exist in the database, calling find_or_create_oauth_user SHALL
    create a user record where:
    - google_id matches the profile's google_id
    - email matches the profile's email
    - avatar_url matches the profile's avatar_url
    - auth_provider equals "google"
    - password is None
    - the returned JWT decodes to contain the new user's id as user_id

    **Validates: Requirements 1.2, 2.1, 2.2, 2.4, 4.5**
    """

    @given(google_info=valid_google_user_info())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_new_oauth_user_fields_set_correctly(self, google_info, setup_db):
        """Verify all fields are set correctly on a newly created OAuth user
        and the JWT contains the correct user_id.

        **Validates: Requirements 1.2, 2.1, 2.2, 2.4, 4.5**
        """
        db = TestSession()
        try:
            # Ensure no pre-existing user with this email or google_id
            db.query(User).filter(
                (User.email == google_info.email) | (User.google_id == google_info.google_id)
            ).delete(synchronize_session="fetch")
            db.commit()

            # Act: create the user via OAuth service
            user = find_or_create_oauth_user(google_info, db)

            # Assert: google_id matches
            assert user.google_id == google_info.google_id, (
                f"google_id mismatch: expected '{google_info.google_id}', got '{user.google_id}'"
            )

            # Assert: email matches
            assert user.email == google_info.email, (
                f"email mismatch: expected '{google_info.email}', got '{user.email}'"
            )

            # Assert: avatar_url matches
            assert user.avatar_url == google_info.avatar_url, (
                f"avatar_url mismatch: expected '{google_info.avatar_url}', got '{user.avatar_url}'"
            )

            # Assert: auth_provider is "google"
            assert user.auth_provider == "google", (
                f"auth_provider mismatch: expected 'google', got '{user.auth_provider}'"
            )

            # Assert: password is None
            assert user.password is None, (
                f"password should be None for OAuth user, got '{user.password}'"
            )

            # Assert: JWT contains the correct user_id (Requirement 2.4)
            token = create_access_token({"user_id": user.id})
            secret = os.getenv("JWT_SECRET")
            algorithm = os.getenv("JWT_ALGORITHM", "HS256")
            decoded = jwt.decode(token, secret, algorithms=[algorithm])
            assert decoded["user_id"] == user.id, (
                f"JWT user_id mismatch: expected {user.id}, got {decoded['user_id']}"
            )
        finally:
            # Cleanup using bulk delete to avoid lazy-loading relationships
            db.query(User).delete()
            db.commit()
            db.close()
