# MCP Server for Atlassian

Atlassian Confluence (Cloud) のコンテンツに AI エージェントがアクセスして検索できるようにする Model Context Protocol (MCP) サーバーです。

## 概要

この MCP サーバーは Atlassian Confluence とのシームレスな統合を提供し、Claude のような AI アシスタントが Confluence ページを検索、取得、ナビゲートできるようにします。FastMCP で構築されており、ローカルおよびリモート使用の両方で複数のトランスポートプロトコルをサポートしています。

## 機能

このサーバーは3つの主要な MCP ツールを実装しています：

### 1. search_pages
CQL (Confluence Query Language) を使用して Confluence ページを検索します。

**入力:**
- 検索クエリ文字列 (CQL 構文)
- オプションのリミット (デフォルト: 10)

**出力:**
- タイトル、ID、URL を含む一致したページのリスト

**例:**
```
"API documentation" を含むページを検索
```

### 2. get_page_content
特定の Confluence ページの完全なコンテンツを取得します。

**入力:**
- ページ ID (文字列または整数)

**出力:**
- Markdown 形式のページコンテンツ (HTML から変換済み)
- タイトル、URL、メタデータ

**注意:** コンテンツは、LLM の理解とトークン効率を向上させるために、HTML から Markdown に自動的に変換されます。

### 3. get_child_pages
指定された親ページの子ページのリストを取得します。

**入力:**
- 親ページ ID
- オプションのリミット (デフォルト: 50)

**出力:**
- タイトルと ID を含む子ページのリスト

**例:**
```
ページ ID "123456" のすべての子ページをリスト
```

## 必要条件

- Python 3.10 以上
- Atlassian Confluence Cloud アカウント
- 認証用 API トークン

## インストール

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/mcp-server-for-atlassian.git
cd mcp-server-for-atlassian
```

### 2. 依存関係のインストール

```bash
pip install -e .
```

開発用:
```bash
pip install -e ".[dev]"
```

### 3. 環境変数の設定

サンプルの環境変数ファイルをコピーし、認証情報で編集します：

```bash
cp .env.example .env
```

`.env` を編集し、以下の変数を設定します：

```bash
ATLASSIAN_URL=https://your-domain.atlassian.net/wiki
ATLASSIAN_USER_EMAIL=your-email@example.com
ATLASSIAN_API_TOKEN=your_api_token_here
```

#### API トークンの取得方法

1. https://id.atlassian.com/manage-profile/security/api-tokens にアクセス
2. "Create API token" をクリック
3. ラベルを付ける (例: "MCP Server")
4. 生成されたトークンをコピーして `.env` ファイルに貼り付け

## 使用方法

### ローカルでの使用 (stdio トランスポート)

Cursor や VS Code のようなローカル AI エディタで使用する場合：

```bash
confluence-mcp
```

### リモートでの使用 (SSE または HTTP トランスポート)

Docker やリモート接続の場合：

```bash
# .env でトランスポートモードを設定
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8000

# サーバーを実行
confluence-mcp
```

### Docker での使用 (本番環境に推奨)

本番環境でサーバーを実行する最も簡単な方法は Docker を使用することです：

```bash
# docker-compose でクイックスタート
docker-compose up -d

# ログの確認
docker-compose logs -f

# サーバーの停止
docker-compose down
```

サーバーは `http://localhost:28000` で利用可能になります。

詳細な Docker デプロイ手順については、[docs/docker.md](docs/docker.md) を参照してください。

### Claude Desktop での設定

