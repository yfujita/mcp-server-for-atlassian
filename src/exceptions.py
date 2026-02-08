"""
Custom exceptions for the MCP server.

Defines a hierarchy of exceptions for different error scenarios:
- Authentication errors
- API communication errors
- Data validation errors
- Configuration errors
"""

from typing import Optional


class MCPServerError(Exception):
    """Base exception for all MCP server errors."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        """
        Initialize exception with message and optional details.

        Args:
            message: Human-readable error message
            details: Additional technical details about the error
        """
        self.message = message
        self.details = details
        super().__init__(message)


class AuthenticationError(MCPServerError):
    """Raised when authentication fails."""

    def __init__(
        self, message: str = "Authentication failed", details: Optional[str] = None
    ) -> None:
        super().__init__(message, details)


class APIError(MCPServerError):
    """Raised when Confluence API returns an error."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, details: Optional[str] = None
    ) -> None:
        """
        Initialize API error with status code.

        Args:
            message: Error message
            status_code: HTTP status code if available
            details: Additional error details
        """
        self.status_code = status_code
        super().__init__(message, details)


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[str] = None,
    ) -> None:
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retry (from Retry-After header)
            details: Additional error details
        """
        self.retry_after = retry_after
        super().__init__(message, status_code=429, details=details)


class PageNotFoundError(APIError):
    """Raised when a requested page is not found."""

    def __init__(self, page_id: str, details: Optional[str] = None) -> None:
        """
        Initialize page not found error.

        Args:
            page_id: ID of the page that was not found
            details: Additional error details
        """
        self.page_id = page_id
        super().__init__(message=f"Page not found: {page_id}", status_code=404, details=details)


class ConfigurationError(MCPServerError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        super().__init__(message, details)


class ConversionError(MCPServerError):
    """Raised when HTML to Markdown conversion fails."""

    def __init__(
        self, message: str = "Failed to convert content", details: Optional[str] = None
    ) -> None:
        super().__init__(message, details)
