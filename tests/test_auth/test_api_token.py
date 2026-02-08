"""
Tests for API Token authentication.

Tests the APITokenAuth implementation including:
- Basic Auth header generation
- Authentication validation
- Error handling
"""

import base64

import pytest
from httpx import Response

from src.auth.api_token import APITokenAuth
from src.exceptions import AuthenticationError, APIError, RateLimitError


class TestAPITokenAuth:
    """Test suite for API Token authentication."""

    def test_init_with_valid_credentials(self) -> None:
        """Test initialization with valid email and token."""
        auth = APITokenAuth(
            email="test@example.com",
            api_token="test_token_123",
            base_url="https://test.atlassian.net/wiki",
        )
        assert auth.email == "test@example.com"
        assert auth.api_token == "test_token_123"
        assert auth.base_url == "https://test.atlassian.net/wiki"
        assert not auth._authenticated

    def test_init_removes_trailing_slash(self) -> None:
        """Test that trailing slash is removed from base_url."""
        auth = APITokenAuth(
            email="test@example.com",
            api_token="test_token_123",
            base_url="https://test.atlassian.net/wiki/",
        )
        assert auth.base_url == "https://test.atlassian.net/wiki"

    def test_init_with_empty_email_raises_error(self) -> None:
        """Test that empty email raises AuthenticationError."""
        with pytest.raises(AuthenticationError) as exc_info:
            APITokenAuth(email="", api_token="test_token")
        assert "Email and API token are required" in str(exc_info.value)

    def test_init_with_empty_token_raises_error(self) -> None:
        """Test that empty token raises AuthenticationError."""
        with pytest.raises(AuthenticationError) as exc_info:
            APITokenAuth(email="test@example.com", api_token="")
        assert "Email and API token are required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_auth_headers_format(self) -> None:
        """Test that auth headers are correctly formatted."""
        auth = APITokenAuth(email="test@example.com", api_token="test_token_123")
        headers = await auth.get_auth_headers()

        # ヘッダーに必須キーが含まれていることを確認
        assert "Authorization" in headers
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

        # Basic認証ヘッダーの形式を確認
        assert headers["Authorization"].startswith("Basic ")

    @pytest.mark.asyncio
    async def test_get_auth_headers_encoding(self) -> None:
        """Test that credentials are correctly base64 encoded."""
        email = "test@example.com"
        token = "test_token_123"
        auth = APITokenAuth(email=email, api_token=token)

        headers = await auth.get_auth_headers()
        auth_value = headers["Authorization"]

        # "Basic " プレフィックスを除去
        encoded = auth_value.replace("Basic ", "")

        # Base64デコードして元の認証情報を確認
        decoded = base64.b64decode(encoded).decode("utf-8")
        assert decoded == f"{email}:{token}"

    @pytest.mark.asyncio
    async def test_get_auth_headers_uses_cache(self) -> None:
        """Test that get_auth_headers returns cached header without re-encoding."""
        email = "test@example.com"
        token = "test_token_123"
        auth = APITokenAuth(email=email, api_token=token)

        # Get headers twice
        headers1 = await auth.get_auth_headers()
        headers2 = await auth.get_auth_headers()

        # Both should return the same Authorization header (using cache)
        assert headers1["Authorization"] == headers2["Authorization"]

        # Verify the header matches the cached value
        assert headers1["Authorization"] == auth._cached_auth_header

        # Verify it's correctly formatted
        expected_credentials = f"{email}:{token}"
        expected_encoded = base64.b64encode(expected_credentials.encode("utf-8")).decode("utf-8")
        assert headers1["Authorization"] == f"Basic {expected_encoded}"

    @pytest.mark.asyncio
    async def test_authenticate_without_base_url(self) -> None:
        """Test authentication without base_url skips validation."""
        auth = APITokenAuth(email="test@example.com", api_token="test_token")

        # base_urlが設定されていない場合は検証をスキップしてTrue
        result = await auth.authenticate()
        assert result is True
        assert auth._authenticated is True

    @pytest.mark.asyncio
    async def test_is_authenticated_returns_status(self) -> None:
        """Test is_authenticated returns correct status."""
        auth = APITokenAuth(email="test@example.com", api_token="test_token")

        # 初期状態は未認証
        assert await auth.is_authenticated() is False

        # base_url未設定の認証後は認証済み
        await auth.authenticate()
        assert await auth.is_authenticated() is True


@pytest.mark.asyncio
async def test_authenticate_with_mock_success(httpx_mock) -> None:
    """Test successful authentication with mocked HTTP response."""
    auth = APITokenAuth(
        email="test@example.com", api_token="test_token", base_url="https://test.atlassian.net/wiki"
    )

    # モックレスポンスの設定（成功）
    httpx_mock.add_response(
        url="https://test.atlassian.net/wiki/rest/api/user/current",
        status_code=200,
        json={"type": "known", "username": "testuser"},
    )

    result = await auth.authenticate()
    assert result is True
    assert auth._authenticated is True


@pytest.mark.asyncio
async def test_authenticate_with_invalid_credentials(httpx_mock) -> None:
    """Test authentication with invalid credentials (401)."""
    auth = APITokenAuth(
        email="test@example.com",
        api_token="invalid_token",
        base_url="https://test.atlassian.net/wiki",
    )

    # モックレスポンスの設定（401エラー）
    httpx_mock.add_response(
        url="https://test.atlassian.net/wiki/rest/api/user/current",
        status_code=401,
        json={"message": "Unauthorized"},
    )

    with pytest.raises(AuthenticationError) as exc_info:
        await auth.authenticate()
    assert "Invalid credentials" in str(exc_info.value)
    assert auth._authenticated is False


@pytest.mark.asyncio
async def test_authenticate_with_forbidden(httpx_mock) -> None:
    """Test authentication with insufficient permissions (403)."""
    auth = APITokenAuth(
        email="test@example.com", api_token="test_token", base_url="https://test.atlassian.net/wiki"
    )

    # モックレスポンスの設定（403エラー）
    httpx_mock.add_response(
        url="https://test.atlassian.net/wiki/rest/api/user/current",
        status_code=403,
        json={"message": "Forbidden"},
    )

    with pytest.raises(AuthenticationError) as exc_info:
        await auth.authenticate()
    assert "Access forbidden" in str(exc_info.value)


@pytest.mark.asyncio
async def test_authenticate_with_rate_limit(httpx_mock) -> None:
    """Test authentication with rate limit error (429)."""
    auth = APITokenAuth(
        email="test@example.com", api_token="test_token", base_url="https://test.atlassian.net/wiki"
    )

    # モックレスポンスの設定（429エラー、Retry-Afterヘッダー付き）
    httpx_mock.add_response(
        url="https://test.atlassian.net/wiki/rest/api/user/current",
        status_code=429,
        headers={"Retry-After": "60"},
    )

    with pytest.raises(RateLimitError) as exc_info:
        await auth.authenticate()
    assert exc_info.value.retry_after == 60
    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_authenticate_with_server_error(httpx_mock) -> None:
    """Test authentication with server error (500)."""
    auth = APITokenAuth(
        email="test@example.com", api_token="test_token", base_url="https://test.atlassian.net/wiki"
    )

    # モックレスポンスの設定（500エラー）
    httpx_mock.add_response(
        url="https://test.atlassian.net/wiki/rest/api/user/current",
        status_code=500,
        text="Internal Server Error",
    )

    with pytest.raises(APIError) as exc_info:
        await auth.authenticate()
    assert exc_info.value.status_code == 500