Claude Desktop の設定ファイルに追加します：

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "confluence": {
      "command": "confluence-mcp",
      "env": {
        "ATLASSIAN_URL": "https://your-domain.atlassian.net/wiki",
        "ATLASSIAN_USER_EMAIL": "your-email@example.com",
        "ATLASSIAN_API_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

## 環境変数

| 変数 | 説明 | 必須 | デフォルト |
|----------|-------------|----------|---------|
| `ATLASSIAN_URL` | Confluence インスタンスのベース URL | はい | - |
| `ATLASSIAN_USER_EMAIL` | API トークン認証用のメールアドレス | はい | - |
| `ATLASSIAN_API_TOKEN` | Atlassian からの API トークン | はい | - |
| `MCP_TRANSPORT` | トランスポートプロトコル (stdio/sse/streamable_http) | いいえ | stdio |
| `MCP_HOST` | SSE/HTTP トランスポート用のホスト | いいえ | 0.0.0.0 |
| `MCP_PORT` | SSE/HTTP トランスポート用のポート | いいえ | 8000 |

## 開発

### テストの実行

```bash
pytest
```

### コードフォーマット

```bash
black src/ tests/
```

### リント (静的解析)

```bash
ruff check src/ tests/
```

### 型チェック

```bash
mypy src/
```

## アーキテクチャ

サーバーは明確な関心の分離を持つモジュラーアーキテクチャに従っています：

- **Authentication**: プラグ可能な認証戦略 (現在は API トークン、OAuth2 対応準備済み)
- **Confluence Client**: 抽象化された API 通信レイヤー
- **MCP Tools**: 個別のツール実装
- **Data Models**: Pydantic ベースのバリデーションとシリアライゼーション

詳細なアーキテクチャドキュメントについては、`development_plan.md` を参照してください。

## CQL クエリ例

CQL (Confluence Query Language) は Confluence コンテンツを検索するための強力なクエリ構文です。以下は一般的な例です：

### 基本的なクエリ

```cql
# 特定のテキストを含むページを検索
text ~ "API documentation"

# 特定のスペース内を検索
space = DEV AND type = page

# タイトルで検索
title ~ "getting started"

# ラベルで検索
label = "api" AND label = "rest"
```

### 高度なクエリ

```cql
# 最近更新されたページ
lastModified >= now("-7d") AND space = DEV

# 特定の作成者によるページ
creator = "john.doe@example.com" AND space = TEAM

# 複数の条件を組み合わせる
space = DOCS AND label = tutorial AND text ~ "beginner" AND created >= "2024-01-01"
```

その他の例や詳細な CQL 構文については、[docs/examples.md](docs/examples.md) を参照してください。

## トラブルシューティング

### 接続の問題

**問題:** Confluence に接続できない

**解決策:**
- `ATLASSIAN_URL` が正しいか確認してください (`/wiki` を含む必要があります)
- インターネット接続を確認してください
- ファイアウォールが送信 HTTPS 接続をブロックしていないか確認してください

### 認証エラー

**問題:** "Authentication failed: Invalid credentials"

**解決策:**
- `ATLASSIAN_USER_EMAIL` が正しいか確認してください
- API トークンを再生成し、`.env` を更新してください
- API トークンの有効期限が切れていないか確認してください

### ページが見つからない

**問題:** コンテンツ取得時の "Page not found" エラー

**解決策:**
- ページ ID が正しいか確認してください
- ページを表示する権限があるか確認してください
- ページが削除または移動されていないか確認してください

### 検索結果がない

**問題:** 検索結果が返ってこない

**解決策:**
- CQL 構文が正しいか確認してください
- スペースキーは大文字と小文字が区別されます (`space = dev` ではなく `space = DEV` を使用)
- 検索したスペース内のページを表示する権限があるか確認してください

## ドキュメント

- [API Reference](docs/api.md) - 詳細な API 仕様
- [Usage Examples](docs/examples.md) - 一般的なユースケースと CQL クエリ
- [Docker Deployment](docs/docker.md) - Docker デプロイとトラブルシューティングガイド
- [Changelog](CHANGELOG.md) - バージョン履歴と変更点
- [Development Plan](development_plan.md) - プロジェクトのロードマップとアーキテクチャ

## ロードマップ

- [x] Phase 1: プロジェクトセットアップ
- [x] Phase 2: 認証基盤
- [x] Phase 3: Confluence クライアント実装
- [x] Phase 4: MCP ツール実装
- [x] Phase 5: テストとドキュメント
- [x] Phase 6: Docker サポート
- [ ] Phase 7: OAuth2 認証 (将来)

## テスト

### ユニットテストの実行

```bash
pytest
```

### カバレッジ付きテストの実行

```bash
pytest --cov=src --cov-report=term-missing --cov-report=html
```

カバレッジレポートは `htmlcov/` ディレクトリに生成されます。

### 統合テストの実行

統合テストには実際の Confluence 認証情報が必要であり、デフォルトではスキップされます。

実行するには：

```bash
# 環境変数の設定
export RUN_INTEGRATION_TESTS=1
export ATLASSIAN_URL=https://your-domain.atlassian.net/wiki
export ATLASSIAN_USER_EMAIL=your-email@example.com
export ATLASSIAN_API_TOKEN=your_api_token_here

# テストの実行
pytest tests/test_integration.py -v
```

**注意:** 統合テストは Confluence インスタンスに対して実際の API 呼び出しを行います。

## ライセンス

MIT License - 詳細については [LICENSE](LICENSE) ファイルを参照してください。

## 貢献

貢献を歓迎します！以下の手順に従ってください：

1. リポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

以下を確認してください：
- すべてのテストが通過すること
- コードが Black でフォーマットされていること
- コードが Ruff のリンティングを通過すること
- 新しいコードに型ヒントが追加されていること
- ドキュメントが更新されていること

## サポート

問題、質問、または機能リクエストについて：
- GitHub で Issue を開く
- 使用例については [docs/examples.md](docs/examples.md) を確認
- API の詳細については [docs/api.md](docs/api.md) を確認

## 謝辞

使用技術：
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP サーバーフレームワーク
- [httpx](https://www.python-httpx.org/) - HTTP クライアント
- [markdownify](https://github.com/matthewwithanm/python-markdownify) - HTML から Markdown へのコンバータ
- [Pydantic](https://pydantic-docs.helpmanual.io/) - データバリデーション
