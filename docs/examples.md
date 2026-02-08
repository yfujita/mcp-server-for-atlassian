# Usage Examples

This document provides practical examples of using the MCP Server for Atlassian Confluence.

## Table of Contents
- [Search Pages](#search-pages)
- [Get Page Content](#get-page-content)
- [Get Child Pages](#get-child-pages)
- [Common Use Cases](#common-use-cases)
- [CQL Query Examples](#cql-query-examples)

---

## Search Pages

The `search_pages` tool allows you to search for Confluence pages using CQL (Confluence Query Language).

### Basic Text Search

Search for pages containing specific keywords:

```
search_pages(cql_query="text ~ 'API documentation'", limit=10)
```

**Response:**
```json
[
  {
    "id": "123456",
    "title": "REST API Documentation",
    "url": "https://your-domain.atlassian.net/wiki/spaces/DEV/pages/123456",
    "space_key": "DEV",
    "excerpt": "This page contains documentation for our REST API..."
  }
]
```

### Search in Specific Space

Find pages within a particular space:

```
search_pages(cql_query="space = DEV AND type = page", limit=25)
```

### Search by Title

Search for pages with specific title patterns:

```
search_pages(cql_query="title ~ 'getting started'", limit=5)
```

### Combined Search

Combine multiple criteria:

```
search_pages(cql_query="space = DOCS AND label = tutorial AND text ~ 'beginner'", limit=10)
```

---

## Get Page Content

The `get_page_content` tool retrieves the full content of a specific page, converted to Markdown format for better LLM comprehension.

### Get Page in Markdown Format (Default)

```
get_page_content(page_id="123456")
```

**Response:**
```json
{
  "id": "123456",
  "title": "Getting Started Guide",
  "url": "https://your-domain.atlassian.net/wiki/spaces/DOCS/pages/123456",
  "content": "# Getting Started\n\nWelcome to our platform...",
  "format": "markdown",
  "space_key": "DOCS",
  "version": 5,
  "created_at": "2024-01-15T10:30:00.000Z",
  "updated_at": "2024-02-01T14:20:00.000Z"
}
```

### Get Page in HTML Format

If you need the raw HTML content:

```
get_page_content(page_id="123456", format="html")
```

---

## Get Child Pages

The `get_child_pages` tool retrieves all child pages of a specified parent page.

### Get All Child Pages

```
get_child_pages(parent_id="123456", limit=50)
```

**Response:**
```json
[
  {
    "id": "123457",
    "title": "Chapter 1: Introduction",
    "position": 0
  },
  {
    "id": "123458",
    "title": "Chapter 2: Installation",
    "position": 1
  },
  {
    "id": "123459",
    "title": "Chapter 3: Configuration",
    "position": 2
  }
]
```

### Explore Page Hierarchy

You can traverse the page hierarchy by recursively getting child pages:

```
# Get root page
root = get_page_content(page_id="100000")

# Get its children
children = get_child_pages(parent_id="100000")

# Get grandchildren
for child in children:
    grandchildren = get_child_pages(parent_id=child["id"])
```

---

## Common Use Cases

### Use Case 1: Find and Read Documentation

**Scenario:** You need to find and read API documentation about authentication.

```python
# Step 1: Search for relevant pages
results = search_pages(
    cql_query="space = DEV AND text ~ 'authentication' AND label = api",
    limit=5
)

# Step 2: Review search results
for page in results:
    print(f"Found: {page['title']} - {page['url']}")

# Step 3: Get full content of the most relevant page
content = get_page_content(page_id=results[0]['id'])
print(content['content'])
```

### Use Case 2: Explore Documentation Structure

**Scenario:** You want to understand the structure of a documentation space.

```python
# Step 1: Find the main documentation page
results = search_pages(
    cql_query="space = DOCS AND title ~ 'index' OR title ~ 'home'",
    limit=1
)

main_page_id = results[0]['id']

# Step 2: Get child pages (main sections)
sections = get_child_pages(parent_id=main_page_id, limit=50)

# Step 3: For each section, get its subsections
for section in sections:
    print(f"Section: {section['title']}")
    subsections = get_child_pages(parent_id=section['id'], limit=50)
    for subsection in subsections:
        print(f"  - {subsection['title']}")
```

### Use Case 3: Search for Recent Updates

**Scenario:** You need to find pages updated in the last week.

```python
results = search_pages(
    cql_query="lastModified >= now('-1w') AND space = DEV",
    limit=20
)

for page in results:
    content = get_page_content(page_id=page['id'])
    print(f"Updated: {content['title']} (Last modified: {content['updated_at']})")
```

### Use Case 4: Find Pages by Author

**Scenario:** Find all pages created by a specific user.

```python
results = search_pages(
    cql_query="creator = 'john.doe@example.com' AND space = TEAM",
    limit=50
)

for page in results:
    print(f"{page['title']} - {page['url']}")
```

---

## CQL Query Examples

CQL (Confluence Query Language) is a powerful query language for searching Confluence content.

### Basic Syntax

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Exact match | `space = DEV` |
| `~` | Contains (fuzzy) | `text ~ "keyword"` |
| `!=` | Not equal | `type != comment` |
| `AND` | Logical AND | `space = DEV AND type = page` |
| `OR` | Logical OR | `label = api OR label = rest` |
| `NOT` | Logical NOT | `NOT label = deprecated` |

### Search by Content

```cql
# Text contains specific keyword
text ~ "kubernetes"

# Title contains keyword
title ~ "getting started"

# Exact title match
title = "Installation Guide"
```

### Search by Space

```cql
# Pages in specific space
space = DEV

# Pages in multiple spaces
space in (DEV, PROD, DOCS)
```

### Search by Type

```cql
# Only pages (not blog posts)
type = page

# Only blog posts
type = blogpost

# Both pages and blog posts
type in (page, blogpost)
```

### Search by Labels

```cql
# Pages with specific label
label = "documentation"

# Pages with multiple labels
label = "api" AND label = "rest"

# Pages with any of the labels
label in ("tutorial", "guide", "howto")
```

### Search by Creator/Contributor

```cql
# Pages created by user
creator = "john.doe@example.com"

# Pages contributed to by user
contributor = "jane.smith@example.com"
```

### Search by Date

```cql
# Created in the last week
created >= now("-1w")

# Modified in the last 30 days
lastModified >= now("-30d")

# Created between specific dates
created >= "2024-01-01" AND created <= "2024-12-31"

# Modified before specific date
lastModified <= "2024-01-01"
```

### Advanced Queries

```cql
# Pages in DEV space, labeled as API, created in last month
space = DEV AND label = "api" AND created >= now("-1M")

# Pages containing "docker" but not labeled as deprecated
text ~ "docker" AND NOT label = "deprecated"

# Recently updated pages in specific spaces
(space = DEV OR space = PROD) AND lastModified >= now("-7d")

# Pages with wildcards in title
title ~ "API*guide"

# Pages by multiple authors
creator in ("john.doe@example.com", "jane.smith@example.com")
```

### Date/Time Functions

```cql
# Relative dates
now()           # Current date/time
now("-1d")      # 1 day ago
now("-1w")      # 1 week ago
now("-1M")      # 1 month ago
now("-1y")      # 1 year ago

# Examples
created >= now("-7d")           # Created in last 7 days
lastModified >= now("-1M")      # Modified in last month
```

---

## Tips and Best Practices

### 1. Start Broad, Then Narrow

Begin with a broad search and progressively add filters:

```cql
# Start broad
type = page

# Add space filter
space = DEV AND type = page

# Add label filter
space = DEV AND type = page AND label = "api"

# Add text search
space = DEV AND type = page AND label = "api" AND text ~ "authentication"
```

### 2. Use Appropriate Limits

- Use smaller limits (5-10) for exploratory searches
- Use larger limits (50-100) when you need comprehensive results
- Default limit is 25, which works well for most cases

### 3. Leverage Markdown Conversion

The default Markdown format is optimized for LLM consumption:
- Reduces token count compared to HTML
- Preserves document structure (headings, lists, links)
- Easier to parse and understand

### 4. Check for Empty Results

Always handle cases where searches return no results:

```python
results = search_pages(cql_query="space = NONEXISTENT")
if not results:
    print("No pages found")
```

### 5. Combine Tools Effectively

Use search to find pages, then get detailed content:

```python
# Search for relevant pages
candidates = search_pages(cql_query="text ~ 'API key'", limit=5)

# Examine each candidate
for page in candidates:
    content = get_page_content(page_id=page['id'])
    # Process content...
```

---

## Troubleshooting

### Issue: Search Returns No Results

**Possible causes:**
- Space key is case-sensitive: use `space = DEV`, not `space = dev`
- CQL syntax error: check quotes and operators
- No permissions to view the space/pages

**Solution:**
```cql
# Verify space exists and you have access
space = YOURSPACE AND type = page
```

### Issue: Page Content is Too Large

**Solution:**
Use search excerpts first, then fetch full content only when needed:

```python
# Review excerpts first
results = search_pages(cql_query="...", limit=10)
for page in results:
    print(page['excerpt'])  # Preview before fetching full content
```

### Issue: CQL Query Syntax Error

**Common mistakes:**
- Missing quotes around text: `text ~ keyword` → `text ~ "keyword"`
- Wrong operator: `space ~ DEV` → `space = DEV`
- Invalid date format: `created >= 2024-01-01` → `created >= "2024-01-01"`

---

## Additional Resources

- [CQL Official Documentation](https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/)
- [Confluence REST API Reference](https://developer.atlassian.com/cloud/confluence/rest/v1/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
