"""
Authentication strategies for Atlassian API.

This module provides a pluggable authentication system using the Strategy pattern.
Different authentication methods (API Token, OAuth2) can be swapped without
changing the client code.

Modules:
    base: Abstract base class for authentication strategies
    api_token: API Token (Basic Auth) implementation
    oauth2: OAuth 2.0 (3LO) implementation (future)
"""

from src.auth.base import AuthenticationStrategy
from src.auth.api_token import APITokenAuth

__all__ = [
    "AuthenticationStrategy",
    "APITokenAuth",
]
