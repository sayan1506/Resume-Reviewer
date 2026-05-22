"""Unit tests for the OAuth service exchange_google_code function."""

import os
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio

from services.oauth_service import exchange_google_code

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def set_oauth_env_vars(monkeypatch):
    """Set required OAuth environment variables for all tests."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/callback")


@pytest.mark.asyncio
async def test_exchange_google_code_success():
    """Test successful code exchange returns GoogleUserInfo."""
    token_response = httpx.Response(
        200,
        json={"access_token": "mock-access-token", "token_type": "Bearer"},
    )
    userinfo_response = httpx.Response(
        200,
        json={
            "email": "user@example.com",
            "sub": "google-id-123",
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
        },
    )

    with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = token_response
        mock_client.get.return_value = userinfo_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await exchange_google_code("valid-code")

    assert result.email == "user@example.com"
    assert result.google_id == "google-id-123"
    assert result.name == "Test User"
    assert result.avatar_url == "https://example.com/avatar.jpg"


@pytest.mark.asyncio
async def test_exchange_google_code_invalid_code_raises_401():
    """Test that an invalid/expired code raises HTTPException 401."""
    token_response = httpx.Response(
        400,
        json={"error": "invalid_grant"},
    )

    with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = token_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(Exception) as exc_info:
            await exchange_google_code("invalid-code")

    assert exc_info.value.status_code == 401
    assert "invalid or expired" in exc_info.value.detail


@pytest.mark.asyncio
async def test_exchange_google_code_token_timeout_raises_502():
    """Test that a timeout during token exchange raises HTTPException 502."""
    with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("Connection timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(Exception) as exc_info:
            await exchange_google_code("some-code")

    assert exc_info.value.status_code == 502
    assert "unavailable" in exc_info.value.detail


@pytest.mark.asyncio
async def test_exchange_google_code_token_non_2xx_raises_502():
    """Test that a non-2xx (non-400/401) token response raises HTTPException 502."""
    token_response = httpx.Response(500, json={"error": "server_error"})

    with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = token_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(Exception) as exc_info:
            await exchange_google_code("some-code")

    assert exc_info.value.status_code == 502
    assert "unavailable" in exc_info.value.detail


@pytest.mark.asyncio
async def test_exchange_google_code_userinfo_timeout_raises_502():
    """Test that a timeout during userinfo fetch raises HTTPException 502."""
    token_response = httpx.Response(
        200,
        json={"access_token": "mock-access-token"},
    )

    with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = token_response
        mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(Exception) as exc_info:
            await exchange_google_code("some-code")

    assert exc_info.value.status_code == 502
    assert "unavailable" in exc_info.value.detail


@pytest.mark.asyncio
async def test_exchange_google_code_userinfo_non_2xx_raises_502():
    """Test that a non-2xx userinfo response raises HTTPException 502."""
    token_response = httpx.Response(
        200,
        json={"access_token": "mock-access-token"},
    )
    userinfo_response = httpx.Response(403, json={"error": "forbidden"})

    with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = token_response
        mock_client.get.return_value = userinfo_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(Exception) as exc_info:
            await exchange_google_code("some-code")

    assert exc_info.value.status_code == 502
    assert "unavailable" in exc_info.value.detail


@pytest.mark.asyncio
async def test_exchange_google_code_reads_env_vars(monkeypatch):
    """Test that the function reads client_id, client_secret, redirect_uri from env."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "my-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "my-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost/callback")

    token_response = httpx.Response(
        200,
        json={"access_token": "token"},
    )
    userinfo_response = httpx.Response(
        200,
        json={
            "email": "test@example.com",
            "sub": "123",
            "name": "Test",
            "picture": None,
        },
    )

    with patch("services.oauth_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = token_response
        mock_client.get.return_value = userinfo_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await exchange_google_code("code")

        # Verify the POST was called with correct env var values
        call_kwargs = mock_client.post.call_args
        post_data = call_kwargs.kwargs.get("data") or call_kwargs[1].get("data")
        assert post_data["client_id"] == "my-client-id"
        assert post_data["client_secret"] == "my-secret"
        assert post_data["redirect_uri"] == "http://localhost/callback"
        assert post_data["grant_type"] == "authorization_code"
