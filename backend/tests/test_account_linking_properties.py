"""Property-based test for account linking.

Feature: google-oauth, Property 2: Account Linking Preserves Identity and Updates OAuth Fields
Validates: Requirements 3.1, 3.2, 3.3
"""

import pytest
from hypothesis import given, settings
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

# Generate non-empty google_id strings
google_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=1,
    max_size=64,
)

# Generate non-empty password hashes (simulating bcrypt-like hashes)
password_hash_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P")),
    min_size=10,
    max_size=100,
).filter(lambda s: s.strip() != "")

# Generate optional avatar URLs
avatar_url_strategy = st.one_of(
    st.none(),
    st.from_regex(r"https://[a-z]{3,10}\.[a-z]{2,4}/[a-z0-9]{1,20}\.png", fullmatch=True),
)


class TestAccountLinkingPreservesIdentity:
    """Property 2: Account Linking Preserves Identity and Updates OAuth Fields.

    For any existing user with auth_provider="email" and a non-NULL password hash,
    when find_or_create_oauth_user is called with a GoogleUserInfo whose email
    matches that user, the operation SHALL:
    - update google_id to the profile's value
    - update avatar_url to the profile's value
    - set auth_provider to "google"
    - preserve the original password hash unchanged
    - preserve the original user.id unchanged

    **Validates: Requirements 3.1, 3.2, 3.3**
    """

    @given(
        email=email_strategy,
        original_password=password_hash_strategy,
        google_id=google_id_strategy,
        avatar_url=avatar_url_strategy,
    )
    @settings(max_examples=100)
    def test_linking_preserves_user_id_and_password(
        self, email, original_password, google_id, avatar_url
    ):
        """Account linking preserves user ID and password hash.

        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        db = TestSession()
        try:
            # Pre-create an email-only user
            existing_user = User(
                email=email,
                password=original_password,
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
                email=email,
                google_id=google_id,
                avatar_url=avatar_url,
            )
            result = find_or_create_oauth_user(google_info, db)

            # Property assertions:
            # 1. user.id is preserved (Requirement 3.2)
            assert result.id == original_id, (
                f"Expected user ID {original_id} to be preserved, got {result.id}"
            )

            # 2. password hash is preserved unchanged (Requirement 3.1)
            assert result.password == original_password, (
                f"Expected password hash to be preserved unchanged"
            )

            # 3. google_id is updated to the profile's value (Requirement 3.1)
            assert result.google_id == google_id, (
                f"Expected google_id to be updated to '{google_id}', got '{result.google_id}'"
            )

            # 4. avatar_url is updated to the profile's value (Requirement 3.1)
            assert result.avatar_url == avatar_url, (
                f"Expected avatar_url to be updated to '{avatar_url}', got '{result.avatar_url}'"
            )

            # 5. auth_provider is set to "google" (Requirement 3.1)
            assert result.auth_provider == "google", (
                f"Expected auth_provider to be 'google', got '{result.auth_provider}'"
            )
        finally:
            # Cleanup for next hypothesis iteration
            db.query(User).delete()
            db.commit()
            db.close()

    @given(
        email=email_strategy,
        original_password=password_hash_strategy,
        google_id=google_id_strategy,
        avatar_url=avatar_url_strategy,
    )
    @settings(max_examples=100)
    def test_linking_does_not_create_new_user(
        self, email, original_password, google_id, avatar_url
    ):
        """Account linking reuses the existing user record, no new user is created.

        **Validates: Requirements 3.2, 3.3**
        """
        db = TestSession()
        try:
            # Pre-create an email-only user
            existing_user = User(
                email=email,
                password=original_password,
                auth_provider="email",
                google_id=None,
                avatar_url=None,
            )
            db.add(existing_user)
            db.commit()
            db.refresh(existing_user)

            # Count users before linking
            count_before = db.query(User).count()

            # Call find_or_create_oauth_user with matching email
            google_info = GoogleUserInfo(
                email=email,
                google_id=google_id,
                avatar_url=avatar_url,
            )
            find_or_create_oauth_user(google_info, db)

            # Count users after linking - should be the same
            count_after = db.query(User).count()
            assert count_after == count_before, (
                f"Expected no new user to be created. Users before: {count_before}, after: {count_after}"
            )
        finally:
            # Cleanup for next hypothesis iteration
            db.query(User).delete()
            db.commit()
            db.close()
