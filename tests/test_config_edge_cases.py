"""
Additional edge case tests for configuration module.

Tests edge cases in email masking that aren't covered by main tests.
"""

import pytest
from pydantic import ValidationError

from src.config import Settings


class TestSettingsEmailMasking:
    """Test suite for email masking edge cases."""

    def test_repr_masks_email_without_at_symbol(self, monkeypatch) -> None:
        """Test that email without @ symbol is fully masked (line 131)."""
        # Set environment variables for valid configuration
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "invalidemail")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token_12345")

        settings = Settings()
        repr_str = repr(settings)

        # Email without @ should be masked as "***"
        assert "atlassian_user_email='***'" in repr_str

    def test_repr_masks_email_with_empty_local_part(self, monkeypatch) -> None:
        """Test that email with empty local part is properly masked."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token_12345")

        settings = Settings()
        repr_str = repr(settings)

        # Email with empty local part should show ***@domain
        assert "atlassian_user_email='***@example.com'" in repr_str

    def test_repr_includes_all_fields(self, monkeypatch) -> None:
        """Test that __repr__ includes all non-sensitive fields."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token_12345")
        monkeypatch.setenv("MCP_TRANSPORT", "sse")
        monkeypatch.setenv("MCP_HOST", "localhost")
        monkeypatch.setenv("MCP_PORT", "9000")

        settings = Settings()
        repr_str = repr(settings)

        # All fields should be present
        assert "atlassian_url='https://test.atlassian.net/wiki'" in repr_str
        assert "mcp_transport='sse'" in repr_str
        assert "mcp_host='localhost'" in repr_str
        assert "mcp_port=9000" in repr_str
