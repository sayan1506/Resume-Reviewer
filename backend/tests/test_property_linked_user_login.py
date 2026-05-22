"""Property-based test for linked user password login.

Feature: google-oauth, Property 4: Linked Users Retain Password Login
**Validates: Requirements 3.4**

For any user whose auth_provider is "google" and whose password is not NULL
(a linked account), calling login_user with the correct email and password
SHALL succeed and return a valid JWT containing that user's id as user_id.
"""

import os
import jwt
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import User
from utils.security import hash_password
from services.auth_service import login_user


# Set JWT_SECRET for testing
os.environ.setdefault("JWT_SECRET", "test-secret-for-property-tests")
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

# In-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
TestSession = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create and tear down the users table for each test."""
    User.__table__.create(bind=engine, checkfirst=True)
    yield
    User.__table__.drop(bind=engine, checkfirst=True)


# --- Strategies ---

# Generate valid email addresses
email_strategy = st.from_regex(
    r"[a-z][a-z0-9]{1,10}@[a-z]{3,8}\.[a-z]{2,4}", fullmatch=True
)

# Generate passwords (printable ASCII, reasonable length for hashing)
password_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "S"),
        blacklist_characters="\x00",
    ),
    min_size=6,
    max_size=50,
).filter(lambda s: s.strip() != "")

# Generate non-empty google_id strings (numeric like real Google sub IDs)
google_id_strategy = st.from_regex(r"[0-9]{5,30}", fullmatch=True)


@st.composite
def linked_user_data(draw):
    """Generate data for a linked user (auth_provider='google', password NOT NULL)."""
    email = draw(email_strategy)
    password = draw(password_strategy)
    google_id = draw(google_id_strategy)

    return {
        "email": email,
        "password": password,
        "google_id": google_id,
    }


class TestLinkedUserRetainsPasswordLogin:
    """Property 4: Linked Users Retain Password Login.

    **Validates: Requirements 3.4**
    """

    @given(data=linked_user_data())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_linked_user_can_login_with_password(self, data, setup_db):
        """A linked user (auth_provider='google', password not NULL) can login with password.

        **Validates: Requirements 3.4**
        """
        db = TestSession()
        try:
            # Create a linked user: auth_provider="google" with a hashed password
            hashed = hash_password(data["password"])
            linked_user = User(
                email=data["email"],
                password=hashed,
                auth_provider="google",
                google_id=data["google_id"],
                avatar_url=None,
            )
            db.add(linked_user)
            db.commit()
            db.refresh(linked_user)
            user_id = linked_user.id

            # Call login_user with correct email and password
            token = login_user(data["email"], data["password"], db)

            # Verify: token is a non-empty string
            assert token is not None and isinstance(token, str) and len(token) > 0, (
                "login_user should return a non-empty JWT token string"
            )

            # Verify: JWT decodes successfully and contains user_id
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            assert payload["user_id"] == user_id, (
                f"Expected JWT user_id={user_id}, got {payload.get('user_id')}"
            )
        finally:
            db.query(User).delete()
            db.commit()
            db.close()
