# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using the MCP Server for Atlassian Confluence.

## Table of Contents
- [Connection Issues](#connection-issues)
- [Authentication Issues](#authentication-issues)
- [Search Issues](#search-issues)
- [Content Retrieval Issues](#content-retrieval-issues)
- [Performance Issues](#performance-issues)
- [Configuration Issues](#configuration-issues)
- [Debugging Tips](#debugging-tips)

---

## Connection Issues

### Cannot Connect to Confluence

**Symptoms:**
- Connection timeout errors
- "Failed to connect" messages
- Network-related errors

**Possible Causes:**
1. Incorrect `ATLASSIAN_URL`
2. Network/firewall blocking HTTPS traffic
3. Confluence instance is down

**Solutions:**

1. **Verify URL format:**
   ```bash
   # Correct format (includes /wiki)
   ATLASSIAN_URL=https://your-domain.atlassian.net/wiki

   # Incorrect formats
   ATLASSIAN_URL=https://your-domain.atlassian.net
   ATLASSIAN_URL=your-domain.atlassian.net/wiki
   ```

2. **Test connectivity:**
   ```bash
   # Test if you can reach Confluence
   curl https://your-domain.atlassian.net/wiki
   ```

3. **Check firewall settings:**
   - Ensure outbound HTTPS (port 443) is allowed
   - Check if you're behind a corporate proxy
   - If using a proxy, configure `HTTP_PROXY` and `HTTPS_PROXY` environment variables

4. **Verify Confluence status:**
   - Check https://status.atlassian.com/
   - Verify your instance is accessible via web browser

---

## Authentication Issues

### Authentication Failed: Invalid Credentials

**Symptoms:**
- "401 Unauthorized" errors
- "Authentication failed" messages
- "Invalid credentials" errors

**Possible Causes:**
1. Incorrect email address
2. Invalid or expired API token
3. API token not properly copied

**Solutions:**

1. **Verify email address:**
   ```bash
   # Must match your Atlassian account email
   ATLASSIAN_USER_EMAIL=your-actual-email@example.com
   ```

2. **Regenerate API token:**
   - Visit https://id.atlassian.com/manage-profile/security/api-tokens
   - Create a new API token
   - Copy the token immediately (you can't view it again)
   - Update `.env` file with new token

3. **Check for extra spaces:**
   ```bash
   # Wrong (has trailing space)
   ATLASSIAN_API_TOKEN=abcd1234

   # Correct (no spaces)
   ATLASSIAN_API_TOKEN=abcd1234
   ```

4. **Verify token hasn't expired:**
   - API tokens don't expire by default, but can be revoked
   - Check your token list in Atlassian account settings

### Permission Denied (403 Forbidden)

**Symptoms:**
- "403 Forbidden" errors
- "You don't have permission" messages

**Possible Causes:**
1. User lacks permission to access the space/page
2. Space is restricted
3. Page-level restrictions

**Solutions:**

1. **Verify space access:**
   - Log into Confluence web interface
   - Try to access the same space/page manually
   - Check space permissions with space admin

2. **Check page restrictions:**
   - Pages can have individual restrictions
   - You need both space access AND page access

3. **Request appropriate permissions:**
   - Contact your Confluence admin
   - Request "View" permission for required spaces

---

## Search Issues

### Search Returns No Results

**Symptoms:**
- Empty result list `[]`
- "No pages found" despite pages existing

**Possible Causes:**
1. Incorrect CQL syntax
2. Case-sensitive space keys
3. No permission to view results
4. Typos in query

**Solutions:**

1. **Check space key case:**
   ```cql
   # Wrong (lowercase)
   space = dev

   # Correct (uppercase as configured in Confluence)
   space = DEV
   ```

2. **Verify CQL syntax:**
   ```cql
   # Wrong (missing quotes)
   text ~ keyword

   # Correct (with quotes)
   text ~ "keyword"
   ```

3. **Test with simpler query:**
   ```python
   # Start simple
   search_pages("type=page", limit=5)

   # Then add filters
   search_pages("type=page AND space=DEV", limit=5)
   ```

4. **Verify you can see results in Confluence:**
   - Try the same search in Confluence UI
   - Check if pages exist in the specified space

### CQL Syntax Error

**Symptoms:**
- "Invalid CQL query" errors
- "Syntax error" messages

**Common Mistakes:**

1. **Missing quotes:**
   ```cql
   # Wrong
   text ~ api documentation

   # Correct
   text ~ "api documentation"
   ```

2. **Wrong operator:**
   ```cql
   # Wrong (~ is for fuzzy match, not exact)
   space ~ DEV

   # Correct (= for exact match)
   space = DEV
   ```

3. **Invalid date format:**
   ```cql
   # Wrong
   created >= 2024-01-01

   # Correct
   created >= "2024-01-01"
   ```

4. **Unbalanced parentheses:**
   ```cql
   # Wrong
   (space = DEV AND type = page OR space = PROD

   # Correct
   (space = DEV AND type = page) OR (space = PROD AND type = page)
   ```

---

## Content Retrieval Issues

### Page Not Found

**Symptoms:**
- "Page not found: {page_id}" error
- 404 errors

**Possible Causes:**
1. Incorrect page ID
2. Page deleted or moved
3. No permission to view page

**Solutions:**

1. **Verify page ID:**
   - Check the page URL in browser:
     `https://domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Title`
   - The number after `/pages/` is the page ID (e.g., `123456`)

2. **Use search first:**
   ```python
   # Find the page by search
   results = search_pages("title ~ 'Page Title'")
   if results:
       page_id = results[0]['id']
       content = get_page_content(page_id)
   ```

3. **Check page still exists:**
   - Try accessing the page in Confluence web interface
   - Check if page was deleted or moved to archive

### Markdown Conversion Failed

**Symptoms:**
- "ConversionError" messages
- Malformed Markdown output
- Missing content after conversion

**Possible Causes:**
1. Complex Confluence macros
2. Malformed HTML
3. Unsupported content types

**Solutions:**

1. **Use HTML format instead:**
   ```python
   # If Markdown conversion fails, get HTML
   content = get_page_content(page_id, format="html")
   ```

2. **Report specific pages:**
   - Note which pages fail conversion
   - Check if they have special macros or formatting

3. **Known limitations:**
   - Some Confluence macros don't convert well
   - Very complex layouts may lose structure
   - Embedded content may not appear in Markdown

---

## Performance Issues

### Slow Response Times

**Symptoms:**
- Requests take a long time
- Timeouts

**Possible Causes:**
1. Large page content
2. Network latency
3. Confluence server load
4. Rate limiting

**Solutions:**

1. **Use appropriate limits:**
   ```python
   # Instead of fetching many results
   search_pages("type=page", limit=100)  # Slow

   # Fetch fewer results
   search_pages("type=page", limit=10)   # Faster
   ```

2. **Filter searches effectively:**
   ```python
   # Too broad (searches everything)
   search_pages("text ~ 'the'")

   # More specific (faster)
   search_pages("space = DEV AND text ~ 'API'")
   ```

3. **Check network latency:**
   ```bash
   # Test round-trip time
   curl -w "Time: %{time_total}s\n" -o /dev/null -s \
     https://your-domain.atlassian.net/wiki
   ```

4. **Consider caching:**
   - Cache frequently accessed pages in your application
   - Avoid repeated requests for the same content

### Rate Limit Errors

**Symptoms:**
- "429 Too Many Requests" errors
- "Rate limit exceeded" messages

**Possible Causes:**
1. Too many requests in short time
2. Multiple users sharing same API token
3. Hitting Confluence Cloud limits

**Solutions:**

1. **Implement backoff:**
   ```python
   # The client already retries automatically
   # But you can add delays between requests in your code
   import asyncio

   for page in pages:
       content = get_page_content(page['id'])
       await asyncio.sleep(0.5)  # 500ms delay between requests
   ```

2. **Reduce request frequency:**
   - Batch operations when possible
   - Cache results locally
   - Only fetch when truly needed

3. **Check rate limit headers:**
   - Monitor `X-RateLimit-Remaining` in responses
   - Respect `Retry-After` header value

4. **Typical limits:**
   - ~200 requests per minute per user (varies by plan)
   - Shared across all apps using same API token

---

## Configuration Issues

### Environment Variables Not Loaded

**Symptoms:**
- "Configuration error" messages
- "Missing required field" errors

**Possible Causes:**
1. `.env` file in wrong location
2. Variables not exported (when running directly)
3. Typos in variable names

**Solutions:**

1. **Verify `.env` location:**
   ```bash
   # Should be in project root
   ls -la /path/to/mcp-server-for-atlassian/.env
   ```

2. **Check variable names:**
   ```bash
   # Correct names (case-sensitive)
   ATLASSIAN_URL=...
   ATLASSIAN_USER_EMAIL=...
   ATLASSIAN_API_TOKEN=...
   ```

3. **For direct Python execution:**
   ```bash
   # Export variables
   export $(cat .env | xargs)
   python -m src.main
   ```

4. **For Claude Desktop:**
   - Variables must be in `claude_desktop_config.json`
   - NOT read from `.env` file

### Invalid Transport Configuration

**Symptoms:**
- "Unsupported transport" error
- Server fails to start

**Possible Causes:**
1. Typo in `MCP_TRANSPORT` value
2. Invalid transport type

**Solutions:**

1. **Use valid transport values:**
   ```bash
   # Valid options
   MCP_TRANSPORT=stdio          # Default, for local editors
   MCP_TRANSPORT=sse            # For remote access
   MCP_TRANSPORT=streamable_http # For remote access
   ```

2. **Default is stdio:**
   - If not specified, `stdio` is used
   - Perfect for Claude Desktop integration

---

## Debugging Tips

### Enable Debug Logging

To see detailed logs:

```python
# In your code
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Check HTTP Requests

To see actual HTTP requests/responses:

```python
import httpx

# Enable httpx logging
logging.getLogger("httpx").setLevel(logging.DEBUG)
```

### Test with Minimal Configuration

Create a test script:

```python
import asyncio
from src.auth.api_token import APITokenAuth
from src.confluence.client import ConfluenceClient

async def test():
    auth = APITokenAuth(
        email="your-email@example.com",
        api_token="your-token",
        base_url="https://your-domain.atlassian.net/wiki"
    )

    async with ConfluenceClient(
        base_url="https://your-domain.atlassian.net/wiki",
        auth_strategy=auth
    ) as client:
        results = await client.search_pages("type=page", limit=1)
        print(f"Found {len(results.results)} pages")
        if results.results:
            print(f"First page: {results.results[0].title}")

asyncio.run(test())
```

### Common Log Messages

**Normal operation:**
```
INFO - Initializing MCP server...
INFO - Loaded settings: base_url=https://...
INFO - Confluence client initialized successfully
INFO - All tools registered successfully
```

**Authentication issues:**
```
ERROR - Authentication failed: Invalid credentials
ERROR - Failed to connect to Confluence API
```

**Rate limiting:**
```
WARNING - Rate limit exceeded, retrying after 60 seconds
```

### Verify Installation

```bash
# Check package is installed
pip show mcp-server-for-atlassian

# Check dependencies
pip list | grep -E 'fastmcp|httpx|markdownify|pydantic'

# Verify command is available
which confluence-mcp

# Test import
python -c "from src.auth.api_token import APITokenAuth; print('OK')"
```

### Check Confluence API Directly

Test Confluence API with curl:

```bash
# Test authentication
curl -u "your-email@example.com:your-token" \
  "https://your-domain.atlassian.net/wiki/rest/api/space"

# Test search
curl -u "your-email@example.com:your-token" \
  "https://your-domain.atlassian.net/wiki/rest/api/content/search?cql=type=page&limit=1"
```

---

## Getting Help

If you're still experiencing issues:

1. **Check existing issues:**
   - Search GitHub issues for similar problems
   - Look at closed issues for solutions

2. **Gather information:**
   - Error messages (full stack trace)
   - Environment details (Python version, OS)
   - Configuration (sanitized, without tokens)
   - Steps to reproduce

3. **Create a minimal reproduction:**
   - Simplify to smallest failing case
   - Share code that demonstrates the issue

4. **Open an issue:**
   - Provide all gathered information
   - Include debug logs if available
   - Mention what you've already tried

---

## Additional Resources

- [API Reference](./api.md)
- [Usage Examples](./examples.md)
- [Confluence CQL Documentation](https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/)
- [Atlassian API Status](https://status.atlassian.com/)
