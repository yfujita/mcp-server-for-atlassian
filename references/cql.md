# Confluence Query Language (CQL)

## 概要

Confluence Query Language (CQL) は、Confluenceのコンテンツを検索するための構造化クエリ言語です。CQLを使用すると、REST APIを通じて高度で柔軟な検索を実行できます。

## 基本構文

CQLクエリは、以下の構造を持ちます:

```
field operator value
```

**例:**
```cql
type = page
title ~ "API Documentation"
space = DOCS AND type = page
```

## CQLの構成要素

### 1. Field (フィールド)

Confluenceコンテンツのインデックス化されたプロパティを表します。

### 2. Operator (演算子)

フィールドと値を比較するための記号またはキーワードです。

### 3. Value (値) または Function (関数)

検索したい値、または値を返す関数です。

## 主要なフィールド

### コンテンツタイプ

| フィールド | 説明 | 例 |
|---------|------|-----|
| `type` | コンテンツタイプ | `type = page` |
| | | `type = blogpost` |
| | | `type = attachment` |

### スペース関連

| フィールド | 説明 | 例 |
|---------|------|-----|
| `space` | スペースキー | `space = DOCS` |
| | | `space in (DOCS, MARKETING)` |
| `space.type` | スペースタイプ | `space.type = global` |
| `space.title` | スペース名 | `space.title ~ "Documentation"` |

### ページ・コンテンツ関連

| フィールド | 説明 | 例 |
|---------|------|-----|
| `title` | タイトル | `title = "API Guide"` |
| | | `title ~ "API"` |
| `text` | 本文テキスト | `text ~ "REST API"` |
| `id` | コンテンツID | `id = 12345` |
| `parent` | 親ページID | `parent = 67890` |

### 作成者・日時関連

| フィールド | 説明 | 例 |
|---------|------|-----|
| `creator` | 作成者 | `creator = currentUser()` |
| | | `creator = "john.doe"` |
| `contributor` | 編集者 | `contributor = currentUser()` |
| `created` | 作成日時 | `created >= "2024-01-01"` |
| `lastModified` | 最終更新日時 | `lastModified >= now("-7d")` |

### ラベル

| フィールド | 説明 | 例 |
|---------|------|-----|
| `label` | ラベル | `label = "api"` |
| | | `label in ("api", "rest")` |

### 添付ファイル

| フィールド | 説明 | 例 |
|---------|------|-----|
| `attachment` | 添付ファイル名 | `attachment ~ "*.pdf"` |
| `mediaType` | MIMEタイプ | `mediaType = "application/pdf"` |

## 演算子

### 比較演算子

| 演算子 | 説明 | 例 |
|-------|------|-----|
| `=` | 完全一致 | `type = page` |
| `!=` | 不一致 | `type != blogpost` |
| `>` | より大きい | `created > "2024-01-01"` |
| `>=` | 以上 | `created >= "2024-01-01"` |
| `<` | より小さい | `created < "2024-12-31"` |
| `<=` | 以下 | `created <= "2024-12-31"` |

**注意:** テキストフィールド（title, textなど）には使用できません。

### テキスト検索演算子

| 演算子 | 説明 | 例 |
|-------|------|-----|
| `~` | 含む（部分一致） | `title ~ "API"` |
| `!~` | 含まない | `title !~ "Draft"` |

### リスト演算子

| 演算子 | 説明 | 例 |
|-------|------|-----|
| `IN` | いずれかに一致 | `space IN (DOCS, DEV)` |
| `NOT IN` | いずれにも一致しない | `label NOT IN (draft, archived)` |

### 論理演算子

| 演算子 | 説明 | 例 |
|-------|------|-----|
| `AND` | かつ | `type = page AND space = DOCS` |
| `OR` | または | `space = DOCS OR space = DEV` |
| `NOT` | 否定 | `NOT label = draft` |

**優先順位:**
1. `NOT`
2. `AND`
3. `OR`

**括弧を使用した優先順位の明示:**
```cql
(space = DOCS OR space = DEV) AND type = page
```

## ワイルドカード

### 単一文字ワイルドカード: `?`

```cql
title ~ "API?"      # "APIS", "APIv" など
```

### 複数文字ワイルドカード: `*`

```cql
title ~ "API*"      # "API Guide", "API Documentation" など
title ~ "*API"      # "REST API", "GraphQL API" など
title ~ "*API*"     # "API"を含むすべて
```

## 関数

### 日時関数

| 関数 | 説明 | 例 |
|-----|------|-----|
| `now()` | 現在日時 | `created >= now()` |
| `now("-7d")` | 7日前 | `lastModified >= now("-7d")` |
| `now("+1w")` | 1週間後 | `created <= now("+1w")` |

**時間単位:**
- `d`: 日
- `w`: 週
- `M`: 月
- `y`: 年

### ユーザー関数

| 関数 | 説明 | 例 |
|-----|------|-----|
| `currentUser()` | 現在のユーザー | `creator = currentUser()` |

### スペース関連関数

