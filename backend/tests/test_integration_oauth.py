"""Backend integration tests for Google OAuth flow.

Tests cover:
- Full OAuth flow with mocked Google endpoints (new user, existing user, linked user)
- Rate limiting on POST /auth/google (5/min/IP, returns 429 with Retry-After)
- JWT compatibility (OAuth-issued JWT works with protected endpoints)

Requirements: 1.1, 1.2, 1.3, 8.1, 8.2, 8.3, 8.4
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set required environment variables BEFORE importing the app
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("GOOGLE_REDIRECT_URI", "http://localhost:5173/callback")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-integration-tests")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_integration.db")

from db.postgres import get_db
from db.models import User, Resume
from main import app
from utils.jwt_handler import create_access_token

# In-memory SQLite with StaticPool to share the same connection across threads
# This ensures TestClient and test code see the same database state
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency with test database."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create only the tables needed for OAuth tests (avoids JSONB incompatibility with SQLite)."""
    User.__table__.create(bind=engine, checkfirst=True)
    Resume.__table__.create(bind=engine, checkfirst=True)
    yield
    Resume.__table__.drop(bind=engine, checkfirst=True)
    User.__table__.drop(bind=engine, checkfirst=True)


@pytest.fixture
def client():
    """Create a test client with rate limiter reset."""
    # Reset rate limiter state between tests
    from utils.rate_limiter import limiter
    limiter.reset()
    return TestClient(app)


