# Confluence Cloud REST API (Cloud版)

## 概要

Confluence Cloud REST APIは、Confluenceのコンテンツやメタデータにプログラマティックにアクセスするための標準的なインターフェースです。現在、v1とv2の2つのバージョンが提供されていますが、v2が最新の推奨APIです。

- **Base URL**: `https://<your-domain>.atlassian.net/wiki/rest/api/` (v1)
- **Base URL**: `https://<your-domain>.atlassian.net/wiki/api/v2/` (v2)

## 認証方法

### API Token (Basic Auth)

Confluence Cloud REST APIは、Basic認証をサポートしており、ユーザーのメールアドレスとAPI Tokenを使用します。

#### API Tokenの作成

1. Atlassianアカウント設定でAPI Tokenを作成
2. トークンに名前と目的を設定
3. 有効期限を設定（1〜365日）
4. スコープを選択（Jira/Confluenceでできること）
5. トークンをコピーして安全に保管

#### 認証の実装方法

**cURLの例:**
```bash
curl -D- \
  -u your_email@domain.com:your_api_token \
  -X GET \
  -H "Content-Type: application/json" \
  https://your-domain.atlassian.net/wiki/rest/api/space
```

**Pythonの例 (httpx使用):**
```python
import httpx
from base64 import b64encode

email = "your_email@domain.com"
api_token = "your_api_token"

# Basic認証ヘッダーの作成
credentials = f"{email}:{api_token}".encode()
auth_header = b64encode(credentials).decode()

headers = {
    "Authorization": f"Basic {auth_header}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# または、httpxのauth引数を使用
async with httpx.AsyncClient() as client:
    response = await client.get(
        "https://your-domain.atlassian.net/wiki/rest/api/space",
        auth=(email, api_token)
    )
```

**重要な注意事項:**
- パスワードによるBasic認証は非推奨になっています
- API Tokenを使用することが推奨されています
- トークンは定期的にローテーションすることをお勧めします

## ページ検索API (CQL使用)

### エンドポイント

**v1:**
```
GET /wiki/rest/api/content/search
```

**v2:**
```
GET /wiki/api/v2/pages
```

### CQLによる検索

Confluence Query Language (CQL) を使用してページを検索します。

**基本的な検索例:**
```bash
GET /wiki/rest/api/content/search?cql=type=page&limit=25
```

**タイトルで検索:**
```bash
GET /wiki/rest/api/content/search?cql=title~Data
```

**スペースとタイプで絞り込み:**
```bash
GET /wiki/rest/api/content/search?cql=space=MARKETING AND type=page
```

**Pythonでの実装例:**
```python
import httpx
from urllib.parse import quote

async def search_pages(
    base_url: str,
    email: str,
    api_token: str,
    cql_query: str,
    limit: int = 25
) -> dict:
    """CQLクエリでページを検索"""
    encoded_cql = quote(cql_query)
    url = f"{base_url}/rest/api/content/search"
    
    params = {
        "cql": cql_query,
        "limit": limit
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            auth=(email, api_token)
        )
        response.raise_for_status()
        return response.json()

# 使用例
results = await search_pages(
    "https://your-domain.atlassian.net/wiki",
    "email@example.com",
    "api_token",
    "type=page AND space=DOCS"
)
```

### ページネーション

検索結果には`next`と`prev`のURLが含まれており、カーソルベースのページネーションを使用します。

**レスポンス例:**
```json
{
  "results": [...],
  "limit": 25,
  "size": 25,
  "_links": {
    "next": "/wiki/rest/api/content/search?cql=type=page&cursor=...",
    "prev": "/wiki/rest/api/content/search?cql=type=page&cursor=..."
  }
}
```

### 検索結果の制限

- `body`拡張を指定した場合: 最大50件
- 拡張なしの場合: 最大1000件
- `body`以外の拡張を指定した場合: 最大200件

## ページコンテンツ取得API

### エンドポイント

**v1:**
```
GET /wiki/rest/api/content/{id}
```

**v2:**
```
GET /wiki/api/v2/pages/{id}
```

### ページ本文の取得

ページの本文をストレージフォーマット（HTML）で取得します。

**v2の例:**
```bash
GET /wiki/api/v2/pages/{page_id}?body-format=storage
```

**cURLの例:**
```bash
curl --request GET \
  --url 'https://your-domain.atlassian.net/wiki/api/v2/pages/12345?body-format=storage' \
  --user 'email@example.com:api_token' \
  --header 'Accept: application/json'
```

**Pythonでの実装例:**
```python
async def get_page_content(
    base_url: str,
    email: str,
    api_token: str,
    page_id: str,
    body_format: str = "storage"
) -> dict:
    """ページIDからコンテンツを取得"""
    url = f"{base_url}/api/v2/pages/{page_id}"
    
    params = {"body-format": body_format}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            auth=(email, api_token)
        )
        response.raise_for_status()
        return response.json()

# 使用例
page_data = await get_page_content(
    "https://your-domain.atlassian.net/wiki",
    "email@example.com",
    "api_token",
    "12345"
)

# ストレージフォーマット（HTML）の取得
html_content = page_data.get("body", {}).get("storage", {}).get("value", "")
```

### v1のexpandパラメータ

v1では`expand`パラメータを使用してコンテンツを取得します。

```bash
GET /wiki/rest/api/content/{id}?expand=body.storage,version,space
```

**レスポンス例:**
```json
{
  "id": "12345",
  "type": "page",
  "title": "Sample Page",
  "space": {
    "key": "DOCS",
    "name": "Documentation"
  },
  "body": {
    "storage": {
      "value": "<p>Page content in HTML format</p>",
      "representation": "storage"
    }
  },
  "version": {
    "number": 3
  }
}
```

