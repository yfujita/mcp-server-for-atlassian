# Docker デプロイメントガイド

このドキュメントでは、MCP Server for AtlassianをDockerコンテナとして実行する方法を説明します。

## 目次

1. [前提条件](#前提条件)
2. [クイックスタート](#クイックスタート)
3. [Dockerイメージのビルド](#dockerイメージのビルド)
4. [docker runでの起動](#docker-runでの起動)
5. [docker-composeでの起動](#docker-composeでの起動)
6. [環境変数の設定](#環境変数の設定)
7. [ヘルスチェック](#ヘルスチェック)
8. [ログの確認](#ログの確認)
9. [トラブルシューティング](#トラブルシューティング)
10. [本番環境での運用](#本番環境での運用)

---

## 前提条件

- Docker 20.10以上がインストールされていること
- docker-compose v1.29以上がインストールされていること（docker-compose使用時）
- Atlassian Confluence Cloudアカウントとアクセス権限
- API Token（[取得方法](https://id.atlassian.com/manage-profile/security/api-tokens)）

---

## クイックスタート

最も簡単な起動方法はdocker-composeを使用することです。

```bash
# 1. .envファイルを作成
cp .env.example .env

# 2. .envファイルを編集（認証情報を設定）
vim .env  # または nano, code など

# 3. docker-composeで起動
docker-compose up -d

# 4. ログを確認
docker-compose logs -f
```

サーバーは `http://localhost:8000` で起動します。

---

## Dockerイメージのビルド

### 基本的なビルド

```bash
docker build -t confluence-mcp:latest .
```

### ビルド引数を使用したビルド（オプション）

将来的にビルド引数を使用する場合の例:

```bash
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  -t confluence-mcp:latest \
  .
```

### イメージサイズの確認

```bash
docker images confluence-mcp:latest
```

**期待されるイメージサイズ**: 200MB以下

### マルチステージビルドの利点

このDockerfileは以下の最適化を行っています:

1. **ビルダーステージ**: 依存関係のインストールとビルド
2. **ランタイムステージ**: 実行に必要な最小限のファイルのみを含む

これにより、セキュリティと効率性が向上します。

---

## docker runでの起動

### 基本的な起動方法

```bash
docker run -d \
  --name confluence-mcp \
  -p 8000:8000 \
  -e ATLASSIAN_URL="https://your-domain.atlassian.net/wiki" \
  -e ATLASSIAN_USER_EMAIL="your-email@example.com" \
  -e ATLASSIAN_API_TOKEN="your_api_token_here" \
  -e MCP_TRANSPORT=streamable_http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8000 \
  confluence-mcp:latest
```

### .envファイルを使用した起動

```bash
docker run -d \
  --name confluence-mcp \
  -p 8000:8000 \
  --env-file .env \
  confluence-mcp:latest
```

### コンテナの停止・削除

```bash
# 停止
docker stop confluence-mcp

# 削除
docker rm confluence-mcp

# 停止と削除を同時に実行
docker rm -f confluence-mcp
```

---

## docker-composeでの起動

### 起動

```bash
# バックグラウンドで起動
docker-compose up -d

# フォアグラウンドで起動（ログを表示）
docker-compose up
```

### 停止

```bash
# コンテナを停止（データは保持）
docker-compose stop

# コンテナを停止して削除
docker-compose down
```

### 再起動

```bash
# コンテナを再起動
docker-compose restart

# イメージを再ビルドして起動
docker-compose up -d --build
```

### サービスのスケーリング（オプション）

```bash
# 複数のコンテナを起動（ロードバランシング時）
docker-compose up -d --scale confluence-mcp=3
```

**注意**: スケーリングする場合はポート競合を避けるため、docker-compose.ymlのポート設定を調整してください。

---

## 環境変数の設定

### 必須の環境変数

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `ATLASSIAN_URL` | Confluence インスタンスのベースURL | `https://your-domain.atlassian.net/wiki` |
| `ATLASSIAN_USER_EMAIL` | API Token認証用のメールアドレス | `your-email@example.com` |
| `ATLASSIAN_API_TOKEN` | Atlassian API Token | `ATATT3xFfGF0...` |

### オプションの環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|--------------|
| `MCP_TRANSPORT` | トランスポート方式 | `streamable_http` |
| `MCP_HOST` | バインドするホストアドレス | `0.0.0.0` |
| `MCP_PORT` | リッスンするポート番号 | `8000` |

### .envファイルの例

```bash
# Atlassian Confluence Configuration
ATLASSIAN_URL=https://your-domain.atlassian.net/wiki
ATLASSIAN_USER_EMAIL=your-email@example.com
ATLASSIAN_API_TOKEN=your_api_token_here

# MCP Server Configuration
MCP_TRANSPORT=streamable_http
MCP_HOST=0.0.0.0
MCP_PORT=8000
```

### セキュリティのベストプラクティス

- **絶対に**.envファイルをGitにコミットしないでください
- API Tokenは定期的にローテーションしてください
- 本番環境では、環境変数をDocker SecretsやKubernetes Secretsで管理してください

---

## ヘルスチェック

### ヘルスチェックエンドポイント

コンテナは `/health` エンドポイントを提供しています。

```bash
# curlでヘルスチェック
curl http://localhost:8000/health
```

**成功時のレスポンス例**:

```json
{
  "status": "healthy",
  "confluence_connected": true,
  "details": {
    "message": "Confluence connection successful"
  }
}
```

**失敗時のレスポンス例**:

```json
{
  "status": "unhealthy",
  "confluence_connected": false,
  "details": {
    "error": "Confluence connection failed: Authentication failed"
  }
}
```

### Dockerのヘルスチェックステータス確認

```bash
# コンテナのヘルスステータスを確認
docker inspect --format='{{.State.Health.Status}}' confluence-mcp

# 詳細なヘルスチェック履歴を確認
docker inspect confluence-mcp | jq '.[0].State.Health'
```

ヘルスチェックステータス:
- `starting`: 起動中（start_period内）
- `healthy`: 正常
- `unhealthy`: 異常（retriesで設定した回数失敗）

---

## ログの確認

### docker-composeを使用している場合

```bash
# 全ログを表示
docker-compose logs

# リアルタイムでログを追跡
docker-compose logs -f

# 最新の100行を表示
docker-compose logs --tail=100

# 特定の時刻以降のログを表示
docker-compose logs --since "2024-01-01T00:00:00"
```

### docker runを使用している場合

```bash
# 全ログを表示
docker logs confluence-mcp

# リアルタイムでログを追跡
docker logs -f confluence-mcp

# 最新の100行を表示
docker logs --tail=100 confluence-mcp

# タイムスタンプ付きでログを表示
docker logs -t confluence-mcp
```

### ログファイルの場所

コンテナ内のログは、docker-compose.ymlで設定されたログドライバー（json-file）により管理されています。

デフォルト設定:
- 最大ファイルサイズ: 10MB
- 最大ファイル数: 3

---

## トラブルシューティング

### 1. コンテナが起動しない

**症状**: `docker-compose up` を実行してもコンテナが起動しない

**確認項目**:

```bash
# コンテナの状態を確認
docker-compose ps

# ログを確認
docker-compose logs
```

**よくある原因**:
- .envファイルが存在しない → `.env.example`をコピーして`.env`を作成
- 環境変数が正しく設定されていない → `.env`ファイルの内容を確認
- ポート8000が既に使用されている → `docker-compose.yml`でポート番号を変更

### 2. ヘルスチェックが失敗する

**症状**: コンテナがunhealthyステータスになる

**確認方法**:

```bash
# ヘルスチェックエンドポイントに直接アクセス
curl http://localhost:8000/health

# コンテナ内からヘルスチェック
docker exec confluence-mcp curl -f http://localhost:8000/health
```

**よくある原因**:
- Atlassian認証情報が無効 → API Tokenを再生成
- ネットワーク接続の問題 → ファイアウォール設定を確認
- Confluence APIのレート制限 → しばらく待ってから再試行

### 3. 認証エラー

**症状**: "Authentication failed: Invalid credentials"

**解決方法**:

```bash
# 環境変数が正しく渡されているか確認
docker exec confluence-mcp env | grep ATLASSIAN

# API Tokenを再生成して.envファイルを更新
vim .env

# コンテナを再起動
docker-compose restart
```

### 4. ポート競合

**症状**: "Bind for 0.0.0.0:8000 failed: port is already allocated"

**解決方法**:

```bash
# ポートを使用しているプロセスを確認
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# docker-compose.ymlのポート番号を変更
ports:
  - "8001:8000"  # ホストポートを8001に変更
```

### 5. イメージサイズが大きすぎる

**症状**: Dockerイメージが200MBを大きく超える

**確認方法**:

```bash
docker images confluence-mcp:latest
```

**解決方法**:
- `.dockerignore`が正しく設定されているか確認
- 不要なファイルがコピーされていないか確認
- マルチステージビルドが正しく機能しているか確認

### 6. コンテナ内でのデバッグ

```bash
# コンテナに入る
docker exec -it confluence-mcp /bin/bash

# Pythonで直接テスト
docker exec -it confluence-mcp python -c "from src.config import get_settings; print(get_settings())"

# ネットワーク接続確認
docker exec -it confluence-mcp curl -I https://your-domain.atlassian.net
```

---

## 本番環境での運用

### リソース制限の設定

本番環境では、リソース制限を明示的に設定することを推奨します。

`docker-compose.yml`の`deploy`セクションのコメントを外して調整:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'      # 使用可能なCPU数の上限
      memory: 512M     # 使用可能なメモリの上限
    reservations:
      cpus: '0.5'      # 予約するCPU数
      memory: 256M     # 予約するメモリ
```

### 自動再起動の設定

docker-compose.ymlには既に設定されています:

```yaml
restart: unless-stopped
```

これにより、以下の場合にコンテナが自動的に再起動されます:
- コンテナがクラッシュした場合
- Dockerデーモンが再起動された場合

### ログのローテーション

docker-compose.ymlには既に設定されています:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"   # 1ファイルの最大サイズ
    max-file: "3"     # 保持するファイル数
```

### セキュリティ強化

1. **非rootユーザーでの実行**: Dockerfileで既に設定済み（UID 1000）
2. **読み取り専用ルートファイルシステム**（オプション）:

```yaml
read_only: true
tmpfs:
  - /tmp
```

3. **Docker Secretsの使用**（Docker Swarm環境）:

```yaml
secrets:
  - atlassian_api_token

services:
  confluence-mcp:
    secrets:
      - atlassian_api_token
```

### モニタリング

Prometheusやその他のモニタリングツールと統合する場合は、ヘルスチェックエンドポイントを活用できます。

**例: Prometheusのblackbox_exporter**:

```yaml
scrape_configs:
  - job_name: 'confluence-mcp'
    metrics_path: /health
    static_configs:
      - targets: ['localhost:8000']
```

### バックアップとリカバリ

現在、このMCPサーバーはステートレスです（永続化データなし）。
環境変数（.envファイル）のみバックアップしてください。

```bash
# .envファイルのバックアップ
cp .env .env.backup-$(date +%Y%m%d)
```

---

## まとめ

Docker化により、MCP Server for Atlassianを以下の環境で簡単にデプロイできます:

- ローカル開発環境
- リモートサーバー
- クラウド環境（AWS ECS, Google Cloud Run, Azure Container Instancesなど）
- Kubernetes環境

次のステップ:
- [API仕様書](api.md)を確認
- [使用例](examples.md)でCQLクエリを学習
- 本番環境へのデプロイメント計画を立てる

---

## 参考リンク

- [Docker公式ドキュメント](https://docs.docker.com/)
- [docker-compose公式ドキュメント](https://docs.docker.com/compose/)
- [Atlassian API Token管理](https://id.atlassian.com/manage-profile/security/api-tokens)
- [FastMCPドキュメント](https://github.com/jlowin/fastmcp)
