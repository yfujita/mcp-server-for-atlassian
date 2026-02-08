# Atlassian Confluence MCP サーバー 開発計画

## ゴールの要約 (Goal Summary)

Atlassian Confluence (Cloud版) の情報をAIエージェントが参照できるようにするMCPサーバーを構築する。FastMCPを使用し、3つの主要ツール（search_pages, get_page_content, get_child_pages）を実装する。初期認証はAPI Token方式で、将来的にOAuth2への切り替えが容易な設計とする。

**成功基準:**
- Stdio, SSE, Streamable HTTPの3つのトランスポートをサポート
- CQL検索、ページコンテンツ取得（Markdown変換）、子ページ一覧取得が正常動作
- 認証ロジックが抽象化され、OAuth2への切り替えが容易
- Docker化され、環境変数で設定可能
- ローカル（Cursor/VS Code）およびリモートから利用可能

## 前提条件 (Assumptions)

- Python 3.10以上の実行環境が利用可能
- Atlassian Confluence Cloud環境へのアクセス権限がある
- API Tokenの発行が可能
- Docker環境が利用可能（Docker化フェーズ）
- FastMCP 2.x（安定版）を使用（必要に応じて3.0ベータへの移行を検討）
- ページコンテンツはHTML（ストレージフォーマット）で取得可能
- CQL検索がConfluence REST API v1で利用可能

---

## 戦略的概要 (Strategic Overview)

| Phase | 内容 | 優先度 |
|-------|------|--------|
| Phase 1 | プロジェクトセットアップ | 必須（MVP） |
| Phase 2 | 認証基盤の実装 | 必須（MVP） |
| Phase 3 | Confluenceクライアントの実装 | 必須（MVP） |
| Phase 4 | MCPツールの実装 | 必須（MVP） |
| Phase 5 | テストとドキュメント | 必須（MVP）〜高優先度 |
| Phase 6 | Docker化とデプロイメント | 高優先度 |
| Phase 7 | OAuth2対応（将来対応） | 中優先度 |

---

## 推奨ディレクトリ構造

```
mcp-server-for-atlassian/
├── src/
│   ├── __init__.py
│   ├── main.py                    # MCPサーバーのエントリーポイント
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── base.py                # 認証抽象基底クラス
│   │   ├── api_token.py           # API Token認証実装
│   │   └── oauth2.py              # OAuth2認証（将来実装）
│   ├── confluence/
│   │   ├── __init__.py
│   │   ├── client.py              # Confluence APIクライアント
│   │   ├── models.py              # データモデル（Pydantic）
│   │   └── converters.py          # HTML→Markdown変換
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search.py              # search_pages ツール
│   │   ├── content.py             # get_page_content ツール
│   │   └── children.py            # get_child_pages ツール
│   ├── config.py                  # 設定管理
│   └── exceptions.py              # カスタム例外
├── tests/
│   ├── __init__.py
│   ├── test_auth/
│   ├── test_confluence/
│   └── test_tools/
├── references/                     # 技術調査ドキュメント（既存）
├── .env.example                    # 環境変数テンプレート
├── .gitignore
├── pyproject.toml                  # プロジェクト設定・依存関係
├── README.md
├── Dockerfile
└── docker-compose.yml
```

---

## 詳細計画 (Detailed Plan)

### Phase 1: プロジェクトセットアップ

**目的**: 開発を開始するための基盤を構築する

**タスク**:
1. プロジェクトディレクトリ構造の作成
2. `pyproject.toml`の作成
   - 依存関係: `fastmcp>=2.0.0`, `httpx>=0.27.0`, `markdownify>=0.12.0`, `pydantic>=2.0.0`, `python-dotenv>=1.0.0`
   - 開発依存: `pytest`, `pytest-asyncio`, `pytest-cov`, `black`, `ruff`, `mypy`
3. `.env.example`の作成
4. `.gitignore`の作成
5. 基本的なREADME.mdの作成

**検証**: `pip install -e .`でインストールできる

---

### Phase 2: 認証基盤の実装

**目的**: Strategyパターンを使用して認証ロジックを抽象化し、API Token認証を実装する

**タスク**:
1. 認証基底クラスの実装 (`src/auth/base.py`)
   ```python
   from abc import ABC, abstractmethod
   from typing import Dict

   class AuthenticationStrategy(ABC):
       @abstractmethod
       async def get_auth_headers(self) -> Dict[str, str]:
           pass

       @abstractmethod
       async def authenticate(self) -> bool:
           pass
   ```

2. API Token認証の実装 (`src/auth/api_token.py`)
3. OAuth2認証のスタブ実装 (`src/auth/oauth2.py`)
4. 設定管理の実装 (`src/config.py`) - Pydantic Settings使用
5. カスタム例外の定義 (`src/exceptions.py`)

