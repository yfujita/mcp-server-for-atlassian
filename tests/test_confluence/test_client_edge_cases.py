"""
Additional edge case tests for Confluence client.

Tests error handling paths and edge cases not covered by main client tests.
"""

import pytest
from datetime import datetime
from httpx import ConnectError, ConnectTimeout, TimeoutException, RequestError

from src.auth.api_token import APITokenAuth
from src.confluence.client import ConfluenceClient
from src.exceptions import APIError, PageNotFoundError, ConversionError


class TestConfluenceClientErrorHandling:
    """Test suite for error handling edge cases."""

    @pytest.mark.asyncio
    async def test_get_page_content_markdown_conversion_failure(self, httpx_mock, monkeypatch) -> None:
        """Test fallback to HTML when Markdown conversion fails (lines 237-241)."""
        # Use auth without base_url to skip authentication check
        auth = APITokenAuth(
            email="test@example.com",
            api_token="test_token",
        )

        # Mock page content with malformed HTML that might cause conversion issues
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/123?expand=body.storage%2Cversion%2Cspace%2Chistory.lastUpdated",
            status_code=200,
            json={
                "id": "123",
                "title": "Test Page",
                "body": {"storage": {"value": "<h1>Test</h1>"}},
                "space": {"key": "DEV"},
                "version": {"number": 1},
                "_links": {"webui": "/pages/123"},
            },
        )

        # Patch html_to_markdown at import location in client module
        def failing_convert(html: str) -> str:
            raise RuntimeError("Conversion failed")

        monkeypatch.setattr("src.confluence.client.html_to_markdown", failing_convert)

        async with ConfluenceClient(
            base_url="https://test.atlassian.net/wiki",
            auth_strategy=auth,
        ) as client:
            # Should fall back to HTML format
            page = await client.get_page_content("123", as_markdown=True)

            # Should have fallen back to HTML
            assert page.content_format == "html"
            assert page.content == "<h1>Test</h1>"

    @pytest.mark.asyncio
    async def test_get_page_content_date_parse_failure(self, httpx_mock) -> None:
        """Test handling of invalid date format (lines 266-267)."""
        # Use auth without base_url to skip authentication check
        auth = APITokenAuth(
            email="test@example.com",
            api_token="test_token",
        )

        # Mock page content with invalid date format
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/123?expand=body.storage%2Cversion%2Cspace%2Chistory.lastUpdated",
            status_code=200,
            json={
                "id": "123",
                "title": "Test Page",
                "body": {"storage": {"value": "content"}},
                "space": {"key": "DEV"},
                "version": {"number": 1},
                "history": {
                    "lastUpdated": {
                        "when": "invalid-date-format",
                        "by": {"displayName": "Test User"},
                    }
                },
                "_links": {"webui": "/pages/123"},
            },
        )

        async with ConfluenceClient(
            base_url="https://test.atlassian.net/wiki",
            auth_strategy=auth,
        ) as client:
            page = await client.get_page_content("123", as_markdown=False)

            # Date parsing should fail gracefully, last_modified should be None
            assert page.last_modified is None
            assert page.author == "Test User"

    @pytest.mark.asyncio
    async def test_get_child_pages_parent_not_found_404(self, httpx_mock) -> None:
        """Test 404 error converted to PageNotFoundError for get_child_pages (line 328)."""
        # Use auth without base_url to skip authentication check
        auth = APITokenAuth(
            email="test@example.com",
            api_token="test_token",
        )

        # Mock 404 response for non-existent parent
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/999/child/page?limit=50&start=0",
            status_code=404,
            json={"message": "Page not found"},
        )

        async with ConfluenceClient(
            base_url="https://test.atlassian.net/wiki",
            auth_strategy=auth,
        ) as client:
            with pytest.raises(PageNotFoundError) as exc_info:
                await client.get_child_pages("999")

            assert "999" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_make_request_client_not_initialized(self) -> None:
        """Test error when making request without initialized client (line 391)."""
        auth = APITokenAuth(
            email="test@example.com",
            api_token="test_token",
            base_url="https://test.atlassian.net/wiki",
        )

        client = ConfluenceClient(
            base_url="https://test.atlassian.net/wiki",
            auth_strategy=auth,
        )

        # Try to make request without entering context manager
        with pytest.raises(APIError) as exc_info:
            await client._make_request("GET", "/content/search")

        assert "Client not initialized" in str(exc_info.value)
        assert "async with" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_make_request_connect_timeout_retry(self, httpx_mock) -> None:
        """Test retry logic for ConnectTimeout (lines 491-505)."""
        # Use auth without base_url to skip authentication check
        auth = APITokenAuth(
            email="test@example.com",
            api_token="test_token",
        )

        # Mock ConnectTimeout for first 2 attempts, then success
        httpx_mock.add_exception(
            ConnectTimeout("Connection timeout"),
            url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
        )
        httpx_mock.add_exception(
            ConnectTimeout("Connection timeout"),
            url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
        )
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
            status_code=200,
            json={"results": [], "start": 0, "limit": 25, "size": 0},
        )

        async with ConfluenceClient(
            base_url="https://test.atlassian.net/wiki",
            auth_strategy=auth,
            max_retries=3,
        ) as client:
            # Should succeed after retries
            result = await client.search_pages("type=page")
            assert len(result.results) == 0

    @pytest.mark.asyncio
    async def test_make_request_connect_timeout_max_retries(self, httpx_mock) -> None:
        """Test ConnectTimeout exceeds max retries."""
        # Use auth without base_url to skip authentication check
        auth = APITokenAuth(
            email="test@example.com",
            api_token="test_token",
        )

        # Mock ConnectTimeout for all attempts
        for _ in range(4):  # max_retries + 1
            httpx_mock.add_exception(
                ConnectTimeout("Connection timeout"),
                url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
            )

        async with ConfluenceClient(
            base_url="https://test.atlassian.net/wiki",
            auth_strategy=auth,
            max_retries=3,
        ) as client:
            with pytest.raises(APIError) as exc_info:
                await client.search_pages("type=page")

            assert "Connection timeout" in str(exc_info.value)
            assert "after 3 retries" in exc_info.value.details

    @pytest.mark.asyncio
    async def test_make_request_connect_error_retry(self, httpx_mock) -> None:
        """Test retry logic for ConnectError (lines 519-533)."""
        # Use auth without base_url to skip authentication check
        auth = APITokenAuth(
            email="test@example.com",
            api_token="test_token",
        )

        # Mock ConnectError for first attempt, then success
        httpx_mock.add_exception(
            ConnectError("Network unreachable"),
            url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
        )
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
            status_code=200,
            json={"results": [], "start": 0, "limit": 25, "size": 0},
        )

        async with ConfluenceClient(
            base_url="https://test.atlassian.net/wiki",
            auth_strategy=auth,
            max_retries=3,
        ) as client:
            # Should succeed after retry
            result = await client.search_pages("type=page")
            assert len(result.results) == 0

    @pytest.mark.asyncio
    async def test_make_request_unexpected_exception(self, httpx_mock) -> None:
        """Test handling of unexpected exceptions (lines 548-550)."""
        # Use auth without base_url to skip authentication check
        auth = APITokenAuth(
            email="test@example.com",
            api_token="test_token",
        )

        # Mock unexpected exception
        httpx_mock.add_exception(
            ValueError("Unexpected error"),
            url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
        )

        async with ConfluenceClient(
            base_url="https://test.atlassian.net/wiki",
            auth_strategy=auth,
        ) as client:
            with pytest.raises(APIError) as exc_info:
                await client.search_pages("type=page")

            assert "Unexpected error" in str(exc_info.value)
            assert "ValueError" in exc_info.value.details
