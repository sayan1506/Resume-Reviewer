"""Unit tests for Google code exchange (exchange_google_code).

Validates: Requirements 1.4, 1.5, 1.6
- 1.4: Invalid/expired code → HTTPException(401)
- 1.5: Timeout (>10s) → HTTPException(502)
- 1.6: Non-2xx response → HTTPException(502)
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from services.oauth_service import exchange_google_code

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def set_oauth_env_vars(monkeypatch):
    """Set required OAuth environment variables for all tests."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/callback")


def _mock_async_client(mock_client):
    """Helper to set up async context manager on a mock client."""
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)


class TestSuccessfulExchange:
    """Test successful Google code exchange returns GoogleUserInfo."""

    async def test_returns_google_user_info_with_all_fields(self):
        """Successful exchange returns GoogleUserInfo with email, google_id, name, avatar_url."""
        token_response = httpx.Response(
            200,
            json={"access_token": "mock-access-token", "token_type": "Bearer"},
        )
        userinfo_response = httpx.Response(
            200,
            json={
                "email": "user@example.com",
                "sub": "google-id-12345",
                "name": "Jane Doe",
                "picture": "https://lh3.googleusercontent.com/photo.jpg",
            },
        )

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = token_response
            mock_client.get.return_value = userinfo_response
            _mock_async_client(mock_client)
            mock_client_cls.return_value = mock_client

            result = await exchange_google_code("valid-auth-code")

        assert result.email == "user@example.com"
        assert result.google_id == "google-id-12345"
        assert result.name == "Jane Doe"
        assert result.avatar_url == "https://lh3.googleusercontent.com/photo.jpg"

    async def test_posts_code_to_google_token_endpoint(self):
        """Verifies the code is sent to Google's token endpoint with correct params."""
        token_response = httpx.Response(
            200,
            json={"access_token": "token-abc"},
        )
        userinfo_response = httpx.Response(
            200,
            json={
                "email": "test@example.com",
                "sub": "gid-999",
                "name": "Test",
                "picture": None,
            },
        )

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = token_response
            mock_client.get.return_value = userinfo_response
            _mock_async_client(mock_client)
            mock_client_cls.return_value = mock_client

            await exchange_google_code("my-auth-code")

            # Verify POST was called with the token URL and correct data
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "https://oauth2.googleapis.com/token"
            post_data = call_args[1]["data"] if "data" in call_args[1] else call_args.kwargs["data"]
            assert post_data["code"] == "my-auth-code"
            assert post_data["client_id"] == "test-client-id"
            assert post_data["client_secret"] == "test-client-secret"
            assert post_data["redirect_uri"] == "http://localhost:3000/callback"
            assert post_data["grant_type"] == "authorization_code"

    async def test_fetches_userinfo_with_access_token(self):
        """Verifies userinfo endpoint is called with the Bearer token from token exchange."""
        token_response = httpx.Response(
            200,
            json={"access_token": "my-access-token-xyz"},
        )
        userinfo_response = httpx.Response(
            200,
            json={
                "email": "user@test.com",
                "sub": "gid-001",
                "name": "User",
                "picture": None,
            },
        )

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = token_response
            mock_client.get.return_value = userinfo_response
            _mock_async_client(mock_client)
            mock_client_cls.return_value = mock_client

            await exchange_google_code("code-123")

            # Verify GET was called with userinfo URL and Bearer token
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = call_args[1]["headers"] if "headers" in call_args[1] else call_args.kwargs["headers"]
            assert headers["Authorization"] == "Bearer my-access-token-xyz"


class TestInvalidCode:
    """Test invalid/expired authorization code raises HTTPException(401).

    Validates: Requirement 1.4
    """

    async def test_google_returns_400_raises_401(self):
        """When Google token endpoint returns 400 (invalid_grant), raise 401."""
        token_response = httpx.Response(
            400,
            json={"error": "invalid_grant", "error_description": "Code has expired"},
        )

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = token_response
            _mock_async_client(mock_client)
            mock_client_cls.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                await exchange_google_code("expired-code")

        assert exc_info.value.status_code == 401
        assert "invalid or expired" in exc_info.value.detail

    async def test_google_returns_401_raises_401(self):
        """When Google token endpoint returns 401, raise 401."""
        token_response = httpx.Response(
            401,
            json={"error": "unauthorized_client"},
        )

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = token_response
            _mock_async_client(mock_client)
            mock_client_cls.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                await exchange_google_code("bad-code")

        assert exc_info.value.status_code == 401
        assert "invalid or expired" in exc_info.value.detail


class TestTimeout:
    """Test timeout scenarios raise HTTPException(502).

    Validates: Requirement 1.5
    """

    async def test_token_endpoint_timeout_raises_502(self):
        """When token endpoint times out (>10s), raise 502."""
        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException(
                "Timed out while connecting"
            )
            _mock_async_client(mock_client)
            mock_client_cls.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                await exchange_google_code("some-code")

        assert exc_info.value.status_code == 502
        assert "unavailable" in exc_info.value.detail

    async def test_userinfo_endpoint_timeout_raises_502(self):
        """When userinfo endpoint times out (>10s), raise 502."""
        token_response = httpx.Response(
            200,
            json={"access_token": "valid-token"},
        )

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = token_response
            mock_client.get.side_effect = httpx.TimeoutException(
                "Read timed out"
            )
            _mock_async_client(mock_client)
            mock_client_cls.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                await exchange_google_code("some-code")

        assert exc_info.value.status_code == 502
        assert "unavailable" in exc_info.value.detail


class TestNon2xxResponse:
    """Test non-2xx responses from Google raise HTTPException(502).

    Validates: Requirement 1.6
    """

    async def test_token_endpoint_500_raises_502(self):
        """When token endpoint returns 500 (server error), raise 502."""
        token_response = httpx.Response(
            500,
            json={"error": "internal_error"},
        )

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = token_response
            _mock_async_client(mock_client)
            mock_client_cls.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                await exchange_google_code("some-code")

        assert exc_info.value.status_code == 502
        assert "unavailable" in exc_info.value.detail

    async def test_token_endpoint_503_raises_502(self):
        """When token endpoint returns 503 (service unavailable), raise 502."""
        token_response = httpx.Response(
            503,
            json={"error": "service_unavailable"},
        )

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = token_response
            _mock_async_client(mock_client)
            mock_client_cls.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                await exchange_google_code("some-code")

        assert exc_info.value.status_code == 502
        assert "unavailable" in exc_info.value.detail

    async def test_userinfo_endpoint_500_raises_502(self):
        """When userinfo endpoint returns 500, raise 502."""
        token_response = httpx.Response(
            200,
            json={"access_token": "valid-token"},
        )
        userinfo_response = httpx.Response(
            500,
            json={"error": "internal_error"},
        )

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = token_response
            mock_client.get.return_value = userinfo_response
            _mock_async_client(mock_client)
            mock_client_cls.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                await exchange_google_code("some-code")

        assert exc_info.value.status_code == 502
        assert "unavailable" in exc_info.value.detail

    async def test_userinfo_endpoint_403_raises_502(self):
        """When userinfo endpoint returns 403 (forbidden), raise 502."""
        token_response = httpx.Response(
            200,
            json={"access_token": "valid-token"},
        )
        userinfo_response = httpx.Response(
            403,
            json={"error": "forbidden"},
        )

        with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = token_response
            mock_client.get.return_value = userinfo_response
            _mock_async_client(mock_client)
            mock_client_cls.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                await exchange_google_code("some-code")

        assert exc_info.value.status_code == 502
        assert "unavailable" in exc_info.value.detail
