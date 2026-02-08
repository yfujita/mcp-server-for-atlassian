"""
Configuration management for the MCP server.

Uses Pydantic Settings for type-safe configuration loading from environment
variables and .env files. All sensitive information (API tokens, credentials)
should be provided through environment variables.
"""

import logging
from functools import lru_cache
from typing import Optional
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        atlassian_url: Base URL for Confluence instance (e.g., https://domain.atlassian.net/wiki)
        atlassian_user_email: User email for API Token authentication
        atlassian_api_token: API Token for authentication
        mcp_transport: Transport protocol (stdio/sse/streamable_http)
        mcp_host: Host for SSE/HTTP transport
        mcp_port: Port for SSE/HTTP transport
    """

    # Atlassian Confluence settings
    atlassian_url: str = Field(..., description="Base URL for Confluence instance")
    atlassian_user_email: str = Field(..., description="User email for API Token authentication")
    atlassian_api_token: str = Field(..., description="API Token from Atlassian")

    # MCP server settings
    mcp_transport: str = Field(
        default="stdio", description="Transport protocol: stdio, sse, or streamable_http"
    )
    mcp_host: str = Field(default="0.0.0.0", description="Host for SSE/HTTP transport")
    mcp_port: int = Field(default=8000, description="Port for SSE/HTTP transport")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("atlassian_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """
        Validate URL format and ensure it's a valid HTTP/HTTPS URL.

        Args:
            v: URL string to validate

        Returns:
            str: Validated URL without trailing slash

        Raises:
            ValueError: If URL is invalid or missing required components
        """
        if not v:
            raise ValueError("URL cannot be empty")

        # Parse URL to validate structure
        parsed = urlparse(v)

        # Check scheme: must be http or https
        if not parsed.scheme:
            raise ValueError(
                f"URL must include a scheme (http:// or https://). Got: {v}"
            )

        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                f"URL scheme must be 'http' or 'https'. Got: {parsed.scheme}://"
            )

        # Warn if using non-HTTPS
        if parsed.scheme == "http":
            logger.warning(
                f"Using non-HTTPS URL: {v}. Consider using HTTPS for secure communication."
            )

        # Check that host/netloc exists
        if not parsed.netloc:
            raise ValueError(
                f"URL must include a host (e.g., domain.atlassian.net). Got: {v}"
            )

        # Remove trailing slash
        return v.rstrip("/")

    @field_validator("mcp_transport")
    @classmethod
    def validate_transport(cls, v: str) -> str:
        """Validate transport is one of the supported types."""
        allowed = {"stdio", "sse", "streamable_http"}
        if v not in allowed:
            raise ValueError(f"Transport must be one of {allowed}, got: {v}")
        return v

    def __repr__(self) -> str:
        """
        Return string representation with masked sensitive information.

        Masks:
        - API token: Shows only last 4 characters (e.g., ****abcd)
        - Email: Shows only first character and domain (e.g., u***@example.com)

        Returns:
            str: Safe representation for logging
        """
        # API tokenのマスキング（末尾4文字のみ表示）
        masked_token = (
            f"****{self.atlassian_api_token[-4:]}"
            if len(self.atlassian_api_token) >= 4
            else "****"
        )

        # Emailのマスキング（先頭1文字とドメインのみ表示）
        email_parts = self.atlassian_user_email.split("@")
        if len(email_parts) == 2:
            local_part = email_parts[0]
            domain = email_parts[1]
            masked_email = f"{local_part[0]}***@{domain}" if local_part else f"***@{domain}"
        else:
            # @がない場合は全体をマスク
            masked_email = "***"

        return (
            f"Settings("
            f"atlassian_url={self.atlassian_url!r}, "
            f"atlassian_user_email={masked_email!r}, "
            f"atlassian_api_token={masked_token!r}, "
            f"mcp_transport={self.mcp_transport!r}, "
            f"mcp_host={self.mcp_host!r}, "
            f"mcp_port={self.mcp_port!r}"
            f")"
        )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings loaded from environment

    Note:
        Settings are cached to avoid repeated file I/O and validation.
        Clear cache with get_settings.cache_clear() if needed.
    """
    return Settings()
