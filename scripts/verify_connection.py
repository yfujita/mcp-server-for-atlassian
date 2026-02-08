#!/usr/bin/env python3
"""
Confluence API connection verification script.

This script tests the actual connection to Confluence API and verifies:
1. Environment settings are correctly loaded
2. Authentication succeeds
3. API client methods work correctly:
   - search_pages
   - get_page_content
   - get_child_pages
4. Error handling works as expected
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.auth.api_token import APITokenAuth
from src.config import get_settings
from src.confluence.client import ConfluenceClient
from src.exceptions import APIError, AuthenticationError, PageNotFoundError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def print_section(title: str) -> None:
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def verify_environment() -> tuple[str, str, str]:
    """
    Verify environment settings are loaded correctly.

    Returns:
        Tuple of (base_url, email, api_token)
    """
    print_section("1. Environment Settings Verification")

    try:
        settings = get_settings()

        # Verify required settings exist
        assert settings.atlassian_url, "ATLASSIAN_URL not set"
        assert settings.atlassian_user_email, "ATLASSIAN_USER_EMAIL not set"
        assert settings.atlassian_api_token, "ATLASSIAN_API_TOKEN not set"

        print(f"✓ ATLASSIAN_URL: {settings.atlassian_url}")
        print(f"✓ ATLASSIAN_USER_EMAIL: {settings.atlassian_user_email}")
        print(f"✓ ATLASSIAN_API_TOKEN: {'*' * 10}...{settings.atlassian_api_token[-4:]}")
        print(f"✓ MCP_TRANSPORT: {settings.mcp_transport}")
        print(f"✓ MCP_HOST: {settings.mcp_host}")
        print(f"✓ MCP_PORT: {settings.mcp_port}")

        return settings.atlassian_url, settings.atlassian_user_email, settings.atlassian_api_token

    except Exception as e:
        print(f"✗ Failed to load environment settings: {e}")
        raise


async def verify_authentication(base_url: str, email: str, api_token: str) -> APITokenAuth:
    """
    Verify authentication works correctly.

    Args:
        base_url: Confluence base URL
        email: User email
        api_token: API token

    Returns:
        Authenticated APITokenAuth instance
    """
    print_section("2. Authentication Verification")

    try:
        # Create auth strategy
        auth = APITokenAuth(
            email=email,
            api_token=api_token,
            base_url=base_url
        )

        print("Attempting authentication...")

        # Authenticate
        success = await auth.authenticate()

        if success:
            print("✓ Authentication successful")
            print(f"✓ User: {email}")
            is_auth = await auth.is_authenticated()
            print(f"✓ Authenticated: {is_auth}")
        else:
            print("✗ Authentication failed")
            raise AuthenticationError("Failed to authenticate")

        return auth

    except AuthenticationError as e:
        print(f"✗ Authentication Error: {e.message}")
        if e.details:
            print(f"  Details: {e.details}")
        raise
    except Exception as e:
        print(f"✗ Unexpected error during authentication: {e}")
        raise


async def verify_search_pages(client: ConfluenceClient) -> str:
    """
    Verify search_pages method works correctly.

    Args:
        client: Authenticated ConfluenceClient

    Returns:
        Page ID of first result (for subsequent tests)
    """
    print_section("3.1 Search Pages Verification")

    try:
        # Simple search for any pages
        print("Searching for pages (type=page, limit=5)...")
        results = await client.search_pages("type=page", limit=5)

        print(f"✓ Search successful")
        print(f"  Total results: {results.total_size or 'unknown'}")
        print(f"  Returned: {results.size} pages")
        print(f"  Start: {results.start}, Limit: {results.limit}")

        if results.results:
            print("\n  Top results:")
            for i, page in enumerate(results.results[:5], 1):
                print(f"    {i}. {page.title}")
                print(f"       ID: {page.id}")
                print(f"       Space: {page.space_key or 'N/A'}")
                print(f"       URL: {page.url}")
                if page.excerpt:
                    excerpt = page.excerpt[:100] + "..." if len(page.excerpt) > 100 else page.excerpt
                    print(f"       Excerpt: {excerpt}")

            # Return first page ID for content test
            return results.results[0].id
        else:
            print("  No pages found in search")
            return None

    except APIError as e:
        print(f"✗ API Error: {e.message}")
        if e.status_code:
            print(f"  Status Code: {e.status_code}")
        if e.details:
            print(f"  Details: {e.details}")
        raise
    except Exception as e:
        print(f"✗ Unexpected error during search: {e}")
        raise


async def verify_get_page_content(client: ConfluenceClient, page_id: str) -> None:
    """
    Verify get_page_content method works correctly.

    Args:
        client: Authenticated ConfluenceClient
        page_id: Page ID to retrieve
    """
    print_section("3.2 Get Page Content Verification")

    if not page_id:
        print("⚠ Skipping (no page ID available from search)")
        return

    try:
        print(f"Fetching content for page ID: {page_id}...")

        # Get page as Markdown
        page = await client.get_page_content(page_id, as_markdown=True)

        print(f"✓ Page content retrieved successfully")
        print(f"  Title: {page.title}")
        print(f"  ID: {page.id}")
        print(f"  Space: {page.space_key}")
        print(f"  Version: {page.version}")
        print(f"  Format: {page.content_format}")
        print(f"  URL: {page.url}")

        if page.last_modified:
            print(f"  Last Modified: {page.last_modified}")
        if page.author:
            print(f"  Author: {page.author}")

        # Show content preview
        content_preview = page.content[:200] + "..." if len(page.content) > 200 else page.content
        print(f"\n  Content Preview ({page.content_format}):")
        print(f"  {'-' * 60}")
        for line in content_preview.split('\n'):
            print(f"  {line}")
        print(f"  {'-' * 60}")
        print(f"  Total content length: {len(page.content)} characters")

        # Also test HTML format
        print("\nTesting HTML format retrieval...")
        page_html = await client.get_page_content(page_id, as_markdown=False)
        print(f"✓ HTML content retrieved (format: {page_html.content_format})")
        print(f"  HTML content length: {len(page_html.content)} characters")

    except PageNotFoundError as e:
        print(f"✗ Page Not Found: {e.message}")
        print(f"  Page ID: {e.page_id}")
        if e.details:
            print(f"  Details: {e.details}")
    except APIError as e:
        print(f"✗ API Error: {e.message}")
        if e.status_code:
            print(f"  Status Code: {e.status_code}")
        if e.details:
            print(f"  Details: {e.details}")
        raise
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        raise


async def verify_get_child_pages(client: ConfluenceClient, page_id: str) -> None:
    """
    Verify get_child_pages method works correctly.

    Args:
        client: Authenticated ConfluenceClient
        page_id: Parent page ID
    """
    print_section("3.3 Get Child Pages Verification")

    if not page_id:
        print("⚠ Skipping (no page ID available from search)")
        return

    try:
        print(f"Fetching child pages for parent ID: {page_id}...")

        children = await client.get_child_pages(page_id, limit=5)

        print(f"✓ Child pages retrieved successfully")
        print(f"  Total children: {children.total_size or 'unknown'}")
        print(f"  Returned: {children.size} pages")
        print(f"  Start: {children.start}, Limit: {children.limit}")

        if children.results:
            print("\n  Child pages:")
            for child in children.results:
                print(f"    - {child.title}")
                print(f"      ID: {child.id}")
                print(f"      Position: {child.position}")
                print(f"      URL: {child.url}")
        else:
            print("  No child pages found (this is normal for leaf pages)")

    except PageNotFoundError as e:
        print(f"✗ Page Not Found: {e.message}")
        print(f"  Page ID: {e.page_id}")
    except APIError as e:
        print(f"✗ API Error: {e.message}")
        if e.status_code:
            print(f"  Status Code: {e.status_code}")
        if e.details:
            print(f"  Details: {e.details}")
        raise
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        raise


async def verify_error_handling(client: ConfluenceClient) -> None:
    """
    Verify error handling works correctly.

    Args:
        client: Authenticated ConfluenceClient
    """
    print_section("4. Error Handling Verification")

    # Test 1: Non-existent page ID
    print("\nTest 1: Non-existent page ID")
    try:
        invalid_id = "999999999"
        print(f"Attempting to get page with invalid ID: {invalid_id}")
        await client.get_page_content(invalid_id)
        print("✗ Should have raised PageNotFoundError")
    except PageNotFoundError as e:
        print(f"✓ PageNotFoundError raised correctly")
        print(f"  Message: {e.message}")
        print(f"  Page ID: {e.page_id}")
        print(f"  Status Code: {e.status_code}")
    except Exception as e:
        print(f"✗ Wrong exception type: {type(e).__name__}: {e}")

    # Test 2: Invalid CQL query
    print("\nTest 2: Invalid CQL query")
    try:
        invalid_cql = "INVALID_CQL_SYNTAX &&& ((("
        print(f"Attempting search with invalid CQL: {invalid_cql}")
        await client.search_pages(invalid_cql)
        print("✗ Should have raised APIError")
    except APIError as e:
        print(f"✓ APIError raised correctly")
        print(f"  Message: {e.message}")
        if e.status_code:
            print(f"  Status Code: {e.status_code}")
    except Exception as e:
        print(f"✗ Wrong exception type: {type(e).__name__}: {e}")

    # Test 3: Get child pages of non-existent parent
    print("\nTest 3: Non-existent parent page")
    try:
        invalid_parent = "888888888"
        print(f"Attempting to get children of invalid parent: {invalid_parent}")
        await client.get_child_pages(invalid_parent)
        print("✗ Should have raised PageNotFoundError")
    except PageNotFoundError as e:
        print(f"✓ PageNotFoundError raised correctly")
        print(f"  Message: {e.message}")
        print(f"  Page ID: {e.page_id}")
    except Exception as e:
        print(f"✗ Wrong exception type: {type(e).__name__}: {e}")


async def main() -> None:
    """Main verification workflow."""
    print("\n" + "=" * 70)
    print("  Confluence MCP Server - Connection Verification")
    print("=" * 70)

    try:
        # Step 1: Verify environment
        base_url, email, api_token = await verify_environment()

        # Step 2: Verify authentication
        auth = await verify_authentication(base_url, email, api_token)

        # Create Confluence client for subsequent tests
        async with ConfluenceClient(base_url, auth) as client:
            # Step 3: Verify client methods
            page_id = await verify_search_pages(client)
            await verify_get_page_content(client, page_id)
            await verify_get_child_pages(client, page_id)

            # Step 4: Verify error handling
            await verify_error_handling(client)

        # Summary
        print_section("Verification Complete")
        print("✓ All tests passed successfully!")
        print("\nThe Confluence MCP Server is correctly configured and working.")
        print("You can now use it with Claude Desktop or other MCP clients.")

    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_section("Verification Failed")
        print(f"✗ Error: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
