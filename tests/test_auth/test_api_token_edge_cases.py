"""
Additional edge case tests for API Token authentication.

Tests network errors and unexpected exceptions that aren't covered
by the main test file.
"""

import pytest
from httpx import ConnectError, TimeoutException, RequestError

from src.auth.api_token import APITokenAuth
from src.exceptions import APIError


class TestAPITokenAuthNetworkErrors:
    """Test suite for network error handling."""

    @pytest.mark.asyncio
    async def test_authenticate_with_timeout_exception(self, httpx_mock) -> None:
        """Test authentication with httpx.TimeoutException (lines 145-149)."""
        auth = APITokenAuth(
            email="test@example.com",
            api_token="test_token",
            base_url="https://test.atlassian.net/wiki",
        )

        # Mock TimeoutException
        httpx_mock.add_exception(
            TimeoutException("Connection timed out"),
            url="https://test.atlassian.net/wiki/rest/api/user/current",
        )

        with pytest.raises(APIError) as exc_info:
            await auth.authenticate()

        assert "Authentication request timed out" in str(exc_info.value)
        assert "Could not connect to" in exc_info.value.details

    @pytest.mark.asyncio
    async def test_authenticate_with_request_error(self, httpx_mock) -> None:
        """Test authentication with httpx.RequestError (lines 150-154)."""
        auth = APITokenAuth(
            email="test@example.com",
            api_token="test_token",
            base_url="https://test.atlassian.net/wiki",
        )

        # Mock RequestError (generic network error)
        httpx_mock.add_exception(
            RequestError("Network error"),
            url="https://test.atlassian.net/wiki/rest/api/user/current",
        )

        with pytest.raises(APIError) as exc_info:
            await auth.authenticate()

        assert "Network error during authentication" in str(exc_info.value)
        assert "Failed to connect to" in exc_info.value.details

    @pytest.mark.asyncio
    async def test_authenticate_with_unexpected_exception(self, httpx_mock) -> None:
        """Test authentication with unexpected exception (lines 158-163)."""
        auth = APITokenAuth(
            email="test@example.com",
            api_token="test_token",
            base_url="https://test.atlassian.net/wiki",
        )

        # Mock unexpected exception (e.g., JSON decode error)
        httpx_mock.add_exception(
            ValueError("Unexpected error"),
            url="https://test.atlassian.net/wiki/rest/api/user/current",
        )

        with pytest.raises(APIError) as exc_info:
            await auth.authenticate()

        assert "Unexpected error during authentication" in str(exc_info.value)
        assert "ValueError" in exc_info.value.details
