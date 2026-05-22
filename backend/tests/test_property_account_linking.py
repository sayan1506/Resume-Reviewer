"""Property-based test for account linking.

Feature: google-oauth, Property 2: Account Linking Preserves Identity and Updates OAuth Fields
**Validates: Requirements 3.1, 3.2, 3.3**

For any existing user with auth_provider="email" and a non-NULL password hash,
when find_or_create_oauth_user is called with a GoogleUserInfo whose email matches
that user, the operation SHALL:
- update google_id to the profile's value
- update avatar_url to the profile's value
- set auth_provider to "google"
- preserve the original password hash unchanged
- preserve the original user.id unchanged
"""

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import User
from schemas.auth_schema import GoogleUserInfo
from services.oauth_service import find_or_create_oauth_user


# In-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestSession = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create only the users table for each test."""
    User.__table__.create(bind=engine, checkfirst=True)
    yield
    User.__table__.drop(bind=engine, checkfirst=True)


# --- Strategies ---

# Generate valid email addresses
email_strategy = st.from_regex(
    r"[a-z][a-z0-9]{1,10}@[a-z]{3,8}\.[a-z]{2,4}", fullmatch=True
)

# Generate non-empty google_id strings (numeric like real Google sub IDs)
google_id_strategy = st.from_regex(r"[0-9]{5,30}", fullmatch=True)

# Generate non-empty password hashes (simulating bcrypt-like hashes)
password_hash_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=10,
    max_size=100,
).filter(lambda s: s.strip() != "")

# Generate optional avatar URLs
avatar_url_strategy = st.one_of(
    st.none(),
    st.from_regex(
        r"https://lh3\.googleusercontent\.com/[a-zA-Z0-9_-]{5,30}",
        fullmatch=True,
    ),
)


@st.composite
def existing_email_user_and_google_profile(draw):
    """Generate an existing email user and a matching Google profile for linking."""
    email = draw(email_strategy)
    original_password = draw(password_hash_strategy)
    google_id = draw(google_id_strategy)
    avatar_url = draw(avatar_url_strategy)

    return {
        "email": email,
        "original_password": original_password,
        "google_id": google_id,
        "avatar_url": avatar_url,
    }