## 子ページ取得API

### エンドポイント

**v1:**
```
GET /wiki/rest/api/content/{id}/child/page
```

**v2での代替方法:**
```
GET /wiki/api/v2/pages?parent-id={id}
```

### 子ページのリスト取得

**v1の例:**
```bash
GET /wiki/rest/api/content/{page_id}/child/page?expand=page
```

**Pythonでの実装例:**
```python
async def get_child_pages(
    base_url: str,
    email: str,
    api_token: str,
    parent_id: str,
    limit: int = 25
) -> dict:
    """親ページIDから子ページを取得"""
    url = f"{base_url}/rest/api/content/{parent_id}/child/page"
    
    params = {
        "expand": "page",
        "limit": limit
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            auth=(email, api_token)
        )
        response.raise_for_status()
        return response.json()

# 使用例
children = await get_child_pages(
    "https://your-domain.atlassian.net/wiki",
    "email@example.com",
    "api_token",
    "12345"
)

for child in children.get("results", []):
    print(f"Child page: {child['title']} (ID: {child['id']})")
```

### 子孫ページの取得

すべてのレベルの子ページを取得する場合は、descendantsエンドポイントを使用します。

```bash
GET /wiki/rest/api/content/{id}/descendant/page
```

**レスポンス例:**
```json
{
  "results": [
    {
      "id": "67890",
      "type": "page",
      "title": "Child Page 1"
    },
    {
      "id": "67891",
      "type": "page",
      "title": "Grandchild Page"
    }
  ],
  "limit": 25,
  "size": 2
}
```

## HTML→Markdown変換

Confluenceのストレージフォーマット（HTML）をMarkdownに変換するには、`markdownify`ライブラリを使用します。

**インストール:**
```bash
pip install markdownify
```

**Pythonでの実装例:**
```python
from markdownify import markdownify as md

def convert_to_markdown(html_content: str) -> str:
    """ConfluenceのHTMLをMarkdownに変換"""
    return md(
        html_content,
        heading_style="ATX",  # # スタイルの見出し
        bullets="-",          # - スタイルのリスト
        strip=["script", "style"]  # 不要なタグを除去
    )

# 使用例
page_data = await get_page_content(
    "https://your-domain.atlassian.net/wiki",
    "email@example.com",
    "api_token",
    "12345"
)

html_content = page_data.get("body", {}).get("storage", {}).get("value", "")
markdown_content = convert_to_markdown(html_content)
print(markdown_content)
```

## 完全な実装例

```python
import httpx
from markdownify import markdownify as md
from typing import Optional, List, Dict
from urllib.parse import quote

class ConfluenceClient:
    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth = (email, api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def search_pages(
        self,
        cql_query: str,
        limit: int = 25,
        cursor: Optional[str] = None
    ) -> Dict:
        """CQLクエリでページを検索"""
        url = f"{self.base_url}/rest/api/content/search"
        params = {"cql": cql_query, "limit": limit}
        if cursor:
            params["cursor"] = cursor
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_page_content(
        self,
        page_id: str,
        as_markdown: bool = True
    ) -> Dict:
        """ページコンテンツを取得（Markdownに変換可能）"""
        url = f"{self.base_url}/api/v2/pages/{page_id}"
        params = {"body-format": "storage"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
        
        if as_markdown:
            html_content = data.get("body", {}).get("storage", {}).get("value", "")
            data["markdown"] = md(html_content, heading_style="ATX", bullets="-")
        
        return data
    
    async def get_child_pages(
        self,
        parent_id: str,
        limit: int = 25
    ) -> List[Dict]:
        """子ページのリストを取得"""
        url = f"{self.base_url}/rest/api/content/{parent_id}/child/page"
        params = {"expand": "page", "limit": limit}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
        
        return data.get("results", [])

# 使用例
async def main():
    client = ConfluenceClient(
        "https://your-domain.atlassian.net/wiki",
        "email@example.com",
        "your_api_token"
    )
    
    # ページ検索
    results = await client.search_pages("type=page AND space=DOCS")
    
    # ページコンテンツ取得
    page = await client.get_page_content("12345", as_markdown=True)
    print(page["markdown"])
    
    # 子ページ取得
    children = await client.get_child_pages("12345")
    for child in children:
        print(f"- {child['title']}")
```

## エラーハンドリング

```python
import httpx

async def safe_api_call():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=auth)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print("認証エラー: API Tokenが無効です")
        elif e.response.status_code == 404:
            print("ページが見つかりません")
        elif e.response.status_code == 429:
            print("レート制限に達しました")
        raise
    except httpx.RequestError as e:
        print(f"ネットワークエラー: {e}")
        raise
```

## レート制限

Atlassian Cloud APIにはレート制限があります。429エラーが返された場合は、`Retry-After`ヘッダーを確認して待機してください。

## 参考リンク

- [Basic auth for REST APIs - Confluence Cloud](https://developer.atlassian.com/cloud/confluence/basic-auth-for-rest-apis/)
- [Confluence Cloud REST API v2](https://developer.atlassian.com/cloud/confluence/rest/v2/intro/)
- [The Confluence Cloud REST API v2 - Page API](https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/)
- [Search API - Confluence Cloud](https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-search/)
- [Advanced searching using CQL](https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/)
- [Manage API tokens](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)
- [How to get page content or child list via REST API](https://support.atlassian.com/confluence/kb/how-to-get-page-content-or-child-list-via-rest-api/)
