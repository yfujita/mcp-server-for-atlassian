"""
Abstract base class for authentication strategies.

Defines the interface that all authentication implementations must follow.
This abstraction allows easy switching between different auth methods
(API Token, OAuth2, etc.) without modifying client code.
"""

from abc import ABC, abstractmethod
from typing import Dict


class AuthenticationStrategy(ABC):
    """
    Abstract base class for authentication strategies.

    All authentication implementations must inherit from this class
    and implement the required methods.
    """

    @abstractmethod
    async def get_auth_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers required for authentication.

        Returns:
            Dict[str, str]: Headers to include in API requests
                          (e.g., {"Authorization": "Bearer token"})

        Raises:
            AuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Perform authentication and validate credentials.

        Returns:
            bool: True if authentication is successful

        Raises:
            AuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    async def is_authenticated(self) -> bool:
        """
        Check if currently authenticated.

        Returns:
            bool: True if authenticated and token is valid
        """
        pass
