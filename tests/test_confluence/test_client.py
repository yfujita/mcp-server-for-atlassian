"""
Tests for Confluence API client.

Tests ConfluenceClient using mocked HTTP responses.
Uses pytest-httpx for mocking httpx requests.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
from pytest_httpx import HTTPXMock

from src.confluence.client import ConfluenceClient
from src.confluence.models import PageSearchResult, PageContent, ChildPage, PaginatedResponse
from src.auth.api_token import APITokenAuth
from src.exceptions import APIError, RateLimitError, PageNotFoundError, AuthenticationError


@pytest.fixture
def auth_strategy() -> APITokenAuth:
    """Create a mock authentication strategy."""
    return APITokenAuth(
        email="test@example.com",
        api_token="test-token",
    )


@pytest.fixture
def base_url() -> str:
    """Return test base URL."""
    return "https://test.atlassian.net/wiki"


@pytest.fixture
async def client(auth_strategy: APITokenAuth, base_url: str) -> ConfluenceClient:
    """Create a ConfluenceClient instance."""
    client = ConfluenceClient(base_url=base_url, auth_strategy=auth_strategy)
    async with client:
        yield client


class TestConfluenceClientInitialization:
    """Tests for ConfluenceClient initialization."""

    @pytest.mark.asyncio
    async def test_client_context_manager(
        self, auth_strategy: APITokenAuth, base_url: str
    ) -> None:
        """Test client initialization with context manager."""
        async with ConfluenceClient(base_url, auth_strategy) as client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_client_base_url_normalization(self, auth_strategy: APITokenAuth) -> None:
        """Test that trailing slash is removed from base URL."""
        async with ConfluenceClient("https://test.atlassian.net/wiki/", auth_strategy) as client:
            assert client.base_url == "https://test.atlassian.net/wiki"

    @pytest.mark.asyncio
    async def test_client_close(self, auth_strategy: APITokenAuth, base_url: str) -> None:
        """Test client cleanup on exit."""
        client = ConfluenceClient(base_url, auth_strategy)
        async with client:
            assert client._client is not None

        # After exiting context, client should be closed
        assert client._client is None


class TestSearchPages:
    """Tests for search_pages method."""

    @pytest.mark.asyncio
    async def test_search_pages_success(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test successful page search."""
        # Mock API response
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
            json={
                "results": [
                    {
                        "id": "123456",
                        "title": "Test Page",
                        "space": {"key": "DEV"},
                        "_links": {"webui": "/spaces/DEV/pages/123456"},
                        "excerpt": "Test excerpt",
                    }
                ],
                "start": 0,
                "limit": 25,
                "size": 1,
                "totalSize": 1,
            },
        )

        # Execute search
        response = await client.search_pages("type=page")

        # Verify response
        assert isinstance(response, PaginatedResponse)
        assert len(response.results) == 1
        assert response.results[0].id == "123456"
        assert response.results[0].title == "Test Page"
        assert response.results[0].space_key == "DEV"
        assert response.start == 0
        assert response.limit == 25
        assert response.size == 1
        assert response.total_size == 1

    @pytest.mark.asyncio
    async def test_search_pages_with_limit(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test search with custom limit."""
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=50&start=0",
            json={
                "results": [],
                "start": 0,
                "limit": 50,
                "size": 0,
            },
        )

        response = await client.search_pages("type=page", limit=50)
        assert response.limit == 50

    @pytest.mark.asyncio
    async def test_search_pages_limit_clamping(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test that limit is clamped to valid range (1-100)."""
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=100&start=0",
            json={
                "results": [],
                "start": 0,
                "limit": 100,
                "size": 0,
            },
        )

        # Test limit too high (should be clamped to 100)
        response = await client.search_pages("type=page", limit=200)
        # Verify the request was made with limit=100
        assert response.limit == 100

    @pytest.mark.asyncio
    async def test_search_pages_empty_results(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test search with no results."""
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
            json={
                "results": [],
                "start": 0,
                "limit": 25,
                "size": 0,
                "totalSize": 0,
            },
        )

        response = await client.search_pages("type=page")
        assert len(response.results) == 0
        assert response.size == 0


class TestGetPageContent:
    """Tests for get_page_content method."""

    @pytest.mark.asyncio
    async def test_get_page_content_success(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test successful page content retrieval."""
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/123456?expand=body.storage%2Cversion%2Cspace%2Chistory.lastUpdated",
            json={
                "id": "123456",
                "title": "Test Page",
                "body": {
                    "storage": {
                        "value": "<h1>Title</h1><p>Content</p>",
                    }
                },
                "space": {"key": "DEV"},
                "version": {"number": 5},
                "_links": {"webui": "/spaces/DEV/pages/123456"},
                "history": {
                    "lastUpdated": {
                        "when": "2024-01-15T10:30:00.000Z",
                        "by": {"displayName": "John Doe"},
                    }
                },
            },
        )

        page = await client.get_page_content("123456")

        assert page.id == "123456"
        assert page.title == "Test Page"
        assert page.space_key == "DEV"
        assert page.version == 5
        assert page.author == "John Doe"
        # Content should be converted to markdown
        assert page.content_format == "markdown"
        assert "# Title" in page.content

    @pytest.mark.asyncio
    async def test_get_page_content_as_html(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test getting page content in HTML format."""
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/123456?expand=body.storage%2Cversion%2Cspace%2Chistory.lastUpdated",
            json={
                "id": "123456",
                "title": "Test Page",
                "body": {
                    "storage": {
                        "value": "<h1>Title</h1><p>Content</p>",
                    }
                },
                "space": {"key": "DEV"},
                "version": {"number": 1},
                "_links": {"webui": "/spaces/DEV/pages/123456"},
            },
        )

        page = await client.get_page_content("123456", as_markdown=False)

        assert page.content_format == "html"
        assert page.content == "<h1>Title</h1><p>Content</p>"

    @pytest.mark.asyncio
    async def test_get_page_content_not_found(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test getting non-existent page."""
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/999999?expand=body.storage%2Cversion%2Cspace%2Chistory.lastUpdated",
            status_code=404,
        )

        with pytest.raises(PageNotFoundError) as exc_info:
            await client.get_page_content("999999")

        assert exc_info.value.page_id == "999999"


