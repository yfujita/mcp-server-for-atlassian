"""
Tests for Confluence data models.

Tests Pydantic model validation, serialization, and deserialization.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.confluence.models import (
    PageSearchResult,
    PageContent,
    ChildPage,
    SearchParams,
    PaginatedResponse,
)


class TestPageSearchResult:
    """Tests for PageSearchResult model."""

    def test_valid_page_search_result(self) -> None:
        """Test creating a valid PageSearchResult."""
        result = PageSearchResult(
            id="123456",
            title="Test Page",
            url="https://example.atlassian.net/wiki/spaces/DEV/pages/123456",
            space_key="DEV",
            excerpt="This is a test page",
        )

        assert result.id == "123456"
        assert result.title == "Test Page"
        assert result.space_key == "DEV"
        assert result.excerpt == "This is a test page"

    def test_page_search_result_without_optional_fields(self) -> None:
        """Test PageSearchResult with minimal required fields."""
        result = PageSearchResult(
            id="123456",
            title="Test Page",
            url="https://example.atlassian.net/wiki/spaces/DEV/pages/123456",
        )

        assert result.id == "123456"
        assert result.title == "Test Page"
        assert result.space_key is None
        assert result.excerpt is None

    def test_page_search_result_invalid_url(self) -> None:
        """Test PageSearchResult with invalid URL."""
        with pytest.raises(ValidationError):
            PageSearchResult(
                id="123456",
                title="Test Page",
                url="not-a-valid-url",
            )


class TestPageContent:
    """Tests for PageContent model."""

    def test_valid_page_content(self) -> None:
        """Test creating a valid PageContent."""
        content = PageContent(
            id="123456",
            title="Test Page",
            content="# Test\n\nThis is content",
            content_format="markdown",
            url="https://example.atlassian.net/wiki/spaces/DEV/pages/123456",
            space_key="DEV",
            version=5,
            last_modified=datetime(2024, 1, 15, 10, 30, 0),
            author="John Doe",
        )

        assert content.id == "123456"
        assert content.title == "Test Page"
        assert content.content == "# Test\n\nThis is content"
        assert content.content_format == "markdown"
        assert content.space_key == "DEV"
        assert content.version == 5
        assert content.author == "John Doe"

    def test_page_content_without_optional_fields(self) -> None:
        """Test PageContent with minimal required fields."""
        content = PageContent(
            id="123456",
            title="Test Page",
            content="Content",
            content_format="html",
            url="https://example.atlassian.net/wiki/spaces/DEV/pages/123456",
            space_key="DEV",
            version=1,
        )

        assert content.id == "123456"
        assert content.last_modified is None
        assert content.author is None


class TestChildPage:
    """Tests for ChildPage model."""

    def test_valid_child_page(self) -> None:
        """Test creating a valid ChildPage."""
        child = ChildPage(
            id="789012",
            title="Child Page",
            url="https://example.atlassian.net/wiki/spaces/DEV/pages/789012",
            position=0,
        )

        assert child.id == "789012"
        assert child.title == "Child Page"
        assert child.position == 0

    def test_child_page_without_optional_fields(self) -> None:
        """Test ChildPage with minimal required fields."""
        child = ChildPage(
            id="789012",
            title="Child Page",
        )

        assert child.id == "789012"
        assert child.title == "Child Page"
        assert child.url is None
        assert child.position is None


class TestSearchParams:
    """Tests for SearchParams model."""

    def test_valid_search_params(self) -> None:
        """Test creating valid SearchParams."""
        params = SearchParams(
            cql="type=page AND space=DEV",
            limit=25,
            start=0,
        )

        assert params.cql == "type=page AND space=DEV"
        assert params.limit == 25
        assert params.start == 0

    def test_search_params_with_defaults(self) -> None:
        """Test SearchParams with default values."""
        params = SearchParams(cql="type=page")

        assert params.cql == "type=page"
        assert params.limit == 10  # Default
        assert params.start == 0  # Default

    def test_search_params_limit_validation(self) -> None:
        """Test SearchParams limit validation."""
        # Valid limits
        SearchParams(cql="type=page", limit=1)
        SearchParams(cql="type=page", limit=100)

        # Invalid limits (too small)
        with pytest.raises(ValidationError):
            SearchParams(cql="type=page", limit=0)

        # Invalid limits (too large)
        with pytest.raises(ValidationError):
            SearchParams(cql="type=page", limit=101)

    def test_search_params_start_validation(self) -> None:
        """Test SearchParams start validation."""
        # Valid start values
        SearchParams(cql="type=page", start=0)
        SearchParams(cql="type=page", start=100)

        # Invalid start (negative)
        with pytest.raises(ValidationError):
            SearchParams(cql="type=page", start=-1)


class TestPaginatedResponse:
    """Tests for PaginatedResponse model."""

    def test_valid_paginated_response(self) -> None:
        """Test creating a valid PaginatedResponse."""
        response = PaginatedResponse[PageSearchResult](
            results=[
                PageSearchResult(
                    id="123456",
                    title="Page 1",
                    url="https://example.atlassian.net/wiki/pages/123456",
                )
            ],
            start=0,
            limit=25,
            size=1,
            total_size=100,
        )

        assert len(response.results) == 1
        assert response.start == 0
        assert response.limit == 25
        assert response.size == 1
        assert response.total_size == 100

    def test_paginated_response_empty_results(self) -> None:
        """Test PaginatedResponse with empty results."""
        response = PaginatedResponse[PageSearchResult](
            results=[],
            start=0,
            limit=25,
            size=0,
            total_size=0,
        )

        assert len(response.results) == 0
        assert response.size == 0
        assert response.total_size == 0

    def test_paginated_response_without_total_size(self) -> None:
        """Test PaginatedResponse without total_size (optional)."""
        response = PaginatedResponse[PageSearchResult](
            results=[],
            start=0,
            limit=25,
            size=0,
        )

        assert response.total_size is None

    def test_paginated_response_with_child_pages(self) -> None:
        """Test PaginatedResponse with ChildPage type."""
        response = PaginatedResponse[ChildPage](
            results=[
                ChildPage(id="1", title="Child 1"),
                ChildPage(id="2", title="Child 2"),
            ],
            start=0,
            limit=50,
            size=2,
            total_size=2,
        )

        assert len(response.results) == 2
        assert all(isinstance(child, ChildPage) for child in response.results)