| 関数 | 説明 | 例 |
|-----|------|-----|
| `currentSpace()` | 現在のスペース | `space = currentSpace()` |
| `favouriteSpaces()` | お気に入りスペース | `space IN favouriteSpaces()` |

### コンテンツ関数

| 関数 | 説明 | 例 |
|-----|------|-----|
| `ancestor()` | 祖先ページ | `ancestor = 12345` |

## よく使うクエリ例

### ページ検索

**スペース内のすべてのページ:**
```cql
type = page AND space = DOCS
```

**タイトルでページを検索:**
```cql
type = page AND title ~ "API"
```

**本文にキーワードを含むページ:**
```cql
type = page AND text ~ "REST API"
```

### 日付範囲で検索

**過去7日間に作成されたページ:**
```cql
type = page AND created >= now("-7d")
```

**今年更新されたページ:**
```cql
type = page AND lastModified >= "2024-01-01"
```

**特定期間に作成されたページ:**
```cql
type = page AND created >= "2024-01-01" AND created <= "2024-12-31"
```

### ラベルで検索

**特定のラベルが付いたページ:**
```cql
type = page AND label = "api"
```

**複数のラベルのいずれかが付いたページ:**
```cql
type = page AND label IN ("api", "rest", "graphql")
```

**複数のラベルがすべて付いたページ:**
```cql
type = page AND label = "api" AND label = "rest"
```

### ユーザーで検索

**自分が作成したページ:**
```cql
type = page AND creator = currentUser()
```

**特定のユーザーが作成したページ:**
```cql
type = page AND creator = "john.doe"
```

**自分が編集したページ:**
```cql
type = page AND contributor = currentUser()
```

### 階層で検索

**特定ページの子ページ:**
```cql
type = page AND parent = 12345
```

**特定ページの子孫ページ:**
```cql
type = page AND ancestor = 12345
```

### 添付ファイルで検索

**PDF添付ファイルがあるページ:**
```cql
type = attachment AND mediaType = "application/pdf"
```

**特定のファイル名パターンの添付ファイル:**
```cql
type = attachment AND attachment ~ "*.xlsx"
```

### 複雑な検索

**複数スペースで、特定ラベルの、最近更新されたページ:**
```cql
type = page AND 
space IN (DOCS, DEV) AND 
label IN ("api", "guide") AND 
lastModified >= now("-30d")
```

**自分が作成した、下書きでない、特定スペースのページ:**
```cql
type = page AND 
space = DOCS AND 
creator = currentUser() AND 
label != "draft"
```

## ソート

CQLクエリに`ORDER BY`句を追加してソートできます。

**構文:**
```cql
query ORDER BY field [ASC|DESC]
```

**例:**
```cql
type = page ORDER BY created DESC
type = page ORDER BY title ASC
type = page AND space = DOCS ORDER BY lastModified DESC
```

**複数フィールドでソート:**
```cql
type = page ORDER BY space ASC, created DESC
```

## Pythonでの使用例

### 基本的な検索

```python
import httpx
from urllib.parse import quote

async def search_confluence(
    base_url: str,
    email: str,
    api_token: str,
    cql_query: str,
    limit: int = 25
):
    """CQLクエリでConfluenceを検索"""
    url = f"{base_url}/rest/api/content/search"
    
    params = {
        "cql": cql_query,
        "limit": limit
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            auth=(email, api_token),
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        return response.json()

# 使用例
results = await search_confluence(
    "https://your-domain.atlassian.net/wiki",
    "email@example.com",
    "api_token",
    "type = page AND space = DOCS AND title ~ 'API'"
)

for page in results.get("results", []):
    print(f"{page['title']} (ID: {page['id']})")
```

### CQLクエリビルダー

