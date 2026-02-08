"""
Confluence API client implementation.

Provides a high-level interface for interacting with the Confluence REST API.
Handles authentication, request construction, error handling, and response parsing.

API Reference: https://developer.atlassian.com/cloud/confluence/rest/v1/intro/
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from src.auth.base import AuthenticationStrategy
from src.confluence.converters import html_to_markdown
from src.confluence.models import ChildPage, PageContent, PageSearchResult, PaginatedResponse
from src.exceptions import APIError, AuthenticationError, PageNotFoundError, RateLimitError

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """
    Client for Confluence REST API v1.

    Provides methods to search pages, get page content, and retrieve
    child pages. Uses httpx for async HTTP communication.

    Usage:
        async with ConfluenceClient(base_url, auth_strategy) as client:
            results = await client.search_pages("type=page AND space=DOCS")
    """

    # Class constants for API limits and defaults
    MAX_RESULTS_PER_PAGE = 100
    MIN_RESULTS_PER_PAGE = 1
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_MAX_RETRIES = 3

    def __init__(
        self,
        base_url: str,
        auth_strategy: AuthenticationStrategy,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """
        Initialize Confluence client.

        Args:
            base_url: Base URL of Confluence instance (e.g., https://domain.atlassian.net/wiki)
            auth_strategy: Authentication strategy to use
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retries for rate limit errors (default: 3)
        """
        self.base_url = base_url.rstrip("/")
        self.auth_strategy = auth_strategy
        self.timeout = timeout
        self.max_retries = max_retries

        # API v1 base path
        self.api_base = f"{self.base_url}/rest/api"

        # HTTP client (initialized in __aenter__)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "ConfluenceClient":
        """
        Enter async context manager.

        Initializes HTTP client and validates authentication.

        Returns:
            ConfluenceClient: Self

        Raises:
            AuthenticationError: If authentication fails
        """
        # Initialize httpx client
        self._client = httpx.AsyncClient(timeout=self.timeout)

        # Validate authentication (ensure we can get headers)
        await self.auth_strategy.get_auth_headers()
        logger.info("Confluence client initialized successfully")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit async context manager.

        Closes HTTP client and cleans up resources.
        """
        await self.close()

    async def close(self) -> None:
        """Close HTTP client and clean up resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Confluence client closed")

    async def search_pages(
        self, cql_query: str, limit: int = 25, start: int = 0
    ) -> PaginatedResponse[PageSearchResult]:
        """
        Search Confluence pages using CQL (Confluence Query Language).

        Args:
            cql_query: CQL query string (e.g., "type=page AND space=DEV")
            limit: Maximum number of results to return (default: 25, max: 100)
            start: Starting index for pagination (default: 0)

        Returns:
            PaginatedResponse[PageSearchResult]: Paginated list of matching pages

        Raises:
            APIError: If API request fails
            RateLimitError: If rate limit is exceeded

        Example:
            >>> async with ConfluenceClient(url, auth) as client:
            ...     response = await client.search_pages("title ~ 'documentation'")
            ...     for page in response.results:
            ...         print(f"{page.title} - {page.url}")
        """
        logger.info(f"Searching pages with CQL: {cql_query}")
        logger.debug(f"Search parameters: limit={limit}, start={start}")

        # Validate limit: clamp between MIN and MAX
        limit = min(max(self.MIN_RESULTS_PER_PAGE, limit), self.MAX_RESULTS_PER_PAGE)

        # Build query parameters
        params = {"cql": cql_query, "limit": limit, "start": start}

        # Make API request
        endpoint = "/content/search"
        data = await self._make_request("GET", endpoint, params=params)

        # Parse response
        results = []
        for item in data.get("results", []):
            # Extract page data
            page_id = item.get("id", "")
            title = item.get("title", "")

            # Build URL
            # API returns _links.webui which is a relative path
            web_ui_path = item.get("_links", {}).get("webui", "")
            url = (
                f"{self.base_url}{web_ui_path}"
                if web_ui_path
                else f"{self.base_url}/pages/{page_id}"
            )

            # Extract space key (if available)
            space_key = None
            if "space" in item:
                space_key = item["space"].get("key")

            # Extract excerpt (if available)
            excerpt = item.get("excerpt", "")

            results.append(
                PageSearchResult(
                    id=page_id,
                    title=title,
                    url=url,
                    space_key=space_key,
                    excerpt=excerpt,
                )
            )

        # Build paginated response
        return PaginatedResponse[PageSearchResult](
            results=results,
            start=data.get("start", start),
            limit=data.get("limit", limit),
            size=data.get("size", len(results)),
            total_size=data.get("totalSize"),
        )

    async def get_page_content(self, page_id: str, as_markdown: bool = True) -> PageContent:
        """
        Get content of a specific Confluence page.

        Args:
            page_id: Page ID to retrieve
            as_markdown: Convert HTML content to Markdown (default: True)

        Returns:
            PageContent: Page data with content in requested format

        Raises:
            PageNotFoundError: If page doesn't exist
            APIError: If API request fails

        Example:
            >>> async with ConfluenceClient(url, auth) as client:
            ...     page = await client.get_page_content("123456")
            ...     print(page.title)
            ...     print(page.content)  # Markdown format
        """
        logger.info(f"Fetching content for page ID: {page_id}")
        logger.debug(f"Content fetch options: as_markdown={as_markdown}")

        # Request page with expanded body and metadata
        # expand=body.storage gets HTML content
        # expand=version,space gets metadata
        endpoint = f"/content/{page_id}"
        params = {"expand": "body.storage,version,space,history.lastUpdated"}

        # Make API request
        try:
            data = await self._make_request("GET", endpoint, params=params)
        except APIError as e:
            # Convert 404 to PageNotFoundError
            if e.status_code == 404:
                raise PageNotFoundError(
                    page_id, details=f"Page {page_id} not found"
                ) from e
            raise

        # Extract page data
        title = data.get("title", "")

        # Get HTML content from storage format
        html_content = data.get("body", {}).get("storage", {}).get("value", "")

        # Convert to markdown if requested
        if as_markdown and html_content:
            try:
                content = html_to_markdown(html_content)
                content_format = "markdown"
            except Exception as e:
                # Fall back to HTML if conversion fails
                logger.warning(f"Failed to convert HTML to Markdown: {e}. Using HTML instead.")
                content = html_content
                content_format = "html"
        else:
            content = html_content
            content_format = "html"

        # Build URL
        web_ui_path = data.get("_links", {}).get("webui", "")
        url = f"{self.base_url}{web_ui_path}" if web_ui_path else f"{self.base_url}/pages/{page_id}"

        # Extract metadata
        space_key = data.get("space", {}).get("key", "")
        version = data.get("version", {}).get("number", 1)

        # Extract last modified date and author
        last_modified = None
        author = None
        if "history" in data and "lastUpdated" in data["history"]:
            last_updated = data["history"]["lastUpdated"]
            # Parse date (format: 2024-01-15T10:30:00.000Z)
            when = last_updated.get("when")
            if when:
                from datetime import datetime

                try:
                    last_modified = datetime.fromisoformat(when.replace("Z", "+00:00"))
                except Exception as e:
                    logger.warning(f"Failed to parse date {when}: {e}")

            # Extract author name
            by = last_updated.get("by", {})
            author = by.get("displayName") or by.get("username")

        return PageContent(
            id=page_id,
            title=title,
            content=content,
            content_format=content_format,
            url=url,
            space_key=space_key,
            version=version,
            last_modified=last_modified,
            author=author,
        )

    async def get_child_pages(
        self, parent_id: str, limit: int = 50, start: int = 0
    ) -> PaginatedResponse[ChildPage]:
        """
        Get child pages of a parent page.

        Args:
            parent_id: Parent page ID
            limit: Maximum number of results (default: 50, max: 100)
            start: Starting index for pagination (default: 0)

        Returns:
            PaginatedResponse[ChildPage]: Paginated list of child pages

        Raises:
            PageNotFoundError: If parent page doesn't exist
            APIError: If API request fails

        Example:
            >>> async with ConfluenceClient(url, auth) as client:
            ...     response = await client.get_child_pages("123456")
            ...     for child in response.results:
            ...         print(f"{child.title} (ID: {child.id})")
        """
        logger.info(f"Fetching child pages for parent ID: {parent_id}")
        logger.debug(f"Child pages parameters: limit={limit}, start={start}")

        # Validate limit: clamp between MIN and MAX
        limit = min(max(self.MIN_RESULTS_PER_PAGE, limit), self.MAX_RESULTS_PER_PAGE)

        # Build endpoint and parameters
        endpoint = f"/content/{parent_id}/child/page"
        params = {"limit": limit, "start": start}

        # Make API request
        try:
            data = await self._make_request("GET", endpoint, params=params)
        except APIError as e:
            # Convert 404 to PageNotFoundError
            if e.status_code == 404:
                raise PageNotFoundError(
                    parent_id, details=f"Parent page {parent_id} not found"
                ) from e
            raise

        # Parse response
        results = []
        for idx, item in enumerate(data.get("results", [])):
            child_id = item.get("id", "")
            title = item.get("title", "")

            # Build URL
            web_ui_path = item.get("_links", {}).get("webui", "")
            url = (
                f"{self.base_url}{web_ui_path}"
                if web_ui_path
                else f"{self.base_url}/pages/{child_id}"
            )

            results.append(
                ChildPage(
                    id=child_id,
                    title=title,
                    url=url,
                    position=start + idx,
                )
            )

        # Build paginated response
        return PaginatedResponse[ChildPage](
            results=results,
            start=data.get("start", start),
            limit=data.get("limit", limit),
            size=data.get("size", len(results)),
            total_size=data.get("totalSize"),
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make authenticated HTTP request to Confluence API.

        Handles retries for rate limit errors (429) with exponential backoff.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (relative to api_base)
            params: Query parameters
            json_data: JSON request body
            retry_count: Current retry attempt (for internal use)

        Returns:
            dict: Parsed JSON response

        Raises:
            APIError: If request fails
            RateLimitError: If rate limited and max retries exceeded
            AuthenticationError: If authentication fails (401, 403)
        """
        if not self._client:
            raise APIError("Client not initialized. Use 'async with' context manager.")

        # Build full URL
        url = f"{self.api_base}{endpoint}"

        # Get authentication headers
        headers = await self.auth_strategy.get_auth_headers()
        headers["Accept"] = "application/json"

        try:
            # Make HTTP request
            logger.debug(f"{method} {url} (params={params})")
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers,
            )

            # Handle response based on status code
            if response.status_code == 200:
                # Success
                return response.json()

            elif response.status_code == 401:
                # Unauthorized - invalid credentials
                raise AuthenticationError(
                    "Authentication failed",
                    details="Invalid API token or email. Please check your credentials.",
                )

            elif response.status_code == 403:
                # Forbidden - valid credentials but insufficient permissions
                raise AuthenticationError(
                    "Access forbidden",
                    details=(
                        "Valid credentials but insufficient permissions to access this resource."
                    ),
                )

            elif response.status_code == 404:
                # Not found
                raise APIError(
                    "Resource not found",
                    status_code=404,
                    details=f"{method} {url} returned 404",
                )

            elif response.status_code == 429:
                # Rate limit exceeded
                retry_after = response.headers.get("Retry-After")
                retry_after_seconds = int(retry_after) if retry_after else None

                # Check if we can retry
                if retry_count < self.max_retries:
                    # Calculate wait time (exponential backoff with jitter)
                    wait_time = retry_after_seconds if retry_after_seconds else (2**retry_count)
                    logger.warning(
                        f"Rate limit exceeded. Retrying after {wait_time}s "
                        f"(attempt {retry_count + 1}/{self.max_retries})"
                    )

                    # Wait before retrying
                    await asyncio.sleep(wait_time)

                    # Retry request
                    return await self._make_request(
                        method=method,
                        endpoint=endpoint,
                        params=params,
                        json_data=json_data,
                        retry_count=retry_count + 1,
                    )
                else:
                    # Max retries exceeded
                    raise RateLimitError(
                        "Rate limit exceeded",
                        retry_after=retry_after_seconds,
                        details=f"Max retries ({self.max_retries}) exceeded",
                    )

            elif response.status_code >= 500:
                # Server error
                raise APIError(
                    f"Server error: {response.status_code}",
                    status_code=response.status_code,
                    details=response.text,
                )

            else:
                # Other HTTP errors
                raise APIError(
                    f"HTTP error: {response.status_code}",
                    status_code=response.status_code,
                    details=response.text,
                )

        except httpx.ConnectTimeout as e:
            # Retry on connection timeout with exponential backoff
            if retry_count < self.max_retries:
                wait_time = 2**retry_count  # 1, 2, 4 seconds
                logger.warning(
                    f"Connection timeout to {url}. Retrying after {wait_time}s "
                    f"(attempt {retry_count + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)
                return await self._make_request(
                    method=method,
                    endpoint=endpoint,
                    params=params,
                    json_data=json_data,
                    retry_count=retry_count + 1,
                )
            raise APIError(
                "Connection timeout",
                details=f"Failed to connect to {url} after {self.max_retries} retries: {str(e)}",
            ) from e

        except httpx.TimeoutException as e:
            # Other timeout errors (read, write, pool) - no retry
            raise APIError(
                "Request timed out",
                details=f"Request to {url} timed out after {self.timeout}s: {str(e)}",
            ) from e

        except httpx.ConnectError as e:
            # Retry on connection errors (network unreachable, DNS failure, etc.)
            if retry_count < self.max_retries:
                wait_time = 2**retry_count
                logger.warning(
                    f"Connection error to {url}. Retrying after {wait_time}s "
                    f"(attempt {retry_count + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)
                return await self._make_request(
                    method=method,
                    endpoint=endpoint,
                    params=params,
                    json_data=json_data,
                    retry_count=retry_count + 1,
                )
            raise APIError(
                "Connection error",
                details=f"Failed to connect to {url} after {self.max_retries} retries: {str(e)}",
            ) from e

        except httpx.RequestError as e:
            raise APIError(
                "Network error",
                details=f"Failed to connect to {url}: {str(e)}",
            ) from e

        except (AuthenticationError, APIError, RateLimitError):
            # Re-raise custom exceptions
            raise

        except Exception as e:
            # Unexpected errors
            raise APIError(
                "Unexpected error",
                details=f"Unexpected error during API request: {type(e).__name__}: {str(e)}",
            ) from e