**検証**: API Token認証で正しいBasic認証ヘッダーが生成される

---

### Phase 3: Confluenceクライアントの実装

**目的**: Confluence REST APIとの通信を抽象化し、エラーハンドリングとデータ変換を実装する

**タスク**:
1. データモデルの定義 (`src/confluence/models.py`)
   - `PageSearchResult`, `PageContent`, `ChildPage`
2. HTML→Markdown変換の実装 (`src/confluence/converters.py`)
3. Confluenceクライアントの実装 (`src/confluence/client.py`)
   - `search_pages(cql_query, limit)` - CQL検索
   - `get_page_content(page_id, as_markdown)` - コンテンツ取得
   - `get_child_pages(parent_id, limit)` - 子ページ取得
4. ロギング設定の追加

**検証**: 実際のConfluence APIに対して各メソッドが動作する

---

### Phase 4: MCPツールの実装

**目的**: FastMCPを使用して3つのツールを実装し、すべてのトランスポート層をサポートする

**タスク**:
1. search_pagesツールの実装 (`src/tools/search.py`)
2. get_page_contentツールの実装 (`src/tools/content.py`)
3. get_child_pagesツールの実装 (`src/tools/children.py`)
4. メインエントリーポイントの実装 (`src/main.py`)
   - トランスポート切り替え: `MCP_TRANSPORT` 環境変数
5. `pyproject.toml`にエントリーポイントを追加

**検証**:
- `confluence-mcp`コマンドで起動できる
- Claude Desktopから呼び出せる
- SSE/streamable_httpモードで動作する

---

### Phase 5: テストとドキュメント

**目的**: コードの品質を保証し、ユーザーが使用できるようにドキュメントを整備する

**タスク**:
1. ユニットテストの実装（カバレッジ80%以上目標）
2. 統合テストの実装（オプション）
3. README.mdの完成
4. 使用例ドキュメントの作成 (`docs/examples.md`)
5. API仕様書の作成 (`docs/api.md`)

---

### Phase 6: Docker化とデプロイメント

**目的**: Dockerイメージを作成し、リモート環境でも動作可能にする

**タスク**:
1. Dockerfileの作成（python:3.11-slim使用）
2. docker-compose.ymlの作成
3. マルチステージビルドの最適化（イメージサイズ200MB以下）
4. ヘルスチェックエンドポイントの実装

---

### Phase 7: OAuth2対応（将来対応）

**目的**: OAuth 2.0 (3LO) 認証を実装し、マルチテナント対応を可能にする

**タスク**:
1. OAuth2認証クライアントの実装
2. トークン管理の実装（暗号化保存）
3. OAuth2フロー用Webエンドポイントの追加
4. ドキュメントの更新

---

## リスクと緩和策 (Risks & Mitigations)

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| Confluence API仕様の変更 | APIが動作しなくなる | APIバージョン明示、Pydantic検証、統合テスト |
| レート制限 | 429エラー発生 | リトライロジック、Retry-Afterヘッダー遵守 |
| HTML→Markdown変換の不完全性 | マクロが正しく変換されない | 特有タグ除去、HTMLオプション提供 |
| 認証情報の漏洩 | セキュリティ問題 | .gitignore設定、OAuth2推奨 |
| 非同期処理の複雑性 | デッドロック | async/await一貫使用、タイムアウト設定 |

---

## 実装の優先順位

### 必須（MVP）
- Phase 1〜4: 基本機能の実装
- Phase 5: 基本テスト + README

### 高優先度（初期リリース）
- Phase 5: 完全なテストスイート + ドキュメント
- Phase 6: Docker化

### 中優先度（今後の機能強化）
- Phase 7: OAuth2対応
- ページネーション機能
- CQLクエリビルダー

### 低優先度（将来検討）
- キャッシュ機能
- 多言語対応

---

## 推奨される最初のステップ

1. **Phase 1のタスク1を実行**: プロジェクトディレクトリ構造を作成
   ```bash
   mkdir -p src/{auth,confluence,tools} tests/{test_auth,test_confluence,test_tools}
   touch src/{__init__,main,config,exceptions}.py
   touch src/auth/{__init__,base,api_token,oauth2}.py
   touch src/confluence/{__init__,client,models,converters}.py
   touch src/tools/{__init__,search,content,children}.py
   ```

2. **Phase 1のタスク2を実行**: `pyproject.toml`を作成し依存関係を定義

3. **Phase 1のタスク3を実行**: `.env.example`を作成
   ```bash
   cp .env.example .env
   # .envを編集してAtlassian認証情報を入力
   ```

これらの最初のステップを完了すると、Phase 2以降の実装に着手できる基盤が整います。
