# プロジェクト概要
Atlassian Confluence (Cloud版) の情報をAIエージェントが参照できるようにするためのMCP (Model Context Protocol) サーバーを構築する。

# 要件

## 1. 機能要件

### MCPサーバー機能
FastMCPを使用し、以下のトランスポート層をサポートする。
* **Stdio**: ローカルのエディタ（Cursor, VS Code等）からの利用
* **SSE (Server-Sent Events)**: リモート接続やDocker経由での利用
* **Streamable HTTP**: リモート接続やDocker経由での利用

### 対象Atlassianリソース (Confluence)
以下のツール（Tool）を実装する。
1. **search_pages**: CQL (Confluence Query Language) を用いてページを検索する。
   - 入力: 検索クエリ文字列
   - 出力: ページタイトル、ID、URLのリスト
2. **get_page_content**: 指定されたページIDのコンテンツを取得する。
   - 入力: ページID
   - **重要**: 取得したHTML形式のコンテンツは、LLMが理解しやすくトークンを節約するために**Markdown形式に変換**して返すこと。
3. **get_child_pages**: 指定されたページの子ページ一覧を取得する。
   - 入力: 親ページID
   - 出力: 子ページのタイトル、IDのリスト

## 2. 非機能要件・設計指針

### 認証 (Authentication)
* 初期実装として **API Token (Basic Auth)** 方式を採用する。
* 将来的に OAuth2 (3LO) への対応を予定しているため、**Strategyパターン**等を用いて認証ロジックを抽象化・分離し、容易に切り替え可能な設計にする。

### 構成・環境
* **言語**: Python 3.10+
* **ライブラリ**: `fastmcp`, `httpx` (HTTPクライアント), `markdownify` (HTML→Markdown変換)
* **設定**: 認証情報やベースURLは環境変数 (`.env`) から読み込む。
  - `ATLASSIAN_URL`
  - `ATLASSIAN_USER_EMAIL`
  - `ATLASSIAN_API_TOKEN`

### Docker化
* 軽量なイメージ（`python:slim` 等）を使用する。
* 環境変数を渡して `docker run` で起動可能にする。
* `entrypoint` は MCPサーバーの起動コマンドとする。

## 3. 成果物
* Pythonソースコード（モジュール分割された状態）
* `Dockerfile`
* `requirements.txt` または `pyproject.toml`
* `.env.example`