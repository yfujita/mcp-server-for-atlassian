# API Reference

This document provides detailed technical specifications for all MCP tools provided by the Confluence MCP Server.

## Table of Contents
- [Tool: search_pages](#tool-search_pages)
- [Tool: get_page_content](#tool-get_page_content)
- [Tool: get_child_pages](#tool-get_child_pages)
- [Error Handling](#error-handling)
- [Data Models](#data-models)

---

## Tool: search_pages

Search for Confluence pages using CQL (Confluence Query Language).

### Signature

```python
async def search_pages(cql_query: str, limit: int = 25) -> list[dict]
```

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `cql_query` | `string` | Yes | - | CQL query string to search for pages. See [CQL syntax](#cql-syntax-reference) |
| `limit` | `integer` | No | `25` | Maximum number of results to return. Valid range: 1-100 |

#### Parameter Details

**cql_query:**
- Must be a non-empty string
- Follows Confluence Query Language syntax
- Case-sensitive for field values (e.g., space keys)
- Supports operators: `=`, `!=`, `~`, `>`, `<`, `>=`, `<=`, `IN`, `NOT IN`
- Supports logical operators: `AND`, `OR`, `NOT`

**limit:**
- Automatically clamped to range [1, 100]
- Values less than 1 are set to 1
- Values greater than 100 are set to 100

### Output Format

Returns a list of page objects. Each page object contains:

```typescript
{
  id: string;              // Unique page identifier (e.g., "123456")
  title: string;           // Page title
  url: string;             // Direct URL to the page
  space_key: string;       // Space key where the page is located
  excerpt: string | null;  // Search result snippet (may be null)
}
```

### Example Request

```json
{
  "cql_query": "space = DEV AND label = api AND text ~ 'authentication'",
  "limit": 10
}
```

### Example Response

```json
[
  {
    "id": "123456",
    "title": "API Authentication Guide",
    "url": "https://your-domain.atlassian.net/wiki/spaces/DEV/pages/123456",
    "space_key": "DEV",
    "excerpt": "This guide explains how to authenticate API requests using..."
  },
  {
    "id": "789012",
    "title": "OAuth 2.0 Implementation",
    "url": "https://your-domain.atlassian.net/wiki/spaces/DEV/pages/789012",
    "space_key": "DEV",
    "excerpt": "OAuth 2.0 is our recommended authentication method for..."
  }
]
```

### Empty Results

When no pages match the query:

```json
[]
```

### Errors

| Error Type | Condition | Message |
|------------|-----------|---------|
| `ValueError` | Empty or whitespace-only query | "CQL query cannot be empty" |
| `APIError` | Confluence API error | Varies based on API response |
| `AuthenticationError` | Invalid credentials | "Authentication failed: Invalid credentials" |
| `RateLimitError` | Rate limit exceeded | "Rate limit exceeded. Retry after N seconds" |

---

## Tool: get_page_content

Retrieve the full content of a specific Confluence page.

### Signature

```python
async def get_page_content(page_id: str, format: str = "markdown") -> dict
```

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page_id` | `string` | Yes | - | Unique identifier of the page to retrieve |
| `format` | `string` | No | `"markdown"` | Content format: `"markdown"` or `"html"` |

#### Parameter Details

**page_id:**
- Must be a non-empty string
- Can be numeric string (e.g., "123456") or full page ID
- Obtained from search results or page URLs

**format:**
- `"markdown"`: HTML content converted to Markdown (recommended for LLMs)
- `"html"`: Raw HTML content (storage format)
- Case-insensitive
- Invalid values default to markdown

### Output Format

Returns a page content object:

```typescript
{
  id: string;           // Page identifier
  title: string;        // Page title
  url: string;          // Direct URL to the page
  content: string;      // Page content (Markdown or HTML based on format parameter)
  format: string;       // Content format: "markdown" or "html"
  space_key: string;    // Space key where the page is located
  version: number;      // Current version number
  created_at: string;   // ISO 8601 timestamp of creation
  updated_at: string;   // ISO 8601 timestamp of last update
}
```

### Example Request (Markdown)

```json
{
  "page_id": "123456",
  "format": "markdown"
}
```

### Example Response (Markdown)

```json
{
  "id": "123456",
  "title": "Getting Started Guide",
  "url": "https://your-domain.atlassian.net/wiki/spaces/DOCS/pages/123456",
  "content": "# Getting Started\n\n## Prerequisites\n\nBefore you begin, ensure you have:\n\n- Python 3.10 or higher\n- Access to Confluence Cloud\n\n## Installation\n\nInstall the package using pip:\n\n```bash\npip install our-package\n```\n\n## Configuration\n\nCreate a `.env` file with the following variables:\n\n```\nATLASSIAN_URL=https://your-domain.atlassian.net/wiki\nATLASSIAN_USER_EMAIL=your-email@example.com\nATLASSIAN_API_TOKEN=your-token-here\n```",
  "format": "markdown",
  "space_key": "DOCS",
  "version": 8,
  "created_at": "2024-01-15T10:30:00.000Z",
  "updated_at": "2024-02-07T14:20:00.000Z"
}
```

### Example Request (HTML)

```json
{
  "page_id": "123456",
  "format": "html"
}
```

### Example Response (HTML)

```json
{
  "id": "123456",
  "title": "Getting Started Guide",
  "url": "https://your-domain.atlassian.net/wiki/spaces/DOCS/pages/123456",
  "content": "<h1>Getting Started</h1><h2>Prerequisites</h2><p>Before you begin, ensure you have:</p><ul><li>Python 3.10 or higher</li><li>Access to Confluence Cloud</li></ul>...",
  "format": "html",
  "space_key": "DOCS",
  "version": 8,
  "created_at": "2024-01-15T10:30:00.000Z",
  "updated_at": "2024-02-07T14:20:00.000Z"
}
```

### Errors

| Error Type | Condition | Message |
|------------|-----------|---------|
| `ValueError` | Empty page_id | "Page ID cannot be empty" |
| `PageNotFoundError` | Page doesn't exist or no access | "Page not found: {page_id}" |
| `APIError` | Confluence API error | Varies based on API response |
| `AuthenticationError` | Invalid credentials | "Authentication failed: Invalid credentials" |
| `ConversionError` | Markdown conversion failed | "Failed to convert HTML to Markdown: {details}" |

---

## Tool: get_child_pages

Retrieve all child pages of a specified parent page.

### Signature

```python
async def get_child_pages(parent_id: str, limit: int = 50) -> list[dict]
```

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `parent_id` | `string` | Yes | - | Page ID of the parent page |
| `limit` | `integer` | No | `50` | Maximum number of child pages to return. Valid range: 1-100 |

#### Parameter Details

**parent_id:**
- Must be a non-empty string
- Can be numeric string (e.g., "123456") or full page ID
- Obtained from search results or page URLs

**limit:**
- Automatically clamped to range [1, 100]
- Default is 50 (higher than search_pages default)
- Values less than 1 are set to 1
- Values greater than 100 are set to 100

### Output Format

Returns a list of child page objects:

```typescript
{
  id: string;        // Unique page identifier
  title: string;     // Page title
  position: number;  // Position in parent's child list (0-indexed)
}
```

### Example Request

```json
{
  "parent_id": "123456",
  "limit": 50
}
```

### Example Response

```json
[
  {
    "id": "123457",
    "title": "Chapter 1: Introduction",
    "position": 0
  },
  {
    "id": "123458",
    "title": "Chapter 2: Getting Started",
    "position": 1
  },
  {
    "id": "123459",
    "title": "Chapter 3: Advanced Topics",
    "position": 2
  }
]
```

### Empty Results

When the parent page has no child pages:

```json
[]
```

### Errors

| Error Type | Condition | Message |
|------------|-----------|---------|
| `ValueError` | Empty parent_id | "Parent ID cannot be empty" |
| `PageNotFoundError` | Parent page doesn't exist or no access | "Parent page not found: {parent_id}" |
| `APIError` | Confluence API error | Varies based on API response |
| `AuthenticationError` | Invalid credentials | "Authentication failed: Invalid credentials" |

---

## Error Handling

All errors inherit from the base `MCPServerError` exception class.

### Error Hierarchy

```
MCPServerError (base)
├── APIError
│   ├── AuthenticationError
│   ├── RateLimitError
│   └── PageNotFoundError
├── ConfigurationError
└── ConversionError
```

### Error Response Format

When an error occurs, the tool returns an error response:

```typescript
{
  error: {
    type: string;      // Error type (e.g., "AuthenticationError")
    message: string;   // Human-readable error message
    details?: object;  // Optional additional error details
  }
}
```

### Common Errors

#### AuthenticationError

**Cause:** Invalid credentials or insufficient permissions

**HTTP Status:** 401 Unauthorized or 403 Forbidden

**Example:**
```json
{
  "error": {
    "type": "AuthenticationError",
    "message": "Authentication failed: Invalid credentials",
    "details": {
      "status_code": 401
    }
  }
}
```

**Resolution:**
- Verify `ATLASSIAN_USER_EMAIL` and `ATLASSIAN_API_TOKEN` are correct
- Check API token hasn't expired
- Ensure user has access to the requested resource

#### RateLimitError

**Cause:** Too many requests in a short time period

**HTTP Status:** 429 Too Many Requests

**Example:**
```json
{
  "error": {
    "type": "RateLimitError",
    "message": "Rate limit exceeded. Retry after 60 seconds",
    "details": {
      "retry_after": 60
    }
  }
}
```

**Resolution:**
- Wait for the specified `retry_after` duration
- Implement exponential backoff in your client
- Reduce request frequency

#### PageNotFoundError

**Cause:** Page doesn't exist or user lacks access

**HTTP Status:** 404 Not Found

**Example:**
```json
{
  "error": {
    "type": "PageNotFoundError",
    "message": "Page not found: 123456",
    "details": {
      "page_id": "123456"
    }
  }
}
```

**Resolution:**
- Verify page ID is correct
- Check user has permission to view the page
- Confirm page hasn't been deleted

#### ConversionError

**Cause:** Failed to convert HTML to Markdown

**Example:**
```json
{
  "error": {
    "type": "ConversionError",
    "message": "Failed to convert HTML to Markdown: Invalid HTML structure",
    "details": {
      "page_id": "123456"
    }
  }
}
```

**Resolution:**
- Request HTML format instead: `get_page_content(page_id, format="html")`
- Check if page contains unsupported macros or complex formatting

---

## Data Models

### PageSearchResult

```python
class PageSearchResult:
    id: str                # Page identifier
    title: str             # Page title
    url: str               # Direct URL to page
    space_key: str         # Space key
    excerpt: Optional[str] # Search result snippet
```

### PageContent

```python
class PageContent:
    id: str               # Page identifier
    title: str            # Page title
    url: str              # Direct URL to page
    content: str          # Page content (HTML or Markdown)
    format: str           # Content format: "html" or "markdown"
    space_key: str        # Space key
    version: int          # Version number
    created_at: str       # ISO 8601 creation timestamp
    updated_at: str       # ISO 8601 update timestamp
```

### ChildPage

```python
class ChildPage:
    id: str        # Page identifier
    title: str     # Page title
    position: int  # Position in parent's child list
```

### PaginatedResponse

Generic container for paginated API responses:

```python
class PaginatedResponse[T]:
    results: List[T]  # List of result items
    start: int        # Starting index of results
    limit: int        # Maximum results per page
    size: int         # Number of results in this response
    total_size: int   # Total number of available results
```

---

## CQL Syntax Reference

### Field Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals (exact match) | `space = DEV` |
| `!=` | Not equals | `type != comment` |
| `~` | Contains (fuzzy match) | `text ~ "keyword"` |
| `!~` | Does not contain | `text !~ "deprecated"` |
| `>` | Greater than | `created > "2024-01-01"` |
| `<` | Less than | `created < "2024-12-31"` |
| `>=` | Greater than or equal | `created >= "2024-01-01"` |
| `<=` | Less than or equal | `created <= "2024-12-31"` |
| `IN` | In list | `space IN (DEV, PROD)` |
| `NOT IN` | Not in list | `space NOT IN (ARCHIVE)` |

### Logical Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `AND` | Logical AND | `space = DEV AND type = page` |
| `OR` | Logical OR | `label = api OR label = rest` |
| `NOT` | Logical NOT | `NOT label = deprecated` |

### Common Fields

| Field | Description | Type | Example |
|-------|-------------|------|---------|
| `type` | Content type | string | `type = page` |
| `space` | Space key | string | `space = DEV` |
| `title` | Page title | string | `title ~ "guide"` |
| `text` | Full text content | string | `text ~ "authentication"` |
| `label` | Labels/tags | string | `label = "api"` |
| `creator` | Creator email | string | `creator = "user@example.com"` |
| `contributor` | Contributor email | string | `contributor = "user@example.com"` |
| `created` | Creation date | date | `created >= "2024-01-01"` |
| `lastModified` | Last modified date | date | `lastModified >= now("-7d")` |

### Date Functions

| Function | Description | Example |
|----------|-------------|---------|
| `now()` | Current date/time | `lastModified >= now()` |
| `now("-Nd")` | N days ago | `created >= now("-7d")` |
| `now("-Nw")` | N weeks ago | `created >= now("-2w")` |
| `now("-NM")` | N months ago | `created >= now("-1M")` |
| `now("-Ny")` | N years ago | `created >= now("-1y")` |

---

## Rate Limits

Confluence Cloud enforces rate limits on API requests:

- **Default Rate Limit:** Varies based on your Atlassian plan
- **Typical Limit:** 200 requests per minute per user
- **Response Header:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`

### Best Practices

1. **Implement exponential backoff** when receiving 429 errors
2. **Respect Retry-After header** in rate limit responses
3. **Cache frequently accessed content** when possible
4. **Use appropriate limits** to minimize number of requests
5. **Batch operations** when fetching multiple pages

---

## Authentication

The server uses API Token authentication (HTTP Basic Auth):

- **Username:** User email address
- **Password:** API Token (not your Atlassian password)

API tokens are generated from:
https://id.atlassian.com/manage-profile/security/api-tokens

### Security Considerations

1. **Never commit API tokens** to version control
2. **Use environment variables** for credentials
3. **Rotate tokens regularly** for security
4. **Use minimal permissions** required for your use case
5. **Monitor token usage** through Atlassian admin console

---

## Version Compatibility

This API reference is for MCP Server for Atlassian Confluence version **0.1.0**.

### Confluence REST API

- **API Version:** Confluence Cloud REST API v1
- **Documentation:** https://developer.atlassian.com/cloud/confluence/rest/

### MCP Protocol

- **MCP Version:** 2024-11-05 specification
- **Documentation:** https://modelcontextprotocol.io/

---

## Additional Resources

- [Usage Examples](./examples.md)
- [CQL Official Documentation](https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/)
- [Confluence REST API Reference](https://developer.atlassian.com/cloud/confluence/rest/v1/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
