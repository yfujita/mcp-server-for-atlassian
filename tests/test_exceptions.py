"""
Tests for custom exceptions.

Tests all custom exception classes including:
- Base exception (MCPServerError)
- Authentication errors
- API errors
- Rate limit errors
- Configuration errors
- Conversion errors
"""

import pytest

from src.exceptions import (
    MCPServerError,
    AuthenticationError,
    APIError,
    RateLimitError,
    PageNotFoundError,
    ConfigurationError,
    ConversionError,
)


class TestMCPServerError:
    """Test suite for base MCPServerError exception."""

    def test_basic_initialization(self) -> None:
        """Test basic exception initialization."""
        error = MCPServerError("Test error message")
        assert error.message == "Test error message"
        assert error.details is None
        assert str(error) == "Test error message"

    def test_initialization_with_details(self) -> None:
        """Test exception initialization with details."""
        error = MCPServerError("Test error message", details="Additional technical details")
        assert error.message == "Test error message"
        assert error.details == "Additional technical details"

    def test_can_be_raised_and_caught(self) -> None:
        """Test that exception can be raised and caught."""
        with pytest.raises(MCPServerError) as exc_info:
            raise MCPServerError("Test error")
        assert "Test error" in str(exc_info.value)


class TestAuthenticationError:
    """Test suite for AuthenticationError exception."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = AuthenticationError()
        assert error.message == "Authentication failed"
        assert error.details is None

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = AuthenticationError("Invalid credentials")
        assert error.message == "Invalid credentials"

    def test_with_details(self) -> None:
        """Test error with details."""
        error = AuthenticationError("Invalid credentials", details="API token is incorrect")
        assert error.message == "Invalid credentials"
        assert error.details == "API token is incorrect"

    def test_inherits_from_mcp_server_error(self) -> None:
        """Test that AuthenticationError inherits from MCPServerError."""
        error = AuthenticationError()
        assert isinstance(error, MCPServerError)


class TestAPIError:
    """Test suite for APIError exception."""

    def test_basic_initialization(self) -> None:
        """Test basic API error initialization."""
        error = APIError("API call failed")
        assert error.message == "API call failed"
        assert error.status_code is None
        assert error.details is None

    def test_with_status_code(self) -> None:
        """Test API error with status code."""
        error = APIError("Server error", status_code=500)
        assert error.message == "Server error"
        assert error.status_code == 500

    def test_with_status_code_and_details(self) -> None:
        """Test API error with status code and details."""
        error = APIError("Bad request", status_code=400, details="Invalid parameter: page_id")
        assert error.message == "Bad request"
        assert error.status_code == 400
        assert error.details == "Invalid parameter: page_id"

    def test_inherits_from_mcp_server_error(self) -> None:
        """Test that APIError inherits from MCPServerError."""
        error = APIError("Test")
        assert isinstance(error, MCPServerError)


class TestRateLimitError:
    """Test suite for RateLimitError exception."""

    def test_default_message(self) -> None:
        """Test default rate limit error message."""
        error = RateLimitError()
        assert error.message == "Rate limit exceeded"
        assert error.status_code == 429
        assert error.retry_after is None

    def test_with_retry_after(self) -> None:
        """Test rate limit error with retry_after."""
        error = RateLimitError(retry_after=60)
        assert error.message == "Rate limit exceeded"
        assert error.retry_after == 60
        assert error.status_code == 429

    def test_with_custom_message_and_details(self) -> None:
        """Test rate limit error with custom message and details."""
        error = RateLimitError(
            message="Too many requests", retry_after=120, details="Exceeded 100 requests per minute"
        )
        assert error.message == "Too many requests"
        assert error.retry_after == 120
        assert error.details == "Exceeded 100 requests per minute"

    def test_inherits_from_api_error(self) -> None:
        """Test that RateLimitError inherits from APIError."""
        error = RateLimitError()
        assert isinstance(error, APIError)
        assert isinstance(error, MCPServerError)


class TestPageNotFoundError:
    """Test suite for PageNotFoundError exception."""

    def test_basic_initialization(self) -> None:
        """Test basic page not found error."""
        error = PageNotFoundError("12345")
        assert error.page_id == "12345"
        assert "12345" in error.message
        assert error.status_code == 404

    def test_with_details(self) -> None:
        """Test page not found error with details."""
        error = PageNotFoundError("67890", details="Page may have been deleted")
        assert error.page_id == "67890"
        assert "67890" in error.message
        assert error.details == "Page may have been deleted"

    def test_inherits_from_api_error(self) -> None:
        """Test that PageNotFoundError inherits from APIError."""
        error = PageNotFoundError("12345")
        assert isinstance(error, APIError)
        assert isinstance(error, MCPServerError)


class TestConfigurationError:
    """Test suite for ConfigurationError exception."""

    def test_basic_initialization(self) -> None:
        """Test basic configuration error."""
        error = ConfigurationError("Invalid configuration")
        assert error.message == "Invalid configuration"
        assert error.details is None

    def test_with_details(self) -> None:
        """Test configuration error with details."""
        error = ConfigurationError(
            "Missing required setting", details="ATLASSIAN_API_TOKEN is not set"
        )
        assert error.message == "Missing required setting"
        assert error.details == "ATLASSIAN_API_TOKEN is not set"

    def test_inherits_from_mcp_server_error(self) -> None:
        """Test that ConfigurationError inherits from MCPServerError."""
        error = ConfigurationError("Test")
        assert isinstance(error, MCPServerError)


class TestConversionError:
    """Test suite for ConversionError exception."""

    def test_default_message(self) -> None:
        """Test default conversion error message."""
        error = ConversionError()
        assert error.message == "Failed to convert content"
        assert error.details is None

    def test_custom_message(self) -> None:
        """Test custom conversion error message."""
        error = ConversionError("Markdown conversion failed")
        assert error.message == "Markdown conversion failed"

    def test_with_details(self) -> None:
        """Test conversion error with details."""
        error = ConversionError("HTML parsing failed", details="Invalid HTML structure")
        assert error.message == "HTML parsing failed"
        assert error.details == "Invalid HTML structure"

    def test_inherits_from_mcp_server_error(self) -> None:
        """Test that ConversionError inherits from MCPServerError."""
        error = ConversionError()
        assert isinstance(error, MCPServerError)


class TestExceptionHierarchy:
    """Test suite for exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_base(self) -> None:
        """Test that all custom exceptions inherit from MCPServerError."""
        exceptions = [
            AuthenticationError(),
            APIError("test"),
            RateLimitError(),
            PageNotFoundError("123"),
            ConfigurationError("test"),
            ConversionError(),
        ]

        for exc in exceptions:
            assert isinstance(exc, MCPServerError)
            assert isinstance(exc, Exception)

    def test_exception_hierarchy_structure(self) -> None:
        """Test the exception hierarchy structure."""
        # APIError系の継承関係
        rate_limit_error = RateLimitError()
        assert isinstance(rate_limit_error, RateLimitError)
        assert isinstance(rate_limit_error, APIError)
        assert isinstance(rate_limit_error, MCPServerError)

        # PageNotFoundError系の継承関係
        not_found_error = PageNotFoundError("123")
        assert isinstance(not_found_error, PageNotFoundError)
        assert isinstance(not_found_error, APIError)
        assert isinstance(not_found_error, MCPServerError)