```python
class CQLBuilder:
    """CQLクエリを構築するヘルパークラス"""
    
    def __init__(self):
        self.conditions = []
        self.order_by_clause = None
    
    def type(self, content_type: str):
        """コンテンツタイプを指定"""
        self.conditions.append(f"type = {content_type}")
        return self
    
    def space(self, space_key: str):
        """スペースを指定"""
        self.conditions.append(f"space = {space_key}")
        return self
    
    def spaces(self, space_keys: list[str]):
        """複数のスペースを指定"""
        spaces = ", ".join(space_keys)
        self.conditions.append(f"space IN ({spaces})")
        return self
    
    def title_contains(self, keyword: str):
        """タイトルにキーワードを含む"""
        self.conditions.append(f'title ~ "{keyword}"')
        return self
    
    def text_contains(self, keyword: str):
        """本文にキーワードを含む"""
        self.conditions.append(f'text ~ "{keyword}"')
        return self
    
    def label(self, label_name: str):
        """ラベルを指定"""
        self.conditions.append(f"label = {label_name}")
        return self
    
    def labels(self, label_names: list[str]):
        """複数のラベルのいずれかを含む"""
        labels = ", ".join(f'"{l}"' for l in label_names)
        self.conditions.append(f"label IN ({labels})")
        return self
    
    def created_after(self, date: str):
        """指定日以降に作成"""
        self.conditions.append(f'created >= "{date}"')
        return self
    
    def modified_after(self, date: str):
        """指定日以降に更新"""
        self.conditions.append(f'lastModified >= "{date}"')
        return self
    
    def modified_last_days(self, days: int):
        """過去N日間に更新"""
        self.conditions.append(f'lastModified >= now("-{days}d")')
        return self
    
    def created_by_current_user(self):
        """現在のユーザーが作成"""
        self.conditions.append("creator = currentUser()")
        return self
    
    def parent(self, parent_id: str):
        """親ページIDを指定"""
        self.conditions.append(f"parent = {parent_id}")
        return self
    
    def ancestor(self, ancestor_id: str):
        """祖先ページIDを指定"""
        self.conditions.append(f"ancestor = {ancestor_id}")
        return self
    
    def order_by(self, field: str, direction: str = "ASC"):
        """ソート順を指定"""
        self.order_by_clause = f"ORDER BY {field} {direction}"
        return self
    
    def build(self) -> str:
        """CQLクエリを生成"""
        query = " AND ".join(self.conditions)
        if self.order_by_clause:
            query += f" {self.order_by_clause}"
        return query

# 使用例
builder = CQLBuilder()
query = (builder
    .type("page")
    .space("DOCS")
    .title_contains("API")
    .modified_last_days(30)
    .order_by("lastModified", "DESC")
    .build())

print(query)
# 出力: type = page AND space = DOCS AND title ~ "API" AND lastModified >= now("-30d") ORDER BY lastModified DESC

# より複雑な例
query = (CQLBuilder()
    .type("page")
    .spaces(["DOCS", "DEV", "MARKETING"])
    .labels(["api", "rest"])
    .text_contains("authentication")
    .created_after("2024-01-01")
    .order_by("created", "DESC")
    .build())

print(query)
```

### よく使うクエリのテンプレート

```python
class CQLTemplates:
    """よく使うCQLクエリのテンプレート集"""
    
    @staticmethod
    def recent_pages(space: str, days: int = 7) -> str:
        """最近更新されたページ"""
        return f'type = page AND space = {space} AND lastModified >= now("-{days}d") ORDER BY lastModified DESC'
    
    @staticmethod
    def pages_by_title(space: str, keyword: str) -> str:
        """タイトルでページを検索"""
        return f'type = page AND space = {space} AND title ~ "{keyword}"'
    
    @staticmethod
    def my_pages(space: str = None) -> str:
        """自分が作成したページ"""
        query = "type = page AND creator = currentUser()"
        if space:
            query += f" AND space = {space}"
        return query + " ORDER BY created DESC"
    
    @staticmethod
    def pages_with_label(space: str, label: str) -> str:
        """特定ラベルのページ"""
        return f'type = page AND space = {space} AND label = "{label}"'
    
    @staticmethod
    def child_pages(parent_id: str) -> str:
        """子ページ一覧"""
        return f"type = page AND parent = {parent_id} ORDER BY title ASC"
    
    @staticmethod
    def search_text(keyword: str, space: str = None) -> str:
        """全文検索"""
        query = f'text ~ "{keyword}"'
        if space:
            query += f" AND space = {space}"
        return query

# 使用例
cql = CQLTemplates.recent_pages("DOCS", days=14)
results = await search_confluence(base_url, email, token, cql)
```

## エスケープ

特殊文字を含む値を検索する場合は、引用符で囲みます。

**特殊文字:**
- スペース
- カンマ `,`
- 括弧 `()`, `[]`
- クォート `"`, `'`

**例:**
```cql
title ~ "API Documentation (v2)"
space = "My Space"
```

## 制限事項

1. **検索結果の上限**: デフォルトで最大1000件（expandを使用すると制限が変わる）
2. **複雑なクエリのパフォーマンス**: 非常に複雑なクエリは実行時間が長くなる可能性がある
3. **テキスト検索の精度**: `~`演算子は部分一致だが、完全一致検索には`=`を使用できない（テキストフィールドでは）

## パフォーマンスのヒント

1. **スペースを指定する**: 可能な限りスペースを絞り込む
2. **必要な拡張のみを要求する**: expandパラメータで必要な情報のみを取得
3. **ページネーションを使用する**: 大量の結果を一度に取得しない
4. **インデックス化されたフィールドを使用**: title, type, spaceなど

## 参考リンク

- [Advanced searching using CQL](https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/)
- [Performing text searches using CQL](https://developer.atlassian.com/cloud/confluence/performing-text-searches-using-cql/)
- [CQL operators](https://developer.atlassian.com/cloud/confluence/cql-operators/)
- [CQL function reference](https://developer.atlassian.com/server/confluence/cql-function-reference/)
- [CQL field reference](https://developer.atlassian.com/server/confluence/cql-field-reference/)
- [Confluence Query Language (CQL) Guide | Praecipio](https://www.praecipio.com/resources/articlesarticles/confluence-query-language-cql-guide)
