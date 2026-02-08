# Atlassian OAuth 2.0 (3LO) - Three-Legged OAuth

## 概要

OAuth 2.0 (3LO)、別名「Three-Legged OAuth」または「Authorization Code Grants」は、外部アプリケーションやサービスがユーザーの代わりにAtlassian製品のAPIにアクセスすることを可能にする認証・認可フローです。

**3LO (Three-Legged OAuth) の意味:**
- **1st Leg**: ユーザー
- **2nd Leg**: クライアントアプリケーション
- **3rd Leg**: Atlassian (認可サーバー)

## サポート状況

- **対応製品**: Confluence Cloud, Jira Cloud, Jira Service Desk, Bitbucket Cloud
- **サポートフロー**: Authorization Code Grant Flow のみ
- **非サポート**: Implicit Grant Flow（モバイルアプリやJavaScriptアプリでの使用に制約あり）

## OAuth 2.0フローの概要

```
┌────────┐                                           ┌─────────────┐
│        │                                           │             │
│  User  │                                           │  Atlassian  │
│        │                                           │   (OAuth    │
└────┬───┘                                           │   Server)   │
     │                                               └──────┬──────┘
     │                                                      │
     │  1. アプリケーションにアクセス                           │
     │ ──────────────────────────────────────►              │
     │                                               ┌──────┴──────┐
     │  2. 認可URLにリダイレクト                       │             │
     │ ◄──────────────────────────────────────        │   Client    │
     │                                               │   App       │
     │  3. Atlassianログイン & 権限承認                 │             │
     │ ──────────────────────────────────────►        └──────┬──────┘
     │                                                      │
     │  4. Authorization Codeとともにリダイレクト               │
     │ ◄────────────────────────────────────────────────────┤
     │                                                      │
     │  5. アプリがAuthorization CodeをAccess Tokenと交換     │
     │    ─────────────────────────────────────────────────►│
     │                                                      │
     │  6. Access Token & Refresh Tokenを返す               │
     │    ◄─────────────────────────────────────────────────┤
     │                                                      │
     │  7. Access TokenでAPIにアクセス                       │
     │    ─────────────────────────────────────────────────►│
     │                                                      │
```

## Authorization Code Grant Flow

### ステップ 1: 認可URLの生成

ユーザーをAtlassianの認可エンドポイントにリダイレクトします。

**エンドポイント:**
```
https://auth.atlassian.com/authorize
```

**必須パラメータ:**
- `audience`: `api.atlassian.com`
- `client_id`: アプリのClient ID
- `scope`: 要求する権限のスペース区切りリスト
- `redirect_uri`: コールバックURL
- `response_type`: `code` (固定)
- `prompt`: `consent` (推奨)

**オプションパラメータ:**
- `state`: CSRF保護用のランダムな文字列

**例:**
```python
from urllib.parse import urlencode

def generate_authorization_url(
    client_id: str,
    redirect_uri: str,
    scopes: list[str],
    state: str
) -> str:
    """OAuth認可URLを生成"""
    params = {
        "audience": "api.atlassian.com",
        "client_id": client_id,
        "scope": " ".join(scopes),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "prompt": "consent",
        "state": state
    }
    base_url = "https://auth.atlassian.com/authorize"
    return f"{base_url}?{urlencode(params)}"

# 使用例
auth_url = generate_authorization_url(
    client_id="your_client_id",
    redirect_uri="https://yourapp.com/callback",
    scopes=["read:confluence-content.all", "read:confluence-space.summary"],
    state="random_state_string_123"
)
print(f"ユーザーをこのURLにリダイレクト: {auth_url}")
```

### ステップ 2: ユーザーの認証と承認

ユーザーは、Atlassianのログインページで認証し、アプリが要求する権限を承認します。

### ステップ 3: Authorization Codeの取得

ユーザーが承認すると、Atlassianは`redirect_uri`にリダイレクトし、クエリパラメータに`code`を含めます。

**コールバックURLの例:**
```
https://yourapp.com/callback?code=AUTH_CODE_HERE&state=random_state_string_123
```

### ステップ 4: Access Tokenの取得

Authorization CodeをAccess TokenとRefresh Tokenに交換します。

**エンドポイント:**
```
POST https://auth.atlassian.com/oauth/token
```

**リクエスト:**
```python
import httpx
import json

async def exchange_code_for_token(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str
) -> dict:
    """Authorization CodeをAccess Tokenに交換"""
    url = "https://auth.atlassian.com/oauth/token"
    
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

# 使用例
token_data = await exchange_code_for_token(
    code="AUTH_CODE_FROM_CALLBACK",
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="https://yourapp.com/callback"
)

# レスポンス例
# {
#   "access_token": "eyJhbG...",
#   "expires_in": 3600,
#   "token_type": "Bearer",
#   "refresh_token": "eyJhbG...",
#   "scope": "read:confluence-content.all read:confluence-space.summary"
# }
```

### ステップ 5: Access Tokenの使用

Access TokenをBearerトークンとして使用してAPIにアクセスします。

