# FastMCP

## 概要

FastMCPは、Model Context Protocol (MCP) サーバーとクライアントを構築するための高速でPythonicなライブラリです。MCPは、AIエージェントをツールやデータに接続するための標準化されたプロトコルで、FastMCPはこのプロトコルの実装を簡単にします。

- **GitHub**: [jlowin/fastmcp](https://github.com/jlowin/fastmcp)
- **PyPI**: [fastmcp](https://pypi.org/project/fastmcp/)
- **公式ドキュメント**: [gofastmcp.com](https://gofastmcp.com)

## バージョン情報

- **FastMCP 2.x**: 安定版（本番環境推奨）
- **FastMCP 3.0**: ベータ版（新機能を試す場合）

**インストール:**
```bash
# 安定版 (2.x)
pip install fastmcp

# または、バージョン2を明示的に指定
pip install 'fastmcp<3'

# ベータ版 (3.0)
pip install fastmcp==3.0.0b1
```

## 基本的な使い方

### 最小限のサーバー例

```python
from fastmcp import FastMCP

# MCPサーバーのインスタンスを作成
mcp = FastMCP("my-server")

@mcp.tool
def get_weather(city: str) -> dict:
    """指定された都市の天気を取得します。"""
    weather_data = {
        "new york": {"temp": 72, "condition": "sunny"},
        "london": {"temp": 59, "condition": "cloudy"},
        "tokyo": {"temp": 68, "condition": "rainy"},
    }
    city_lower = city.lower()
    if city_lower in weather_data:
        return {"city": city, **weather_data[city_lower]}
    else:
        return {"city": city, "temp": 70, "condition": "unknown"}

if __name__ == "__main__":
    # STDIOトランスポートで実行
    mcp.run(transport="stdio")
```

### FastMCPの3つの抽象化

FastMCPは、3つの主要な抽象化に基づいています:

1. **Tools (ツール)**: AIアシスタントが実行できるアクション
2. **Resources (リソース)**: データソースへのアクセス
3. **Prompts (プロンプト)**: 再利用可能なプロンプトテンプレート

これらはすべてPython関数として定義され、FastMCPが自動的にスキーマ生成、バリデーション、ドキュメント生成を処理します。

## ツールの定義方法

### 基本的なツール定義

`@mcp.tool`デコレータを使用して、Python関数をMCPツールに変換します。

```python
from fastmcp import FastMCP

mcp = FastMCP("example-server")

@mcp.tool
def add_numbers(a: int, b: int) -> int:
    """2つの数値を加算します。
    
    Args:
        a: 最初の数値
        b: 2番目の数値
    
    Returns:
        2つの数値の合計
    """
    return a + b

@mcp.tool
def search_database(query: str, limit: int = 10) -> list[dict]:
    """データベースを検索します。
    
    Args:
        query: 検索クエリ
        limit: 返す結果の最大数（デフォルト: 10）
    
    Returns:
        検索結果のリスト
    """
    # 検索ロジックの実装
    results = []
    # ... 検索処理 ...
    return results
```

### 型アノテーションの重要性

FastMCPは、Python の型アノテーションを使用して自動的にスキーマを生成します。

```python
from typing import Optional, List, Dict
from pydantic import BaseModel

class SearchResult(BaseModel):
    id: str
    title: str
    score: float

@mcp.tool
def advanced_search(
    query: str,
    filters: Optional[Dict[str, str]] = None,
    max_results: int = 20
) -> List[SearchResult]:
    """高度な検索を実行します。"""
    # 実装
    pass
```

### 非同期ツール

FastMCPは非同期関数もサポートしています。

```python
import httpx

@mcp.tool
async def fetch_data(url: str) -> dict:
    """URLからデータを取得します。"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

## リソースの定義

リソースは、ファイル、データベース、APIなどのデータソースを公開します。

```python
@mcp.resource("config://settings")
def get_settings() -> str:
    """アプリケーション設定を返します。"""
    return """
    {
        "api_key": "***",
        "timeout": 30,
        "retries": 3
    }
    """

@mcp.resource("data://users/{user_id}")
def get_user(user_id: str) -> str:
    """ユーザー情報を取得します。"""
    # データベースからユーザー情報を取得
    user_data = {"id": user_id, "name": "John Doe"}
    return str(user_data)
```

## プロンプトの定義

プロンプトは、再利用可能なプロンプトテンプレートです。

```python
@mcp.prompt
def code_review_prompt(language: str, code: str) -> str:
    """コードレビュー用のプロンプトを生成します。"""
    return f"""
    以下の{language}コードをレビューしてください:
    
    ```{language}
    {code}
    ```
    
    以下の観点でレビューしてください:
    - コードの品質
    - パフォーマンス
    - セキュリティ
    - ベストプラクティス
    """
```

## トランスポート層の設定

FastMCPは、複数のトランスポート方式をサポートしています。

### 1. STDIO トランスポート (デフォルト)

標準入出力を使用した通信。ローカルツールやCLI統合に最適です。

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

# ... ツールの定義 ...

if __name__ == "__main__":
    # STDIOトランスポート（デフォルト）
    mcp.run(transport="stdio")
```

**特徴:**
- ネットワーク設定不要
- 最もシンプルな実装
- ローカル環境に最適
- Claude Desktopなどのクライアントで使用可能

### 2. SSE トランスポート

Server-Sent Eventsを使用したHTTP通信。

```python
if __name__ == "__main__":
    # SSEトランスポート
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=8000
    )
```

**特徴:**
- リアルタイム更新
- Webサービスとの統合が容易
- ファイアウォール越しの通信が可能

### 3. Streamable HTTP トランスポート（推奨）

本番環境向けの効率的なHTTP通信。

```python
if __name__ == "__main__":
    # Streamable HTTPトランスポート（推奨）
    mcp.run(
        transport="streamable_http",
        host="0.0.0.0",
        port=8000,
        stateless_http=True,
        json_response=True
    )
```

**特徴:**
- ステートレスで高スケーラビリティ
- ストリーミング対応
- 本番環境に最適
- ロードバランサーとの親和性が高い

### トランスポートの選択ガイド

| トランスポート | 用途 | メリット | デメリット |
|------------|------|---------|----------|
| STDIO | ローカル開発、CLI | シンプル、設定不要 | ネットワーク経由不可 |
| SSE | リアルタイムアプリ | リアルタイム性 | ステートフル |
| Streamable HTTP | 本番環境 | スケーラブル、高効率 | 設定が必要 |

## Confluence用MCPサーバーの実装例

```python
from fastmcp import FastMCP
import httpx
from markdownify import markdownify as md
from typing import Optional, List, Dict
import os

# FastMCPインスタンスの作成
mcp = FastMCP("confluence-server")

# 環境変数から認証情報を取得
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

@mcp.tool
async def search_pages(
    cql_query: str,
    limit: int = 25
) -> List[Dict]:
    """CQLクエリを使用してConfluenceページを検索します。
    
    Args:
        cql_query: Confluence Query Language (CQL) クエリ
        limit: 返す結果の最大数（デフォルト: 25）
    
    Returns:
        検索結果のページリスト
    
    Examples:
        - search_pages("type=page AND space=DOCS")
        - search_pages("title~'API' AND type=page", limit=10)
    """
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/search"
    params = {"cql": cql_query, "limit": limit}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            auth=(CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN),
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
    
    return data.get("results", [])

@mcp.tool
async def get_page_content(
    page_id: str,
    output_format: str = "markdown"
) -> Dict:
    """ページIDからコンテンツを取得します。
    
    Args:
        page_id: ConfluenceページのID
        output_format: 出力フォーマット（"markdown" または "html"）
    
    Returns:
        ページのタイトル、コンテンツ、メタデータを含む辞書
    """
    url = f"{CONFLUENCE_BASE_URL}/api/v2/pages/{page_id}"
    params = {"body-format": "storage"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            auth=(CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN),
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
    
    html_content = data.get("body", {}).get("storage", {}).get("value", "")
    
    result = {
        "id": data.get("id"),
        "title": data.get("title"),
        "space_id": data.get("spaceId"),
        "version": data.get("version", {}).get("number"),
    }
    
    if output_format == "markdown":
        result["content"] = md(html_content, heading_style="ATX", bullets="-")
        result["format"] = "markdown"
    else:
        result["content"] = html_content
        result["format"] = "html"
    
    return result

@mcp.tool
async def get_child_pages(
    parent_id: str,
    limit: int = 25
) -> List[Dict]:
    """親ページの子ページリストを取得します。
    
    Args:
        parent_id: 親ページのID
        limit: 返す結果の最大数（デフォルト: 25）
    
    Returns:
        子ページのリスト
    """
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{parent_id}/child/page"
    params = {"expand": "page", "limit": limit}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            auth=(CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN),
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
    
    return data.get("results", [])

if __name__ == "__main__":
    # STDIOトランスポートで実行（Claude Desktop用）
    mcp.run(transport="stdio")
    
    # または、HTTPサーバーとして実行
    # mcp.run(
    #     transport="streamable_http",
    #     host="0.0.0.0",
    #     port=8000
    # )
```

## 環境変数の設定

`.env`ファイルを使用して認証情報を管理します。

```bash
# .env
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your_api_token_here
```

```python
from dotenv import load_dotenv
import os

load_dotenv()

CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
```

## エラーハンドリング

```python
from fastmcp import FastMCP
import httpx

mcp = FastMCP("confluence-server")

@mcp.tool
async def safe_search(cql_query: str) -> dict:
    """エラーハンドリング付きの検索"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={"cql": cql_query},
                auth=(email, token),
                timeout=30.0  # タイムアウト設定
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTPエラー: {e.response.status_code}"
        if e.response.status_code == 401:
            error_msg = "認証エラー: API Tokenが無効です"
        elif e.response.status_code == 404:
            error_msg = "リソースが見つかりません"
        return {"success": False, "error": error_msg}
    except httpx.RequestError as e:
        return {"success": False, "error": f"リクエストエラー: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"予期しないエラー: {str(e)}"}
```

## ログ設定

```python
import logging
from fastmcp import FastMCP

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

mcp = FastMCP("confluence-server")

@mcp.tool
async def logged_search(query: str) -> dict:
    """ログ付きの検索"""
    logger.info(f"検索開始: {query}")
    try:
        result = await perform_search(query)
        logger.info(f"検索成功: {len(result)} 件の結果")
        return result
    except Exception as e:
        logger.error(f"検索エラー: {e}")
        raise
```

## Claude Desktopでの使用

Claude Desktopの設定ファイル (`claude_desktop_config.json`) に以下を追加します。

```json
{
  "mcpServers": {
    "confluence": {
      "command": "python",
      "args": ["/path/to/your/confluence_server.py"],
      "env": {
        "CONFLUENCE_BASE_URL": "https://your-domain.atlassian.net/wiki",
        "CONFLUENCE_EMAIL": "your-email@example.com",
        "CONFLUENCE_API_TOKEN": "your_api_token"
      }
    }
  }
}
```

## テスト

```python
import pytest
from fastmcp import FastMCP

@pytest.mark.asyncio
async def test_search_pages():
    mcp = FastMCP("test-server")
    
    # テスト用のモックツール
    @mcp.tool
    async def mock_search(query: str) -> list:
        return [{"id": "123", "title": "Test Page"}]
    
    # ツールの実行をテスト
    result = await mock_search("test")
    assert len(result) == 1
    assert result[0]["title"] == "Test Page"
```

## パフォーマンス最適化

### 接続プーリング

```python
import httpx

# 永続的なクライアントを使用
client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
)

@mcp.tool
async def optimized_search(query: str) -> dict:
    """接続プーリングを使用した最適化された検索"""
    response = await client.get(url, params={"cql": query}, auth=auth)
    return response.json()
```

### キャッシュの実装

```python
from functools import lru_cache
import asyncio

# シンプルなインメモリキャッシュ
cache = {}

@mcp.tool
async def cached_search(query: str, ttl: int = 300) -> dict:
    """キャッシュ付きの検索（TTL: 5分）"""
    cache_key = f"search:{query}"
    
    if cache_key in cache:
        cached_result, timestamp = cache[cache_key]
        if time.time() - timestamp < ttl:
            return cached_result
    
    result = await perform_search(query)
    cache[cache_key] = (result, time.time())
    return result
```

## 参考リンク

- [FastMCP GitHub Repository](https://github.com/jlowin/fastmcp)
- [FastMCP Documentation](https://gofastmcp.com)
- [FastMCP Quickstart](https://gofastmcp.com/getting-started/quickstart)
- [Build MCP Servers in Python with FastMCP - Complete Guide](https://mcpcat.io/guides/building-mcp-server-python-fastmcp/)
- [Building an MCP Server and Client with FastMCP 2.0 | DataCamp](https://www.datacamp.com/tutorial/building-mcp-server-client-fastmcp)
- [How to Build Powerful LLM Tools with FastMCP](https://apidog.com/blog/fastmcp/)
- [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk)
