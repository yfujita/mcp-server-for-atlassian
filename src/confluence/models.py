"""
Pydantic models for Confluence API data.

Defines type-safe data models for API requests and responses.
These models provide:
- Automatic validation
- Type hints for better IDE support
- Serialization/deserialization
- Documentation through field descriptions
"""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

# Generic type for paginated response
T = TypeVar("T")


class PageSearchResult(BaseModel):
    """
    Result from a Confluence page search.

    Represents a single page in search results with minimal metadata.
    """

    id: str = Field(..., description="Unique page identifier")
    title: str = Field(..., description="Page title")
    url: HttpUrl = Field(..., description="Full URL to the page")
    space_key: Optional[str] = Field(None, description="Space key where page resides")
    excerpt: Optional[str] = Field(None, description="Search result excerpt/snippet")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123456",
                "title": "API Documentation",
                "url": "https://example.atlassian.net/wiki/spaces/DEV/pages/123456",
                "space_key": "DEV",
                "excerpt": "This page contains API documentation...",
            }
        }
    )


class PageContent(BaseModel):
    """
    Full content of a Confluence page.

    Contains all page data including the main content body,
    metadata, and version information.
    """

    id: str = Field(..., description="Unique page identifier")
    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Page content (HTML or Markdown)")
    content_format: str = Field(..., description="Format of content: 'html' or 'markdown'")
    url: HttpUrl = Field(..., description="Full URL to the page")
    space_key: str = Field(..., description="Space key where page resides")
    version: int = Field(..., description="Current page version number")
    last_modified: Optional[datetime] = Field(None, description="Last modification timestamp")
    author: Optional[str] = Field(None, description="Last author display name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123456",
                "title": "API Documentation",
                "content": "# API Documentation\\n\\nThis is the main content...",
                "content_format": "markdown",
                "url": "https://example.atlassian.net/wiki/spaces/DEV/pages/123456",
                "space_key": "DEV",
                "version": 5,
                "last_modified": "2024-01-15T10:30:00Z",
                "author": "John Doe",
            }
        }
    )


class ChildPage(BaseModel):
    """
    Child page metadata.

    Represents a child page in a page hierarchy with minimal information.
    """

    id: str = Field(..., description="Unique page identifier")
    title: str = Field(..., description="Page title")
    url: Optional[HttpUrl] = Field(None, description="Full URL to the page")
    position: Optional[int] = Field(None, description="Position in child page list")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "789012",
                "title": "Getting Started",
                "url": "https://example.atlassian.net/wiki/spaces/DEV/pages/789012",
                "position": 0,
            }
        }
    )


class SearchParams(BaseModel):
    """
    Parameters for page search requests.

    Used to validate and structure search query parameters.
    """

    cql: str = Field(..., description="CQL query string")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results (1-100)")
    start: int = Field(default=0, ge=0, description="Starting index for pagination")

    model_config = ConfigDict(
        json_schema_extra={"example": {"cql": "type=page AND space=DEV", "limit": 10, "start": 0}}
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response from Confluence API.

    Wraps results with pagination metadata to handle large result sets.
    """

    results: List[T] = Field(..., description="List of results for current page")
    start: int = Field(..., description="Starting index of this page")
    limit: int = Field(..., description="Maximum number of results per page")
    size: int = Field(..., description="Actual number of results in this page")
    total_size: Optional[int] = Field(None, description="Total number of results available")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [],
                "start": 0,
                "limit": 25,
                "size": 10,
                "total_size": 100,
            }
        }
    )