class TestAccountLinkingPreservesIdentity:
    """Property 2: Account Linking Preserves Identity and Updates OAuth Fields.

    **Validates: Requirements 3.1, 3.2, 3.3**
    """

    @given(data=existing_email_user_and_google_profile())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_linking_preserves_user_id(self, data, setup_db):
        """Account linking preserves the original user.id (Requirement 3.2).

        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        db = TestSession()
        try:
            # Pre-create an email-only user
            existing_user = User(
                email=data["email"],
                password=data["original_password"],
                auth_provider="email",
                google_id=None,
                avatar_url=None,
            )
            db.add(existing_user)
            db.commit()
            db.refresh(existing_user)
            original_id = existing_user.id

            # Call find_or_create_oauth_user with matching email
            google_info = GoogleUserInfo(
                email=data["email"],
                google_id=data["google_id"],
                avatar_url=data["avatar_url"],
            )
            result = find_or_create_oauth_user(google_info, db)

            # Property: user.id is preserved
            assert result.id == original_id, (
                f"Expected user ID {original_id} to be preserved, got {result.id}"
            )
        finally:
            db.query(User).delete()
            db.commit()
            db.close()

    @given(data=existing_email_user_and_google_profile())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_linking_preserves_password_hash(self, data, setup_db):
        """Account linking preserves the original password hash unchanged (Requirement 3.1).

        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        db = TestSession()
        try:
            # Pre-create an email-only user
            existing_user = User(
                email=data["email"],
                password=data["original_password"],
                auth_provider="email",
                google_id=None,
                avatar_url=None,
            )
            db.add(existing_user)
            db.commit()
            db.refresh(existing_user)

            # Call find_or_create_oauth_user with matching email
            google_info = GoogleUserInfo(
                email=data["email"],
                google_id=data["google_id"],
                avatar_url=data["avatar_url"],
            )
            result = find_or_create_oauth_user(google_info, db)

            # Property: password hash is preserved unchanged
            assert result.password == data["original_password"], (
                f"Expected password hash to be preserved unchanged, "
                f"got '{result.password}' instead of '{data['original_password']}'"
            )
        finally:
            db.query(User).delete()
            db.commit()
            db.close()

    @given(data=existing_email_user_and_google_profile())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_linking_updates_google_id(self, data, setup_db):
        """Account linking updates google_id to the profile's value (Requirement 3.1).

        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        db = TestSession()
        try:
            # Pre-create an email-only user
            existing_user = User(
                email=data["email"],
                password=data["original_password"],
                auth_provider="email",
                google_id=None,
                avatar_url=None,
            )
            db.add(existing_user)
            db.commit()
            db.refresh(existing_user)

            # Call find_or_create_oauth_user with matching email
            google_info = GoogleUserInfo(
                email=data["email"],
                google_id=data["google_id"],
                avatar_url=data["avatar_url"],
            )
            result = find_or_create_oauth_user(google_info, db)

            # Property: google_id is updated to the profile's value
            assert result.google_id == data["google_id"], (
                f"Expected google_id to be '{data['google_id']}', got '{result.google_id}'"
            )
        finally:
            db.query(User).delete()
            db.commit()
            db.close()

    @given(data=existing_email_user_and_google_profile())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_linking_updates_avatar_url(self, data, setup_db):
        """Account linking updates avatar_url to the profile's value (Requirement 3.1).

        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        db = TestSession()
        try:
            # Pre-create an email-only user
            existing_user = User(
                email=data["email"],
                password=data["original_password"],
                auth_provider="email",
                google_id=None,
                avatar_url=None,
            )
            db.add(existing_user)
            db.commit()
            db.refresh(existing_user)

            # Call find_or_create_oauth_user with matching email
            google_info = GoogleUserInfo(
                email=data["email"],
                google_id=data["google_id"],
                avatar_url=data["avatar_url"],
            )
            result = find_or_create_oauth_user(google_info, db)

            # Property: avatar_url is updated to the profile's value
            assert result.avatar_url == data["avatar_url"], (
                f"Expected avatar_url to be '{data['avatar_url']}', got '{result.avatar_url}'"
            )
        finally:
            db.query(User).delete()
            db.commit()
            db.close()

    @given(data=existing_email_user_and_google_profile())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_linking_sets_auth_provider_to_google(self, data, setup_db):
        """Account linking sets auth_provider to "google" (Requirement 3.1).

        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        db = TestSession()
        try:
            # Pre-create an email-only user
            existing_user = User(
                email=data["email"],
                password=data["original_password"],
                auth_provider="email",
                google_id=None,
                avatar_url=None,
            )
            db.add(existing_user)
            db.commit()
            db.refresh(existing_user)

            # Call find_or_create_oauth_user with matching email
            google_info = GoogleUserInfo(
                email=data["email"],
                google_id=data["google_id"],
                avatar_url=data["avatar_url"],
            )
            result = find_or_create_oauth_user(google_info, db)

            # Property: auth_provider is set to "google"
            assert result.auth_provider == "google", (
                f"Expected auth_provider to be 'google', got '{result.auth_provider}'"
            )
        finally:
            db.query(User).delete()
            db.commit()
            db.close()

    @given(data=existing_email_user_and_google_profile())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_linking_does_not_create_new_user(self, data, setup_db):
        """Account linking reuses the existing user record, no new user is created.

        **Validates: Requirements 3.2, 3.3**
        """
        db = TestSession()
        try:
            # Pre-create an email-only user
            existing_user = User(
                email=data["email"],
                password=data["original_password"],
                auth_provider="email",
                google_id=None,
                avatar_url=None,
            )
            db.add(existing_user)
            db.commit()

            # Count users before linking
            count_before = db.query(User).count()

            # Call find_or_create_oauth_user with matching email
            google_info = GoogleUserInfo(
                email=data["email"],
                google_id=data["google_id"],
                avatar_url=data["avatar_url"],
            )
            find_or_create_oauth_user(google_info, db)

            # Count users after linking - should be the same
            count_after = db.query(User).count()
            assert count_after == count_before, (
                f"Expected no new user to be created. "
                f"Users before: {count_before}, after: {count_after}"
            )
        finally:
            db.query(User).delete()
            db.commit()
            db.close()
