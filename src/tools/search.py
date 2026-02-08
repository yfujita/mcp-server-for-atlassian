"""
Search pages MCP tool implementation.

Implements the search_pages tool that allows AI agents to search
Confluence pages using CQL (Confluence Query Language).

CQL Reference: https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/
"""

import logging
from typing import TYPE_CHECKING

from src.tools.types import PageSearchResultDict

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from src.confluence.client import ConfluenceClient

logger = logging.getLogger(__name__)


def register_search_tool(mcp: "FastMCP", client: "ConfluenceClient") -> None:
    """
    Register search_pages tool with FastMCP server.

    Args:
        mcp: FastMCP server instance
        client: Initialized ConfluenceClient instance
    """

    @mcp.tool()
    async def search_pages(cql_query: str, limit: int = 25) -> list[PageSearchResultDict]:
        """Search Confluence pages using CQL (Confluence Query Language).

        This tool enables AI agents to search for relevant Confluence pages
        using powerful CQL queries. CQL supports searching by:
        - Text content (text ~ "keyword")
        - Page type (type = page)
        - Space (space = SPACEKEY)
        - Labels (label = "documentation")
        - Creator/contributor (creator = "john.doe")
        - Date ranges (created >= "2024-01-01")

        Args:
            cql_query: CQL query string
                       Examples:
                       - "type=page AND text~'documentation'"
                       - "space=DEV AND label=api"
                       - "title~'getting started'"
            limit: Maximum number of results to return (1-100, default: 25)

        Returns:
            List of page results, each containing:
            - id: Page identifier
            - title: Page title
            - url: Direct link to the page
            - space_key: Space where the page is located
            - excerpt: Search result snippet (if available)

        Examples:
            Search for pages about API documentation:
            search_pages("text ~ 'API documentation'", limit=5)

            Search in a specific space:
            search_pages("space = DEV AND type = page")

        CQL Tips:
            - Use ~ for fuzzy text matching: text ~ "keyword"
            - Use = for exact matching: space = SPACEKEY
            - Combine with AND, OR: space = DEV AND label = api
            - Use wildcards: title ~ "api*"
        """
        logger.info(f"Searching pages with CQL: {cql_query} (limit={limit})")

        # Validation: limit範囲のチェック（ConfluenceClientでも実施されるが、早期チェック）
        if not cql_query or not cql_query.strip():
            raise ValueError("CQL query cannot be empty")

        # 検索実行
        response = await client.search_pages(cql_query=cql_query, limit=limit)

        # 結果をdict形式に変換
        results = [result.model_dump() for result in response.results]

        logger.info(f"Found {len(results)} pages")
        return results
