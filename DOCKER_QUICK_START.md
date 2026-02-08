# Docker クイックスタートガイド

このガイドでは、最短で MCP Server for Atlassian を Docker で起動する方法を説明します。

## 前提条件

- Docker と docker-compose がインストール済みであること
- Atlassian API Token を取得済みであること

## 5分で起動

### 1. 環境変数ファイルの作成

```bash
cp .env.example .env
```

### 2. .env ファイルを編集

以下の3つの値を設定してください:

```bash
ATLASSIAN_URL=https://your-domain.atlassian.net/wiki
ATLASSIAN_USER_EMAIL=your-email@example.com
ATLASSIAN_API_TOKEN=your_api_token_here
```

**API Token の取得方法**:
https://id.atlassian.com/manage-profile/security/api-tokens

### 3. 起動

```bash
docker-compose up -d
```

### 4. 動作確認

```bash
# ログを確認
docker-compose logs -f

# ヘルスチェック
curl http://localhost:8000/health
```

成功すると以下のようなレスポンスが返ります:

```json
{
  "status": "healthy",
  "confluence_connected": true,
  "details": {
    "message": "Confluence connection successful"
  }
}
```

## よく使うコマンド

```bash
# サーバーを起動
docker-compose up -d

# ログをリアルタイムで表示
docker-compose logs -f

# サーバーを停止
docker-compose stop

# サーバーを停止してコンテナを削除
docker-compose down

# サーバーを再起動
docker-compose restart

# イメージを再ビルド
docker-compose up -d --build
```

## トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
docker-compose logs

# コンテナの状態を確認
docker-compose ps
```

### ヘルスチェックが失敗する

```bash
# ヘルスチェックエンドポイントに直接アクセス
curl http://localhost:8000/health

# 環境変数が正しく設定されているか確認
docker-compose exec confluence-mcp env | grep ATLASSIAN
```

### ポートが既に使用されている

docker-compose.yml のポート番号を変更:

```yaml
ports:
  - "8001:8000"  # ホスト側を8001に変更
```

## 詳細なドキュメント

さらに詳しい情報は以下を参照してください:

- [Docker デプロイメントガイド](docs/docker.md) - 包括的なDockerガイド
- [API リファレンス](docs/api.md) - MCPツールの詳細仕様
- [使用例](docs/examples.md) - CQLクエリの例

## サーバーの停止

使用後は以下のコマンドで停止してください:

```bash
docker-compose down
```

## 次のステップ

1. Claude Desktop や他の MCP クライアントから接続
2. CQL クエリで Confluence を検索
3. ページコンテンツを取得して AI に読み込ませる

Enjoy! 🚀