```python
async def get_accessible_resources(access_token: str) -> list:
    """アクセス可能なAtlassianリソース（サイト）を取得"""
    url = "https://api.atlassian.com/oauth/token/accessible-resources"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

# レスポンス例
# [
#   {
#     "id": "cloud-id-123",
#     "url": "https://your-domain.atlassian.net",
#     "name": "Your Site Name",
#     "scopes": ["read:confluence-content.all"],
#     "avatarUrl": "https://..."
#   }
# ]

async def get_confluence_page(
    access_token: str,
    cloud_id: str,
    page_id: str
) -> dict:
    """OAuth 2.0でConfluenceページを取得"""
    url = f"https://api.atlassian.com/ex/confluence/{cloud_id}/rest/api/content/{page_id}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    params = {"expand": "body.storage"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
```

### ステップ 6: Refresh Tokenの使用

Access Tokenが期限切れになったら、Refresh Tokenを使用して新しいAccess Tokenを取得します。

**重要: Rotating Refresh Tokens**
- Atlassianは、セキュリティ向上のため、Rotating Refresh Tokensを実装しています
- Refresh Tokenを使用するたびに、新しいRefresh Tokenが発行されます
- 古いRefresh Tokenは無効になります

```python
async def refresh_access_token(
    refresh_token: str,
    client_id: str,
    client_secret: str
) -> dict:
    """Refresh Tokenを使用して新しいAccess Tokenを取得"""
    url = "https://auth.atlassian.com/oauth/token"
    
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

# レスポンス例
# {
#   "access_token": "new_access_token",
#   "expires_in": 3600,
#   "token_type": "Bearer",
#   "refresh_token": "new_refresh_token",  # 新しいRefresh Token
#   "scope": "..."
# }
```

## Confluenceのスコープ

OAuth 2.0 (3LO) アプリでConfluenceにアクセスするために必要なスコープの例:

### 読み取りスコープ

- `read:confluence-content.all`: すべてのConfluenceコンテンツを読み取る
- `read:confluence-content.summary`: コンテンツのサマリー情報を読み取る
- `read:confluence-space.summary`: スペースのサマリー情報を読み取る
- `read:confluence-user`: ユーザー情報を読み取る

### 書き込みスコープ

- `write:confluence-content`: Confluenceコンテンツを作成・更新する
- `write:confluence-space`: スペースを作成・更新する

### その他のスコープ

- `search:confluence`: Confluenceを検索する
- `read:confluence-props`: プロパティを読み取る
- `write:confluence-props`: プロパティを書き込む

**参考**: [Confluence scopes for OAuth 2.0 (3LO)](https://developer.atlassian.com/cloud/confluence/scopes-for-oauth-2-3LO-and-forge-apps/)

## 完全な実装例

```python
import httpx
from typing import Optional, Dict
from urllib.parse import urlencode
import secrets

class AtlassianOAuthClient:
    """Atlassian OAuth 2.0 (3LO) クライアント"""
    
    AUTH_URL = "https://auth.atlassian.com/authorize"
    TOKEN_URL = "https://auth.atlassian.com/oauth/token"
    RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    def generate_authorization_url(self, scopes: list[str]) -> tuple[str, str]:
        """認可URLとstateを生成"""
        state = secrets.token_urlsafe(32)
        
        params = {
            "audience": "api.atlassian.com",
            "client_id": self.client_id,
            "scope": " ".join(scopes),
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "prompt": "consent",
            "state": state
        }
        
        auth_url = f"{self.AUTH_URL}?{urlencode(params)}"
        return auth_url, state
    
    async def exchange_code(self, code: str) -> Dict:
        """Authorization CodeをAccess Tokenに交換"""
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                json=data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
    
    async def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh Tokenで新しいAccess Tokenを取得"""
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                json=data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_accessible_resources(self, access_token: str) -> list:
        """アクセス可能なリソースを取得"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.RESOURCES_URL, headers=headers)
            response.raise_for_status()
            return response.json()

class ConfluenceOAuthAPI:
    """OAuth 2.0認証を使用したConfluence API"""
    
    def __init__(self, access_token: str, cloud_id: str):
        self.access_token = access_token
        self.cloud_id = cloud_id
        self.base_url = f"https://api.atlassian.com/ex/confluence/{cloud_id}"
    
    def _get_headers(self) -> Dict:
        """認証ヘッダーを取得"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def search_content(self, cql: str, limit: int = 25) -> Dict:
        """CQLでコンテンツを検索"""
        url = f"{self.base_url}/rest/api/content/search"
        params = {"cql": cql, "limit": limit}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def get_page(self, page_id: str) -> Dict:
        """ページを取得"""
        url = f"{self.base_url}/rest/api/content/{page_id}"
        params = {"expand": "body.storage,version,space"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

# 使用例
async def main():
    # OAuth クライアントの初期化
    oauth_client = AtlassianOAuthClient(
        client_id="your_client_id",
        client_secret="your_client_secret",
        redirect_uri="https://yourapp.com/callback"
    )
    
    # 認可URLの生成
    scopes = [
        "read:confluence-content.all",
        "read:confluence-space.summary",
        "search:confluence"
    ]
    auth_url, state = oauth_client.generate_authorization_url(scopes)
    print(f"認可URL: {auth_url}")
    
    # ユーザーが承認後、コールバックでcodeを取得
    # code = "AUTHORIZATION_CODE_FROM_CALLBACK"
    
    # Access Tokenの取得
    # token_data = await oauth_client.exchange_code(code)
    # access_token = token_data["access_token"]
    # refresh_token = token_data["refresh_token"]
    
    # アクセス可能なリソースの取得
    # resources = await oauth_client.get_accessible_resources(access_token)
    # cloud_id = resources[0]["id"]
    
    # Confluence APIの使用
    # confluence = ConfluenceOAuthAPI(access_token, cloud_id)
    # results = await confluence.search_content("type=page AND space=DOCS")
```

## トークンの保存とセキュリティ

### トークンの安全な保存

```python
import json
from cryptography.fernet import Fernet

class TokenStorage:
    """トークンの暗号化保存"""
    
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
    
    def save_tokens(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        expires_in: int
    ):
        """トークンを暗号化して保存"""
        data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": time.time() + expires_in
        }
        encrypted = self.cipher.encrypt(json.dumps(data).encode())
        
        # データベースまたはファイルに保存
        # db.save(user_id, encrypted)
    
    def load_tokens(self, user_id: str) -> dict:
        """暗号化されたトークンを読み込み"""
        # encrypted = db.load(user_id)
        decrypted = self.cipher.decrypt(encrypted)
        return json.loads(decrypted)

# 暗号化キーの生成
# key = Fernet.generate_key()
# storage = TokenStorage(key)
```

### セキュリティのベストプラクティス

1. **HTTPS必須**: すべての通信はHTTPSで行う
2. **State パラメータ**: CSRF攻撃を防ぐためにstateパラメータを使用
3. **トークンの暗号化**: データベースに保存する際は暗号化
4. **Refresh Tokenのローテーション**: 新しいRefresh Tokenを取得したら古いものを破棄
5. **スコープの最小化**: 必要最小限のスコープのみを要求
6. **Client Secretの保護**: サーバー側でのみ使用し、クライアント側に公開しない

## Webアプリケーションでの統合例

### Flask/FastAPIでの実装

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx

app = FastAPI()

oauth_client = AtlassianOAuthClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="http://localhost:8000/callback"
)

