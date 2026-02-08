# ==========================================
# Stage 1: Builder - 依存関係のインストール
# ==========================================
FROM python:3.11-slim AS builder

# メタデータラベル
LABEL maintainer="your-email@example.com"
LABEL description="MCP Server for Atlassian Confluence integration"
LABEL version="0.1.0"

# 作業ディレクトリの設定
WORKDIR /build

# ビルドに必要な最小限のパッケージをインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルのコピー（レイヤーキャッシュ最適化）
COPY pyproject.toml setup.py ./

# 依存関係のインストール（/build/.venvに配置）
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e .

# ==========================================
# Stage 2: Runtime - 最小限の実行環境
# ==========================================
FROM python:3.11-slim AS runtime

# メタデータラベル
LABEL maintainer="your-email@example.com"
LABEL description="MCP Server for Atlassian Confluence integration"
LABEL version="0.1.0"

# セキュリティ: 非rootユーザーで実行
# mcpserverユーザー（UID 1000）を作成
RUN groupadd -r mcpserver --gid=1000 && \
    useradd -r -g mcpserver --uid=1000 --home-dir=/app --shell=/bin/bash mcpserver

# 作業ディレクトリの設定
WORKDIR /app

# 必要なシステムパッケージのインストール（実行時に必要な最小限）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    procps \
    && rm -rf /var/lib/apt/lists/*

# ビルダーステージからPythonパッケージをコピー
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# アプリケーションコードのコピー
COPY --chown=mcpserver:mcpserver src/ ./src/
COPY --chown=mcpserver:mcpserver setup.py pyproject.toml ./

# パッケージを再インストール（エントリーポイントを有効化）
RUN pip install --no-cache-dir -e .

# 環境変数のデフォルト値設定
ENV MCP_TRANSPORT=streamable_http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ポートの公開
EXPOSE 8000

# 非rootユーザーに切り替え
USER mcpserver

# ヘルスチェック設定（プロセス確認）
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f confluence-mcp || exit 1

# エントリーポイント: MCPサーバーを起動
ENTRYPOINT ["confluence-mcp"]