class TestGetChildPages:
    """Tests for get_child_pages method."""

    @pytest.mark.asyncio
    async def test_get_child_pages_success(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test successful child pages retrieval."""
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/123456/child/page?limit=50&start=0",
            json={
                "results": [
                    {
                        "id": "111",
                        "title": "Child 1",
                        "_links": {"webui": "/spaces/DEV/pages/111"},
                    },
                    {
                        "id": "222",
                        "title": "Child 2",
                        "_links": {"webui": "/spaces/DEV/pages/222"},
                    },
                ],
                "start": 0,
                "limit": 50,
                "size": 2,
                "totalSize": 2,
            },
        )

        response = await client.get_child_pages("123456")

        assert len(response.results) == 2
        assert response.results[0].id == "111"
        assert response.results[0].title == "Child 1"
        assert response.results[0].position == 0
        assert response.results[1].id == "222"
        assert response.results[1].title == "Child 2"
        assert response.results[1].position == 1

    @pytest.mark.asyncio
    async def test_get_child_pages_parent_not_found(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test getting child pages of non-existent parent."""
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/999999/child/page?limit=50&start=0",
            status_code=404,
        )

        with pytest.raises(PageNotFoundError) as exc_info:
            await client.get_child_pages("999999")

        assert exc_info.value.page_id == "999999"

    @pytest.mark.asyncio
    async def test_get_child_pages_empty(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test getting child pages when there are none."""
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/123456/child/page?limit=50&start=0",
            json={
                "results": [],
                "start": 0,
                "limit": 50,
                "size": 0,
                "totalSize": 0,
            },
        )

        response = await client.get_child_pages("123456")
        assert len(response.results) == 0


class TestErrorHandling:
    """Tests for error handling in ConfluenceClient."""

    @pytest.mark.asyncio
    async def test_authentication_error_401(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test handling of 401 authentication error."""
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
            status_code=401,
        )

        with pytest.raises(AuthenticationError):
            await client.search_pages("type=page")

    @pytest.mark.asyncio
    async def test_authentication_error_403(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test handling of 403 forbidden error."""
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
            status_code=403,
        )

        with pytest.raises(AuthenticationError):
            await client.search_pages("type=page")

    @pytest.mark.asyncio
    async def test_rate_limit_error_without_retry(
        self, auth_strategy: APITokenAuth, base_url: str, httpx_mock: HTTPXMock
    ) -> None:
        """Test handling of 429 rate limit error (max retries=0)."""
        # Create client with no retries
        async with ConfluenceClient(base_url, auth_strategy, max_retries=0) as client:
            httpx_mock.add_response(
                url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
                status_code=429,
                headers={"Retry-After": "60"},
            )

            with pytest.raises(RateLimitError) as exc_info:
                await client.search_pages("type=page")

            assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_server_error_500(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test handling of 500 server error."""
        httpx_mock.add_response(
            url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
            status_code=500,
            text="Internal Server Error",
        )

        with pytest.raises(APIError) as exc_info:
            await client.search_pages("type=page")

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_timeout_error(
        self, auth_strategy: APITokenAuth, base_url: str, httpx_mock: HTTPXMock
    ) -> None:
        """Test handling of timeout error."""
        async with ConfluenceClient(base_url, auth_strategy, timeout=0.001) as client:
            # Mock a slow response (will timeout)
            httpx_mock.add_exception(
                httpx.TimeoutException("Request timed out"),
            )

            with pytest.raises(APIError) as exc_info:
                await client.search_pages("type=page")

            assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_network_error(
        self, client: ConfluenceClient, httpx_mock: HTTPXMock
    ) -> None:
        """Test handling of network error."""
        httpx_mock.add_exception(
            httpx.RequestError("Connection failed"),
        )

        with pytest.raises(APIError) as exc_info:
            await client.search_pages("type=page")

        assert "network error" in str(exc_info.value).lower()


class TestRetryLogic:
    """Tests for retry logic on rate limit errors."""

    @pytest.mark.asyncio
    async def test_rate_limit_retry_success(
        self, auth_strategy: APITokenAuth, base_url: str, httpx_mock: HTTPXMock
    ) -> None:
        """Test successful retry after rate limit error."""
        # Create client with retries enabled
        async with ConfluenceClient(base_url, auth_strategy, max_retries=2) as client:
            # First request returns 429
            httpx_mock.add_response(
                url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
                status_code=429,
                headers={"Retry-After": "0"},  # No wait for testing
            )

            # Second request (retry) succeeds
            httpx_mock.add_response(
                url="https://test.atlassian.net/wiki/rest/api/content/search?cql=type%3Dpage&limit=25&start=0",
                json={
                    "results": [],
                    "start": 0,
                    "limit": 25,
                    "size": 0,
                },
            )

            # Should succeed after retry
            response = await client.search_pages("type=page")
            assert response is not None
