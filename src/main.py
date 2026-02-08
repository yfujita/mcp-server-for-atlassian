"""
Main entry point for the MCP server.

This module initializes the FastMCP server, registers tools, and starts
the server with the configured transport layer (stdio, SSE, or streamable HTTP).
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

from fastmcp import FastMCP

from src.auth.api_token import APITokenAuth
from src.confluence.client import ConfluenceClient
from src.config import get_settings
from src.tools.children import register_children_tool
from src.tools.content import register_content_tool
from src.tools.search import register_search_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """
    サーバーのライフサイクル管理.

    起動時:
    - 設定の読み込み
    - 認証戦略の作成
    - ConfluenceClientの初期化
    - ツールの登録

    シャットダウン時:
    - ConfluenceClientのクローズ

    Args:
        server: FastMCPインスタンス

    Yields:
        Dict[str, Any]: ConfluenceClientを含むコンテキスト
    """
    # 起動時の初期化
    logger.info("Initializing MCP server...")

    # 設定の読み込み
    settings = get_settings()
    # センシティブ情報をマスキングしてログ出力（__repr__が使用される）
    logger.info(f"Loaded settings: {settings}")

    # 認証戦略の作成
    auth = APITokenAuth(
        email=settings.atlassian_user_email,
        api_token=settings.atlassian_api_token,
        base_url=settings.atlassian_url,
    )

    # ConfluenceClientの初期化とリソース管理（async withを使用）
    client = ConfluenceClient(base_url=settings.atlassian_url, auth_strategy=auth)

    async with client:
        logger.info("Confluence client initialized successfully")

        # ツールの登録
        register_search_tool(server, client)
        register_content_tool(server, client)
        register_children_tool(server, client)

        logger.info("All tools registered successfully")

        # コンテキストを返す
        yield {"client": client}

    # async withブロックを抜けると自動的にクリーンアップされる
    logger.info("Confluence client closed")
    logger.info("MCP server shutdown complete")


# FastMCPインスタンスの作成（lifespanを渡す）
mcp = FastMCP("confluence-mcp-server", lifespan=lifespan)


def main() -> None:
    """
    Main entry point for the MCP server.

    Initializes the server based on MCP_TRANSPORT environment variable:
    - stdio: For local editor integration (default)
    - sse: For Server-Sent Events (remote)
    - streamable_http: For HTTP streaming (remote)
    """
    logger.info("Starting MCP Server for Atlassian Confluence...")

    # 環境変数からトランスポート設定を取得
    # デフォルトはstdio（ローカルエディタ用）
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    # 設定を読み込み（ホスト・ポート設定のため）
    settings = get_settings()

    logger.info(f"Using transport: {transport}")

    # トランスポートに応じてサーバーを起動
    if transport == "stdio":
        # STDIOトランスポート（ローカルエディタ用）
        mcp.run(transport="stdio")

    elif transport == "sse":
        # SSEトランスポート（Server-Sent Events）
        logger.info(f"Starting SSE server on {settings.mcp_host}:{settings.mcp_port}")
        mcp.run(transport="sse", host=settings.mcp_host, port=settings.mcp_port)

    elif transport == "streamable_http":
        # Streamable HTTPトランスポート（推奨）
        logger.info(
            f"Starting Streamable HTTP server on {settings.mcp_host}:{settings.mcp_port}"
        )
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)

    else:
        raise ValueError(
            f"Unsupported transport: {transport}. "
            f"Supported transports: stdio, sse, streamable_http"
        )


if __name__ == "__main__":
    main()
