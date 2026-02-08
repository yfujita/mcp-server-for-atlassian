"""
Type definitions for MCP tool return values.

These TypedDicts provide precise type hints for the dictionaries
returned by MCP tools, improving type safety and IDE autocomplete.
"""

from typing import Optional

from typing_extensions import TypedDict


class PageSearchResultDict(TypedDict):
    """
    Type definition for page search result dictionary.

    Returned by search_pages tool for each matching page.
    """

    id: str
    title: str
    url: str
    space_key: Optional[str]
    excerpt: str


class PageContentDict(TypedDict):
    """
    Type definition for page content dictionary.

    Returned by get_page_content tool.
    """

    id: str
    title: str
    content: str
    content_format: str
    url: str
    space_key: str
    version: int
    last_modified: Optional[str]
    author: Optional[str]


class ChildPageDict(TypedDict):
    """
    Type definition for child page dictionary.

    Returned by get_child_pages tool for each child page.
    """

    id: str
    title: str
    url: str
    position: int
