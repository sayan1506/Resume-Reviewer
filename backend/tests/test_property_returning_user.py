"""Property-based test for returning Google user authentication.

Feature: google-oauth, Property 3: Returning Google User Authentication
**Validates: Requirements 1.3**
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import User
from db.postgres import Base
from schemas.auth_schema import GoogleUserInfo
from services.oauth_service import find_or_create_oauth_user


# In-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestSession = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create only the users table (avoids JSONB incompatibility with SQLite)."""
    User.__table__.create(bind=engine, checkfirst=True)
    yield
    User.__table__.drop(bind=engine, checkfirst=True)


# --- Strategies ---

google_ids = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), blacklist_characters="\x00"),
    min_size=1,
    max_size=100,
).filter(lambda s: s.strip() != "")

emails = st.from_regex(
    r"[a-z][a-z0-9]{0,19}@[a-z]{3,10}\.[a-z]{2,4}",
    fullmatch=True,
)

avatar_urls = st.one_of(
    st.none(),
    st.from_regex(r"https://example\.com/avatar/[a-z0-9]{1,20}\.png", fullmatch=True),
)

passwords = st.one_of(
    st.none(),
    st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "P"), blacklist_characters="\x00"),
        min_size=8,
        max_size=72,
    ).filter(lambda s: s.strip() != ""),
)


class TestReturningGoogleUserAuthentication:
    """Property 3: Returning Google User Authentication.

    For any existing user with auth_provider="google" and a matching google_id,
    when find_or_create_oauth_user is called with a GoogleUserInfo whose google_id
    matches that user, the operation SHALL return the same user.id without modifying
    the user record's id, email, or password fields.

    **Validates: Requirements 1.3**
    """

    @given(
        google_id=google_ids,
        email=emails,
        avatar_url=avatar_urls,
        password=passwords,
    )
    @settings(max_examples=100)
    def test_returning_user_preserves_id_email_password(self, google_id, email, avatar_url, password):
        """Re-authenticating an existing Google user returns same user ID without modifications.

        **Validates: Requirements 1.3**
        """
        db = TestSession()
        try:
            # Create an existing Google user in the database
            existing_user = User(
                email=email,
                google_id=google_id,
                avatar_url=avatar_url,
                auth_provider="google",
                password=password,
            )
            db.add(existing_user)
            db.commit()
            db.refresh(existing_user)

            # Record original values
            original_id = existing_user.id
            original_email = existing_user.email
            original_password = existing_user.password

            # Call find_or_create_oauth_user with matching google_id
            google_info = GoogleUserInfo(
                email=email,
                google_id=google_id,
                name="Some Name",
                avatar_url="https://example.com/new-avatar.png",
            )
            returned_user = find_or_create_oauth_user(google_info, db)

            # The returned user should be the same user
            assert returned_user.id == original_id, (
                f"Expected user ID {original_id}, got {returned_user.id}"
            )

            # The email should not be modified
            assert returned_user.email == original_email, (
                f"Expected email '{original_email}', got '{returned_user.email}'"
            )

            # The password should not be modified
            assert returned_user.password == original_password, (
                f"Expected password to remain unchanged"
            )
        finally:
            db.query(User).delete()
            db.commit()
            db.close()

    @given(
        google_id=google_ids,
        email=emails,
    )
    @settings(max_examples=100)
    def test_no_duplicate_user_created_on_re_auth(self, google_id, email):
        """Re-authenticating does not create a duplicate user record.

        **Validates: Requirements 1.3**
        """
        db = TestSession()
        try:
            # Create an existing Google user
            existing_user = User(
                email=email,
                google_id=google_id,
                auth_provider="google",
                password=None,
            )
            db.add(existing_user)
            db.commit()
            db.refresh(existing_user)

            # Count users before re-auth
            user_count_before = db.query(User).count()

            # Re-authenticate with same google_id
            google_info = GoogleUserInfo(
                email=email,
                google_id=google_id,
                name="Updated Name",
                avatar_url="https://example.com/updated.png",
            )
            find_or_create_oauth_user(google_info, db)

            # Count users after re-auth - should be the same
            user_count_after = db.query(User).count()
            assert user_count_after == user_count_before, (
                f"Expected {user_count_before} users, but found {user_count_after} after re-auth"
            )
        finally:
            db.query(User).delete()
            db.commit()
            db.close()
