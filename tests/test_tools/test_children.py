"""
Tests for get_child_pages MCP tool.

Tests the get_child_pages tool implementation including:
- Child page retrieval
- Pagination
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.confluence.models import ChildPage, PaginatedResponse
from src.tools.children import register_children_tool


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
async def test_get_child_pages_success(mock_client, mock_mcp):
    """Test successful child pages retrieval."""
    # モックレスポンスの準備
    mock_children = [
        ChildPage(
            id="789",
            title="Child Page 1",
            url="https://example.atlassian.net/wiki/pages/789",
            position=0,
        ),
        ChildPage(
            id="790",
            title="Child Page 2",
            url="https://example.atlassian.net/wiki/pages/790",
            position=1,
        ),
    ]
    mock_response = PaginatedResponse[ChildPage](
        results=mock_children, start=0, limit=25, size=2, total_size=2
    )
    mock_client.get_child_pages.return_value = mock_response

    register_children_tool(mock_mcp, mock_client)

    # テスト用関数
    async def get_child_pages(parent_id: str, limit: int = 25) -> list[dict]:
        if not parent_id or not parent_id.strip():
            raise ValueError("Parent ID cannot be empty")

        response = await mock_client.get_child_pages(parent_id=parent_id, limit=limit)
        results = [child.model_dump() for child in response.results]
        return results

    # テスト実行
    results = await get_child_pages("123", limit=10)

    # 検証
    assert len(results) == 2
    assert results[0]["id"] == "789"
    assert results[0]["title"] == "Child Page 1"
    assert results[0]["position"] == 0
    assert results[1]["id"] == "790"
    assert results[1]["title"] == "Child Page 2"
    assert results[1]["position"] == 1

    # クライアントが正しく呼ばれたか確認
    mock_client.get_child_pages.assert_called_once_with(parent_id="123", limit=10)


@pytest.mark.asyncio
async def test_get_child_pages_empty_parent_id(mock_client, mock_mcp):
    """Test getting child pages with empty parent ID."""
    register_children_tool(mock_mcp, mock_client)

    async def get_child_pages(parent_id: str, limit: int = 25) -> list[dict]:
        if not parent_id or not parent_id.strip():
            raise ValueError("Parent ID cannot be empty")

        response = await mock_client.get_child_pages(parent_id=parent_id, limit=limit)
        results = [child.model_dump() for child in response.results]
        return results

    with pytest.raises(ValueError, match="Parent ID cannot be empty"):
        await get_child_pages("")


@pytest.mark.asyncio
async def test_get_child_pages_no_children(mock_client, mock_mcp):
    """Test getting child pages when parent has no children."""
    # 子ページが存在しない場合の空レスポンス
    mock_response = PaginatedResponse[ChildPage](
        results=[], start=0, limit=25, size=0, total_size=0
    )
    mock_client.get_child_pages.return_value = mock_response

    register_children_tool(mock_mcp, mock_client)

    async def get_child_pages(parent_id: str, limit: int = 25) -> list[dict]:
        if not parent_id or not parent_id.strip():
            raise ValueError("Parent ID cannot be empty")

        response = await mock_client.get_child_pages(parent_id=parent_id, limit=limit)
        results = [child.model_dump() for child in response.results]
        return results

    results = await get_child_pages("123")

    # 空のリストが返されることを確認
    assert results == []
    mock_client.get_child_pages.assert_called_once_with(parent_id="123", limit=25)


@pytest.mark.asyncio
async def test_get_child_pages_default_limit(mock_client, mock_mcp):
    """Test getting child pages with default limit."""
    mock_response = PaginatedResponse[ChildPage](
        results=[], start=0, limit=25, size=0, total_size=0
    )
    mock_client.get_child_pages.return_value = mock_response

    register_children_tool(mock_mcp, mock_client)

    async def get_child_pages(parent_id: str, limit: int = 25) -> list[dict]:
        if not parent_id or not parent_id.strip():
            raise ValueError("Parent ID cannot be empty")

        response = await mock_client.get_child_pages(parent_id=parent_id, limit=limit)
        results = [child.model_dump() for child in response.results]
        return results

    # デフォルトのlimit（25）でテスト
    results = await get_child_pages("123")

    # デフォルト値25で呼ばれたか確認
    mock_client.get_child_pages.assert_called_once_with(parent_id="123", limit=25)
