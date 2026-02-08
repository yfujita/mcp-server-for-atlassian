"""
API Token authentication implementation.

Implements Basic Authentication using Atlassian API Tokens.
This is the recommended authentication method for server-to-server
integrations with Atlassian Cloud.

Reference: https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/
"""

import base64
from typing import Dict, Optional

import httpx

from src.auth.base import AuthenticationStrategy
from src.exceptions import AuthenticationError, APIError, RateLimitError


class APITokenAuth(AuthenticationStrategy):
    """
    API Token authentication using Basic Auth.

    Atlassian Cloud uses Basic Authentication with:
    - Username: User email address
    - Password: API Token

    The credentials are base64-encoded and sent in the Authorization header.
    """

    def __init__(self, email: str, api_token: str, base_url: Optional[str] = None) -> None:
        """
        Initialize API Token authentication.

        Args:
            email: User email address associated with the API token
            api_token: API token generated from Atlassian account settings
            base_url: Base URL for Confluence instance (optional, for validation)

        Raises:
            AuthenticationError: If email or api_token is empty
        """
        if not email or not api_token:
            raise AuthenticationError(
                "Email and API token are required",
                details="Both ATLASSIAN_USER_EMAIL and ATLASSIAN_API_TOKEN must be set",
            )

        self.email = email
        self.api_token = api_token
        self.base_url = base_url.rstrip("/") if base_url else None
        self._authenticated = False

        # Cache the Base64-encoded auth header to avoid repeated encoding
        credentials = f"{email}:{api_token}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        self._cached_auth_header = f"Basic {encoded}"

    async def get_auth_headers(self) -> Dict[str, str]:
        """
        Generate Basic Authentication header.

        Returns:
            Dict[str, str]: Authorization header with base64-encoded credentials

        Example:
            {"Authorization": "Basic ZW1haWxAZXhhbXBsZS5jb206dG9rZW4="}

        Note:
            The authorization header is cached in __init__ to avoid repeated Base64 encoding.
        """
        return {
            "Authorization": self._cached_auth_header,
            "Content-Type": "application/json",
        }

    async def authenticate(self) -> bool:
        """
        Validate API token by making a test API call.

        Makes a lightweight API call to /rest/api/user/current to verify
        the credentials are valid and the user has access to the Confluence instance.

        Returns:
            bool: True if authentication is successful

        Raises:
            AuthenticationError: If authentication fails (401, 403)
            APIError: If API call fails with other errors

        Note:
            Requires base_url to be set for validation.
        """
        if not self.base_url:
            # base_urlが設定されていない場合は検証をスキップ
            # （Phase 3以降でConfluenceClientから呼ばれる場合に使用）
            self._authenticated = True
            return True

        # 認証ヘッダーを取得
        headers = await self.get_auth_headers()
        headers["Accept"] = "application/json"

        # 軽量なエンドポイントで認証を検証
        # /rest/api/user/current は現在のユーザー情報を返すため認証確認に最適
        url = f"{self.base_url}/rest/api/user/current"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)

                # ステータスコードに応じたエラーハンドリング
                if response.status_code == 200:
                    self._authenticated = True
                    return True
                elif response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid credentials",
                        details="API token or email is incorrect. "
                        "Please verify your ATLASSIAN_API_TOKEN and ATLASSIAN_USER_EMAIL.",
                    )
                elif response.status_code == 403:
                    raise AuthenticationError(
                        "Access forbidden",
                        details="Valid credentials but insufficient permissions. "
                        "Ensure the user has access to the Confluence instance.",
                    )
                elif response.status_code == 429:
                    # レート制限エラー
                    retry_after = response.headers.get("Retry-After")
                    retry_after_seconds = int(retry_after) if retry_after else None
                    raise RateLimitError(
                        "Rate limit exceeded during authentication",
                        retry_after=retry_after_seconds,
                        details="Too many authentication attempts. Please wait before retrying.",
                    )
                else:
                    # その他のHTTPエラー
                    raise APIError(
                        f"Authentication failed with status {response.status_code}",
                        status_code=response.status_code,
                        details=response.text,
                    )

        except httpx.TimeoutException as e:
            raise APIError(
                "Authentication request timed out",
                details=f"Could not connect to {url}: {str(e)}",
            )
        except httpx.RequestError as e:
            raise APIError(
                "Network error during authentication",
                details=f"Failed to connect to {url}: {str(e)}",
            )
        except (AuthenticationError, APIError, RateLimitError):
            # カスタム例外はそのまま再送出
            raise
        except Exception as e:
            # 予期しないエラー
            raise APIError(
                "Unexpected error during authentication",
                details=f"Error: {type(e).__name__}: {str(e)}",
            )

    async def is_authenticated(self) -> bool:
        """
        Check if authenticated.

        Returns:
            bool: True if authenticated

        Note:
            API tokens don't expire, so once validated, they remain valid
            until revoked. In a production system, you might want to
            periodically re-validate.
        """
        return self._authenticated
