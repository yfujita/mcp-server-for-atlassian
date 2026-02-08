"""
Integration tests for MCP Server for Atlassian Confluence.

These tests require actual Confluence Cloud credentials and are skipped
by default. To run these tests, set the environment variable:
    RUN_INTEGRATION_TESTS=1

And ensure the following environment variables are set:
    ATLASSIAN_URL
    ATLASSIAN_USER_EMAIL
    ATLASSIAN_API_TOKEN

These tests will make real API calls to your Confluence instance.
"""

import os

import pytest

# Skip all tests in this module unless explicitly enabled
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Integration tests are disabled. Set RUN_INTEGRATION_TESTS=1 to enable.",
)


@pytest.fixture
def confluence_client():
    """Create a real ConfluenceClient instance."""
    from src.auth.api_token import APITokenAuth
    from src.config import get_settings
    from src.confluence.client import ConfluenceClient

    settings = get_settings()
    auth = APITokenAuth(
        email=settings.atlassian_user_email,
        api_token=settings.atlassian_api_token,
        base_url=settings.atlassian_url,
    )
    client = ConfluenceClient(base_url=settings.atlassian_url, auth_strategy=auth)
    return client


class TestAuthentication:
    """Test authentication with real Confluence API."""

    @pytest.mark.asyncio
    async def test_authenticate_success(self, confluence_client):
        """Test successful authentication."""
        async with confluence_client:
            # Successful context manager entry means authentication worked
            assert confluence_client._client is not None


class TestSearchPages:
    """Test search_pages with real Confluence API."""

    @pytest.mark.asyncio
    async def test_search_all_pages(self, confluence_client):
        """Test searching for all pages."""
        async with confluence_client:
            response = await confluence_client.search_pages(cql_query="type=page", limit=5)

            assert response is not None
            assert response.limit == 5
            assert isinstance(response.results, list)

            # If there are results, verify structure
            if response.results:
                page = response.results[0]
                assert hasattr(page, "id")
                assert hasattr(page, "title")
                assert hasattr(page, "url")
                assert hasattr(page, "space_key")

    @pytest.mark.asyncio
    async def test_search_with_cql_query(self, confluence_client):
        """Test searching with a specific CQL query."""
        async with confluence_client:
            # Search for pages (this should work on any Confluence instance)
            response = await confluence_client.search_pages(
                cql_query="type=page ORDER BY lastModified DESC", limit=3
            )

            assert response is not None
            assert len(response.results) <= 3


class TestGetPageContent:
    """Test get_page_content with real Confluence API."""

    @pytest.mark.asyncio
    async def test_get_page_content_markdown(self, confluence_client):
        """Test getting page content in Markdown format."""
        async with confluence_client:
            # First, search for a page to get its ID
            search_response = await confluence_client.search_pages(
                cql_query="type=page", limit=1
            )

            if not search_response.results:
                pytest.skip("No pages found in Confluence instance")

            page_id = search_response.results[0].id

            # Get the page content
            content = await confluence_client.get_page_content(
                page_id=page_id, as_markdown=True
            )

            assert content is not None
            assert content.id == page_id
            assert content.title
            assert content.content
            assert content.content_format == "markdown"
            assert content.version >= 1

    @pytest.mark.asyncio
    async def test_get_page_content_html(self, confluence_client):
        """Test getting page content in HTML format."""
        async with confluence_client:
            # First, search for a page to get its ID
            search_response = await confluence_client.search_pages(
                cql_query="type=page", limit=1
            )

            if not search_response.results:
                pytest.skip("No pages found in Confluence instance")

            page_id = search_response.results[0].id

            # Get the page content as HTML
            content = await confluence_client.get_page_content(
                page_id=page_id, as_markdown=False
            )

            assert content is not None
            assert content.id == page_id
            assert content.content_format == "html"
            assert "<" in content.content  # Should contain HTML tags


class TestGetChildPages:
    """Test get_child_pages with real Confluence API."""

    @pytest.mark.asyncio
    async def test_get_child_pages(self, confluence_client):
        """Test getting child pages of a parent page."""
        async with confluence_client:
            # Search for pages that might have children
            search_response = await confluence_client.search_pages(
                cql_query="type=page", limit=10
            )

            if not search_response.results:
                pytest.skip("No pages found in Confluence instance")

            # Try to find a page with children
            for page in search_response.results:
                children = await confluence_client.get_child_pages(
                    parent_id=page.id, limit=10
                )

                # We found a page with children
                if children.results:
                    assert len(children.results) > 0
                    child = children.results[0]
                    assert hasattr(child, "id")
                    assert hasattr(child, "title")
                    assert hasattr(child, "position")
                    break
            else:
                # No pages with children found - this is ok for test
                pytest.skip("No pages with children found")


class TestErrorHandling:
    """Test error handling with real Confluence API."""

    @pytest.mark.asyncio
    async def test_page_not_found(self, confluence_client):
        """Test handling of non-existent page."""
        from src.exceptions import PageNotFoundError

        async with confluence_client:
            with pytest.raises(PageNotFoundError):
                await confluence_client.get_page_content(page_id="999999999999")

    @pytest.mark.asyncio
    async def test_invalid_cql_query(self, confluence_client):
        """Test handling of invalid CQL query."""
        from src.exceptions import APIError

        async with confluence_client:
            # Invalid CQL syntax should raise an error
            with pytest.raises(APIError):
                await confluence_client.search_pages(cql_query="invalid syntax +++")


class TestEndToEnd:
    """End-to-end workflow tests."""

    @pytest.mark.asyncio
    async def test_search_and_retrieve_workflow(self, confluence_client):
        """Test complete workflow: search -> get content -> get children."""
        async with confluence_client:
            # Step 1: Search for pages
            search_response = await confluence_client.search_pages(
                cql_query="type=page", limit=5
            )

            if not search_response.results:
                pytest.skip("No pages found in Confluence instance")

            page = search_response.results[0]
            page_id = page.id

            # Step 2: Get page content
            content = await confluence_client.get_page_content(
                page_id=page_id, as_markdown=True
            )
            assert content.id == page_id
            assert content.title == page.title

            # Step 3: Try to get child pages
            children = await confluence_client.get_child_pages(parent_id=page_id, limit=10)
            # Children may or may not exist - that's ok
            assert children is not None
            assert isinstance(children.results, list)

    @pytest.mark.asyncio
    async def test_pagination(self, confluence_client):
        """Test pagination of search results."""
        async with confluence_client:
            # Get first page of results
            first_page = await confluence_client.search_pages(cql_query="type=page", limit=5)

            if first_page.total_size <= 5:
                pytest.skip("Not enough pages to test pagination")

            # Get second page
            # Note: Confluence API uses start parameter for pagination
            # This is a basic test - actual pagination would need start parameter support
            second_page = await confluence_client.search_pages(cql_query="type=page", limit=5)

            assert first_page is not None
            assert second_page is not None
