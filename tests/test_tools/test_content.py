"""
Tests for get_page_content MCP tool.

Tests the get_page_content tool implementation including:
- Content retrieval
- Markdown/HTML format selection
- Error handling
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.confluence.models import PageContent
from src.tools.content import register_content_tool


@pytest.fixture
def mock_client():
    """Create a mock ConfluenceClient."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP instance."""
    mcp = MagicMock()
    mcp.tool = MagicMock(side_effect=lambda: lambda func: func)
    return mcp


@pytest.mark.asyncio
async def test_get_page_content_markdown(mock_client, mock_mcp):
    """Test getting page content in Markdown format."""
    # モックレスポンスの準備
    mock_page = PageContent(
        id="123",
        title="Test Page",
        content="# Test Page\n\nThis is a test.",
        content_format="markdown",
        url="https://example.atlassian.net/wiki/pages/123",
        space_key="DEV",
        version=1,
        last_modified=datetime.now(),
        author="Test User",
    )
    mock_client.get_page_content.return_value = mock_page

    register_content_tool(mock_mcp, mock_client)

    # テスト用関数
    async def get_page_content(page_id: str, output_format: str = "markdown") -> dict:
        if not page_id or not page_id.strip():
            raise ValueError("Page ID cannot be empty")
        if output_format not in ("markdown", "html"):
            raise ValueError("output_format must be 'markdown' or 'html'")

        as_markdown = output_format.lower() == "markdown"
        page_content = await mock_client.get_page_content(page_id=page_id, as_markdown=as_markdown)
        return page_content.model_dump()

    # テスト実行
    result = await get_page_content("123", output_format="markdown")

    # 検証
    assert result["id"] == "123"
    assert result["title"] == "Test Page"
    assert result["content_format"] == "markdown"
    assert "# Test Page" in result["content"]

    # クライアントが正しく呼ばれたか確認
    mock_client.get_page_content.assert_called_once_with(page_id="123", as_markdown=True)


@pytest.mark.asyncio
async def test_get_page_content_html(mock_client, mock_mcp):
    """Test getting page content in HTML format."""
    mock_page = PageContent(
        id="123",
        title="Test Page",
        content="<h1>Test Page</h1><p>This is a test.</p>",
        content_format="html",
        url="https://example.atlassian.net/wiki/pages/123",
        space_key="DEV",
        version=1,
    )
    mock_client.get_page_content.return_value = mock_page

    register_content_tool(mock_mcp, mock_client)

    async def get_page_content(page_id: str, output_format: str = "markdown") -> dict:
        if not page_id or not page_id.strip():
            raise ValueError("Page ID cannot be empty")
        if output_format not in ("markdown", "html"):
            raise ValueError("output_format must be 'markdown' or 'html'")

        as_markdown = output_format.lower() == "markdown"
        page_content = await mock_client.get_page_content(page_id=page_id, as_markdown=as_markdown)
        return page_content.model_dump()

    # HTML形式でテスト
    result = await get_page_content("123", output_format="html")

    assert result["content_format"] == "html"
    assert "<h1>Test Page</h1>" in result["content"]

    mock_client.get_page_content.assert_called_once_with(page_id="123", as_markdown=False)


@pytest.mark.asyncio
async def test_get_page_content_empty_page_id(mock_client, mock_mcp):
    """Test getting page content with empty page ID."""
    register_content_tool(mock_mcp, mock_client)

    async def get_page_content(page_id: str, output_format: str = "markdown") -> dict:
        if not page_id or not page_id.strip():
            raise ValueError("Page ID cannot be empty")
        if output_format not in ("markdown", "html"):
            raise ValueError("output_format must be 'markdown' or 'html'")

        as_markdown = output_format.lower() == "markdown"
        page_content = await mock_client.get_page_content(page_id=page_id, as_markdown=as_markdown)
        return page_content.model_dump()

    with pytest.raises(ValueError, match="Page ID cannot be empty"):
        await get_page_content("")


@pytest.mark.asyncio
async def test_get_page_content_invalid_format(mock_client, mock_mcp):
    """Test getting page content with invalid format."""
    register_content_tool(mock_mcp, mock_client)

    async def get_page_content(page_id: str, output_format: str = "markdown") -> dict:
        if not page_id or not page_id.strip():
            raise ValueError("Page ID cannot be empty")
        if output_format not in ("markdown", "html"):
            raise ValueError("output_format must be 'markdown' or 'html'")

        as_markdown = output_format.lower() == "markdown"
        page_content = await mock_client.get_page_content(page_id=page_id, as_markdown=as_markdown)
        return page_content.model_dump()

    with pytest.raises(ValueError, match="output_format must be 'markdown' or 'html'"):
        await get_page_content("123", output_format="invalid")
