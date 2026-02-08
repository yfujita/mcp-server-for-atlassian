"""
Tests for configuration management.

Tests the Settings class including:
- Environment variable loading
- URL validation
- Default values
- Transport validation
"""

import os

import pytest
from pydantic import ValidationError

from src.config import Settings, get_settings


class TestSettings:
    """Test suite for Settings configuration."""

    def test_settings_with_valid_env_vars(self, monkeypatch) -> None:
        """Test Settings initialization with valid environment variables."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token_123")
        # .envファイルからの値をオーバーライドするため、明示的にデフォルト値を設定
        monkeypatch.setenv("MCP_TRANSPORT", "stdio")

        # キャッシュをクリア
        get_settings.cache_clear()

        settings = Settings()
        assert settings.atlassian_url == "https://test.atlassian.net/wiki"
        assert settings.atlassian_user_email == "test@example.com"
        assert settings.atlassian_api_token == "test_token_123"
        assert settings.mcp_transport == "stdio"  # デフォルト値
        assert settings.mcp_host == "0.0.0.0"  # デフォルト値
        assert settings.mcp_port == 8000  # デフォルト値

    def test_settings_removes_trailing_slash_from_url(self, monkeypatch) -> None:
        """Test that trailing slash is removed from URL."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki/")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token")

        settings = Settings()
        assert settings.atlassian_url == "https://test.atlassian.net/wiki"

    def test_settings_with_custom_transport(self, monkeypatch) -> None:
        """Test Settings with custom transport configuration."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token")
        monkeypatch.setenv("MCP_TRANSPORT", "sse")
        monkeypatch.setenv("MCP_HOST", "localhost")
        monkeypatch.setenv("MCP_PORT", "9000")

        settings = Settings()
        assert settings.mcp_transport == "sse"
        assert settings.mcp_host == "localhost"
        assert settings.mcp_port == 9000

    def test_settings_missing_required_field_raises_error(self, monkeypatch) -> None:
        """Test that missing required fields raise ValidationError."""
        # .envファイルの影響を受けないよう、env_fileを無効化したSettingsクラスを使用
        from pydantic_settings import BaseSettings, SettingsConfigDict
        from pydantic import Field

        class TestSettings(BaseSettings):
            atlassian_url: str = Field(..., description="Base URL for Confluence instance")
            atlassian_user_email: str = Field(
                ..., description="User email for API Token authentication"
            )
            atlassian_api_token: str = Field(..., description="API Token from Atlassian")

            model_config = SettingsConfigDict(env_file=None, case_sensitive=False, extra="ignore")

        # ATLASSIAN_URLのみ設定
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.delenv("ATLASSIAN_USER_EMAIL", raising=False)
        monkeypatch.delenv("ATLASSIAN_API_TOKEN", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            TestSettings()

        # 必須フィールドが不足していることを確認
        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "atlassian_user_email" in error_fields
        assert "atlassian_api_token" in error_fields

    def test_settings_invalid_transport_raises_error(self, monkeypatch) -> None:
        """Test that invalid transport raises ValidationError."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token")
        monkeypatch.setenv("MCP_TRANSPORT", "invalid_transport")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        # エラーメッセージにtransportが含まれていることを確認
        errors = exc_info.value.errors()
        transport_errors = [e for e in errors if "mcp_transport" in str(e["loc"])]
        assert len(transport_errors) > 0

    def test_settings_case_insensitive(self, monkeypatch) -> None:
        """Test that environment variables are case insensitive."""
        monkeypatch.setenv("atlassian_url", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("atlassian_user_email", "test@example.com")
        monkeypatch.setenv("atlassian_api_token", "test_token")

        settings = Settings()
        assert settings.atlassian_url == "https://test.atlassian.net/wiki"
        assert settings.atlassian_user_email == "test@example.com"

    def test_get_settings_returns_cached_instance(self, monkeypatch) -> None:
        """Test that get_settings returns cached instance."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token")

        # キャッシュをクリア
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        # 同じインスタンスであることを確認
        assert settings1 is settings2

    def test_transport_validation_allows_valid_values(self, monkeypatch) -> None:
        """Test that transport validation allows valid values."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token")

        valid_transports = ["stdio", "sse", "streamable_http"]

        for transport in valid_transports:
            monkeypatch.setenv("MCP_TRANSPORT", transport)
            settings = Settings()
            assert settings.mcp_transport == transport

    def test_repr_masks_api_token(self, monkeypatch) -> None:
        """Test that __repr__ masks API token showing only last 4 characters."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "secret_token_1234567890")

        settings = Settings()
        repr_str = repr(settings)

        # センシティブな値が含まれていないことを確認
        assert "secret_token_1234567890" not in repr_str
        # マスキングされた形式が含まれていることを確認（末尾4文字）
        assert "****7890" in repr_str

    def test_repr_masks_email(self, monkeypatch) -> None:
        """Test that __repr__ masks email showing only first character and domain."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "user123@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token")

        settings = Settings()
        repr_str = repr(settings)

        # 元のメールアドレスが含まれていないことを確認
        assert "user123@" not in repr_str
        # マスキングされた形式が含まれていることを確認
        assert "u***@example.com" in repr_str

    def test_repr_handles_short_token(self, monkeypatch) -> None:
        """Test that __repr__ handles short tokens correctly."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "abc")  # 短いトークン

        settings = Settings()
        repr_str = repr(settings)

        # 短いトークンの場合は完全にマスク
        assert "abc" not in repr_str
        assert "****" in repr_str

    def test_repr_includes_non_sensitive_fields(self, monkeypatch) -> None:
        """Test that __repr__ includes non-sensitive fields."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token")
        monkeypatch.setenv("MCP_TRANSPORT", "sse")
        monkeypatch.setenv("MCP_HOST", "localhost")
        monkeypatch.setenv("MCP_PORT", "9000")

        settings = Settings()
        repr_str = repr(settings)

        # センシティブでない情報は含まれることを確認
        assert "https://test.atlassian.net/wiki" in repr_str
        assert "sse" in repr_str
        assert "localhost" in repr_str
        assert "9000" in repr_str

    def test_url_validation_requires_scheme(self, monkeypatch) -> None:
        """Test that URL validation requires http:// or https:// scheme."""
        monkeypatch.setenv("ATLASSIAN_URL", "test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        url_errors = [e for e in errors if "atlassian_url" in str(e["loc"])]
        assert len(url_errors) > 0
        assert "scheme" in str(url_errors[0]["msg"]).lower()

    def test_url_validation_requires_valid_scheme(self, monkeypatch) -> None:
        """Test that URL validation only allows http or https."""
        monkeypatch.setenv("ATLASSIAN_URL", "ftp://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        url_errors = [e for e in errors if "atlassian_url" in str(e["loc"])]
        assert len(url_errors) > 0
        assert "http" in str(url_errors[0]["msg"]).lower()

    def test_url_validation_requires_host(self, monkeypatch) -> None:
        """Test that URL validation requires a host."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        url_errors = [e for e in errors if "atlassian_url" in str(e["loc"])]
        assert len(url_errors) > 0
        assert "host" in str(url_errors[0]["msg"]).lower()

    def test_url_validation_allows_valid_https_url(self, monkeypatch) -> None:
        """Test that URL validation allows valid HTTPS URLs."""
        monkeypatch.setenv("ATLASSIAN_URL", "https://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token")

        settings = Settings()
        assert settings.atlassian_url == "https://test.atlassian.net/wiki"

    def test_url_validation_allows_valid_http_url_with_warning(
        self, monkeypatch, caplog
    ) -> None:
        """Test that URL validation allows HTTP URLs but logs a warning."""
        import logging

        monkeypatch.setenv("ATLASSIAN_URL", "http://test.atlassian.net/wiki")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token")

        with caplog.at_level(logging.WARNING):
            settings = Settings()

        assert settings.atlassian_url == "http://test.atlassian.net/wiki"
        # Warning should be logged about non-HTTPS
        assert any("non-HTTPS" in record.message for record in caplog.records)

    def test_url_validation_rejects_empty_url(self, monkeypatch) -> None:
        """Test that URL validation rejects empty URLs."""
        monkeypatch.setenv("ATLASSIAN_URL", "")
        monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "test@example.com")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "test_token")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        # Empty string should fail validation
        assert len(errors) > 0