# セッションストレージ（本番環境では適切なストレージを使用）
sessions = {}

@app.get("/login")
async def login():
    """OAuth認証を開始"""
    scopes = ["read:confluence-content.all", "search:confluence"]
    auth_url, state = oauth_client.generate_authorization_url(scopes)
    
    # stateをセッションに保存（本番環境ではセッション管理を適切に行う）
    sessions["pending_state"] = state
    
    return RedirectResponse(url=auth_url)

@app.get("/callback")
async def callback(request: Request):
    """OAuth コールバック"""
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    
    # stateの検証
    if state != sessions.get("pending_state"):
        raise HTTPException(status_code=400, detail="Invalid state")
    
    # Access Tokenの取得
    token_data = await oauth_client.exchange_code(code)
    
    # トークンを保存
    sessions["access_token"] = token_data["access_token"]
    sessions["refresh_token"] = token_data["refresh_token"]
    
    return {"message": "認証成功", "access_token": token_data["access_token"]}

@app.get("/search")
async def search(query: str):
    """Confluenceを検索"""
    access_token = sessions.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # リソースを取得
    resources = await oauth_client.get_accessible_resources(access_token)
    cloud_id = resources[0]["id"]
    
    # Confluence APIを使用
    confluence = ConfluenceOAuthAPI(access_token, cloud_id)
    results = await confluence.search_content(f"text~'{query}'")
    
    return results
```

## API Token vs OAuth 2.0

| 特徴 | API Token (Basic Auth) | OAuth 2.0 (3LO) |
|-----|----------------------|-----------------|
| 認証方法 | ユーザーのメール + Token | Authorization Code Flow |
| ユーザー体験 | トークンを手動で作成・設定 | Webブラウザで承認 |
| 権限管理 | ユーザーの全権限 | スコープで制限可能 |
| トークン有効期限 | 1〜365日（設定可能） | Access Token: 1時間 |
| セキュリティ | Basic認証ヘッダー | Bearer トークン |
| 用途 | 個人利用、スクリプト | マルチテナントアプリ |
| 実装の複雑さ | シンプル | 複雑 |

**推奨事項:**
- **個人利用やスクリプト**: API Token
- **SaaSアプリケーション**: OAuth 2.0 (3LO)
- **エンタープライズ統合**: 要件に応じて選択

## 参考リンク

- [OAuth 2.0 (3LO) apps - Confluence Cloud](https://developer.atlassian.com/cloud/confluence/oauth-2-3lo-apps/)
- [Implementing OAuth 2.0 (3LO)](https://developer.atlassian.com/cloud/oauth/getting-started/implementing-oauth-3lo/)
- [Confluence scopes for OAuth 2.0 (3LO)](https://developer.atlassian.com/cloud/confluence/scopes-for-oauth-2-3LO-and-forge-apps/)
- [OAuth 2.0 (3LO) apps - Jira Cloud platform](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)
- [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
