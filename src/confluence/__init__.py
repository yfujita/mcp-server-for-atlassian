"""
Confluence API client and utilities.

This module provides a high-level client for interacting with the
Atlassian Confluence REST API v1. It handles authentication, HTTP
communication, error handling, and data transformation.

Modules:
    client: Main API client for Confluence operations
    models: Pydantic models for API request/response data
    converters: HTML to Markdown conversion utilities
"""

from src.confluence.client import ConfluenceClient
from src.confluence.models import ChildPage, PageContent, PageSearchResult

__all__ = [
    "ConfluenceClient",
    "PageSearchResult",
    "PageContent",
    "ChildPage",
]
