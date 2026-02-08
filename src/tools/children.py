"""
Get child pages MCP tool implementation.

Implements the get_child_pages tool that retrieves the list of
child pages for a given parent page, useful for navigating
the Confluence page hierarchy.
"""

import logging
from typing import TYPE_CHECKING

from src.tools.types import ChildPageDict

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from src.confluence.client import ConfluenceClient

logger = logging.getLogger(__name__)


def register_children_tool(mcp: "FastMCP", client: "ConfluenceClient") -> None:
    """
    Register get_child_pages tool with FastMCP server.

    Args:
        mcp: FastMCP server instance
        client: Initialized ConfluenceClient instance
    """

    @mcp.tool()
    async def get_child_pages(parent_id: str, limit: int = 25) -> list[ChildPageDict]:
        """Get list of child pages for a parent page.

        Confluence pages can be organized in a hierarchical structure.
        This tool retrieves all immediate children of a specified parent page,
        which is useful for:
        - Exploring documentation structure
        - Finding related pages
        - Building a sitemap of content
        - Discovering sub-sections

        Args:
            parent_id: Parent page ID (numeric string)
                       Can be found in the page URL:
                       https://domain.atlassian.net/wiki/spaces/SPACE/pages/{parent_id}/Title
            limit: Maximum number of child pages to return (1-100, default: 25)

        Returns:
            List of child pages, each containing:
            - id: Child page identifier
            - title: Child page title
            - url: Direct link to the child page
            - position: Position in the child page list (if available)

        Examples:
            Get all children of a page:
            get_child_pages("123456")

            Get limited number of children:
            get_child_pages("123456", limit=10)

        Notes:
            - Returns only immediate children (not grandchildren)
            - Pages without children return an empty list
            - Children are typically ordered by position
            - Use search_pages for broader content discovery
        """
        logger.info(f"Fetching child pages for parent ID: {parent_id} (limit={limit})")

        # Validation
        if not parent_id or not parent_id.strip():
            raise ValueError("Parent ID cannot be empty")

        # 子ページを取得
        response = await client.get_child_pages(parent_id=parent_id, limit=limit)

        # 結果をdict形式に変換
        results = [child.model_dump() for child in response.results]

        logger.info(f"Found {len(results)} child pages")
        return results