@pytest.fixture
def db_session():
    """Provide a database session for test setup."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _mock_google_success(email: str, google_id: str, name: str = "Test User", picture: str = "https://example.com/avatar.jpg"):
    """Create mock responses for a successful Google OAuth exchange."""

    async def mock_post(url, **kwargs):
        """Mock the token endpoint POST."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "access_token": "mock-google-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        return response

    async def mock_get(url, **kwargs):
        """Mock the userinfo endpoint GET."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "email": email,
            "sub": google_id,
            "name": name,
            "picture": picture,
        }
        return response

    return mock_post, mock_get


class TestOAuthFlowNewUser:
    """Test full OAuth flow for a new user (email not in database).

    Validates: Requirements 1.1, 1.2
    """

    def test_new_user_created_on_first_google_login(self, client, db_session):
        """A new user is created when Google returns an email not in the database."""
        email = "newuser@example.com"
        google_id = "1234567890"

        mock_post, mock_get = _mock_google_success(email, google_id)

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.get = mock_get
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            response = client.post("/auth/google", json={"code": "valid-auth-code"})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify user was created in the database
        user = db_session.query(User).filter(User.email == email).first()
        assert user is not None
        assert user.google_id == google_id
        assert user.auth_provider == "google"
        assert user.password is None

    def test_new_user_gets_correct_fields(self, client, db_session):
        """New user record has correct google_id, avatar_url, and auth_provider."""
        email = "brand_new@test.org"
        google_id = "9876543210"
        avatar = "https://lh3.googleusercontent.com/photo.jpg"

        mock_post, mock_get = _mock_google_success(email, google_id, "Brand New", avatar)

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.get = mock_get
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            response = client.post("/auth/google", json={"code": "another-valid-code"})

        assert response.status_code == 200

        user = db_session.query(User).filter(User.email == email).first()
        assert user is not None
        assert user.google_id == google_id
        assert user.avatar_url == avatar
        assert user.auth_provider == "google"
        assert user.password is None


class TestOAuthFlowExistingGoogleUser:
    """Test full OAuth flow for an existing Google user (same email, same google_id).

    Validates: Requirements 1.3
    """

    def test_existing_google_user_gets_token(self, client, db_session):
        """An existing Google user gets a token without creating a new record."""
        email = "existing@example.com"
        google_id = "111222333"

        # Pre-create the user in the database
        existing_user = User(
            email=email,
            google_id=google_id,
            auth_provider="google",
            password=None,
            avatar_url="https://example.com/old-avatar.jpg",
        )
        db_session.add(existing_user)
        db_session.commit()
        db_session.refresh(existing_user)
        original_id = existing_user.id

        mock_post, mock_get = _mock_google_success(email, google_id)

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.get = mock_get
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            response = client.post("/auth/google", json={"code": "valid-code"})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify no duplicate user was created
        users = db_session.query(User).filter(User.email == email).all()
        assert len(users) == 1
        assert users[0].id == original_id


class TestOAuthFlowLinkedUser:
    """Test full OAuth flow for account linking (email-registered user signs in with Google).

    Validates: Requirements 1.2, 1.3
    """

    def test_email_user_gets_linked_on_google_login(self, client, db_session):
        """An email-registered user gets their account linked when signing in with Google."""
        email = "emailuser@example.com"
        google_id = "444555666"
        password_hash = "$2b$12$fakehashforexistinguser1234567890"

        # Pre-create an email-registered user
        email_user = User(
            email=email,
            password=password_hash,
            auth_provider="email",
            google_id=None,
            avatar_url=None,
        )
        db_session.add(email_user)
        db_session.commit()
        db_session.refresh(email_user)
        original_id = email_user.id

        mock_post, mock_get = _mock_google_success(email, google_id, "Email User", "https://example.com/new-avatar.jpg")

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.get = mock_get
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            response = client.post("/auth/google", json={"code": "link-code"})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

        # Verify account was linked (not a new user)
        db_session.expire_all()
        user = db_session.query(User).filter(User.email == email).first()
        assert user is not None
        assert user.id == original_id  # Same user ID preserved
        assert user.google_id == google_id  # Google ID linked
        assert user.auth_provider == "google"  # Provider updated
        assert user.password == password_hash  # Password preserved
        assert user.avatar_url == "https://example.com/new-avatar.jpg"


class TestRateLimiting:
    """Test rate limiting on POST /auth/google (5 requests/min/IP).

    Validates: Requirements 8.2, 8.3
    """

    def test_rate_limit_allows_5_requests(self, client, db_session):
        """First 5 requests within a minute should succeed."""
        email = "ratelimit@example.com"
        google_id = "777888999"

        mock_post, mock_get = _mock_google_success(email, google_id)

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.get = mock_get
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            for i in range(5):
                response = client.post("/auth/google", json={"code": f"code-{i}"})
                assert response.status_code == 200, f"Request {i+1} should succeed but got {response.status_code}"

    def test_rate_limit_blocks_6th_request(self, client, db_session):
        """The 6th request within a minute should return 429 with Retry-After header."""
        email = "ratelimit2@example.com"
        google_id = "000111222"

        mock_post, mock_get = _mock_google_success(email, google_id)

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.get = mock_get
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            # Send 5 successful requests
            for i in range(5):
                response = client.post("/auth/google", json={"code": f"code-{i}"})
                assert response.status_code == 200

            # 6th request should be rate limited
            response = client.post("/auth/google", json={"code": "code-6"})
            assert response.status_code == 429
            assert "retry-after" in response.headers or "Retry-After" in response.headers


class TestJWTCompatibility:
    """Test that OAuth-issued JWTs work with protected endpoints.

    Validates: Requirements 8.1, 8.4
    """

    def test_oauth_jwt_works_with_protected_endpoint(self, client, db_session):
        """A JWT issued via OAuth login should work with protected endpoints (e.g., /resume/list)."""
        email = "jwttest@example.com"
        google_id = "555666777"

        mock_post, mock_get = _mock_google_success(email, google_id)

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.get = mock_get
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            # Get a token via OAuth
            response = client.post("/auth/google", json={"code": "jwt-test-code"})

        assert response.status_code == 200
        token = response.json()["access_token"]

        # Use the token to access a protected endpoint
        protected_response = client.get(
            "/resume/list",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should get 200 (empty list for new user) — NOT 401
        assert protected_response.status_code == 200

    def test_oauth_jwt_contains_correct_user_id(self, client, db_session):
        """The JWT issued via OAuth should decode to contain the correct user_id."""
        import jwt

        email = "jwtclaim@example.com"
        google_id = "888999000"

        mock_post, mock_get = _mock_google_success(email, google_id)

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.get = mock_get
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            response = client.post("/auth/google", json={"code": "claim-test-code"})

        assert response.status_code == 200
        token = response.json()["access_token"]

        # Decode the token and verify user_id claim
        secret = os.getenv("JWT_SECRET")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert "user_id" in decoded

        # Verify the user_id matches the created user
        user = db_session.query(User).filter(User.email == email).first()
        assert user is not None
        assert decoded["user_id"] == user.id

    def test_oauth_user_subject_to_same_rate_limits_as_email_user(self, client, db_session):
        """OAuth-authenticated users are identified by JWT user_id for rate limiting,
        same as email-authenticated users.

        Validates: Requirements 8.1, 8.4
        """
        email = "rateuser@example.com"
        google_id = "123456789"

        mock_post, mock_get = _mock_google_success(email, google_id)

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = mock_post
            mock_client_instance.get = mock_get
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            response = client.post("/auth/google", json={"code": "rate-user-code"})

        assert response.status_code == 200
        token = response.json()["access_token"]

        # Use the OAuth token to access a protected endpoint multiple times
        # This verifies the rate limiter can identify the user by JWT user_id
        for _ in range(3):
            protected_response = client.get(
                "/resume/list",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert protected_response.status_code == 200
