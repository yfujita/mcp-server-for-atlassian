"""
Get page content MCP tool implementation.

Implements the get_page_content tool that retrieves full content
of a Confluence page, automatically converting from HTML to Markdown
for better LLM comprehension and token efficiency.
"""

import logging
from typing import TYPE_CHECKING

from src.tools.types import PageContentDict

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from src.confluence.client import ConfluenceClient

logger = logging.getLogger(__name__)


def register_content_tool(mcp: "FastMCP", client: "ConfluenceClient") -> None:
    """
    Register get_page_content tool with FastMCP server.

    Args:
        mcp: FastMCP server instance
        client: Initialized ConfluenceClient instance
    """

    @mcp.tool()
    async def get_page_content(page_id: str, output_format: str = "markdown") -> PageContentDict:
        """Get full content of a Confluence page.

        Retrieves all content and metadata for a specific page.
        By default, HTML content is converted to Markdown for better
        readability and reduced token consumption when used with LLMs.

        Args:
            page_id: Confluence page ID (numeric string)
                     Can be found in the page URL:
                     https://domain.atlassian.net/wiki/spaces/SPACE/pages/{page_id}/Title
            output_format: Content format to return: "markdown" or "html" (default: "markdown")
                          - markdown: Converted from HTML, easier to read, fewer tokens
                          - html: Original HTML storage format

        Returns:
            Dictionary containing:
            - id: Page identifier
            - title: Page title
            - content: Page content in requested format
            - content_format: Format of the content ("markdown" or "html")
            - url: Direct link to the page
            - space_key: Space where the page is located
            - version: Current version number
            - last_modified: Last modification timestamp
            - author: Last author's display name

        Examples:
            Get page content in Markdown:
            get_page_content("123456")

            Get original HTML content:
            get_page_content("123456", output_format="html")

        Notes:
            - Markdown conversion removes some Confluence-specific macros
            - Large pages may take longer to convert
            - The page_id is visible in the page URL
        """
        logger.info(f"Fetching content for page ID: {page_id} (format={output_format})")

        # Validation
        if not page_id or not page_id.strip():
            raise ValueError("Page ID cannot be empty")

        if output_format not in ("markdown", "html"):
            raise ValueError("output_format must be 'markdown' or 'html'")

        # Markdown変換を実行するかどうかを判定
        as_markdown = output_format.lower() == "markdown"

        # ページコンテンツを取得
        page_content = await client.get_page_content(page_id=page_id, as_markdown=as_markdown)

        # dictに変換して返す
        result = page_content.model_dump()

        logger.info(
            f"Retrieved page '{page_content.title}' "
            f"(version={page_content.version}, format={page_content.content_format})"
        )
        return result
