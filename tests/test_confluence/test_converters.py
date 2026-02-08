"""
Tests for HTML to Markdown conversion.

Tests the ConfluenceHTMLConverter and various Confluence-specific
HTML elements (macros, links, images).
"""

import pytest

from src.confluence.converters import ConfluenceHTMLConverter, html_to_markdown
from src.exceptions import ConversionError


class TestConfluenceHTMLConverter:
    """Tests for ConfluenceHTMLConverter class."""

    def test_basic_html_conversion(self) -> None:
        """Test basic HTML to Markdown conversion."""
        converter = ConfluenceHTMLConverter()

        html = "<h1>Title</h1><p>This is a paragraph.</p>"
        markdown = converter.convert(html)

        assert "# Title" in markdown
        assert "This is a paragraph." in markdown

    def test_empty_html(self) -> None:
        """Test conversion of empty HTML."""
        converter = ConfluenceHTMLConverter()

        assert converter.convert("") == ""
        assert converter.convert("   ") == ""

    def test_headings_conversion(self) -> None:
        """Test heading conversion (ATX style)."""
        converter = ConfluenceHTMLConverter()

        html = """
        <h1>Heading 1</h1>
        <h2>Heading 2</h2>
        <h3>Heading 3</h3>
        """
        markdown = converter.convert(html)

        assert "# Heading 1" in markdown
        assert "## Heading 2" in markdown
        assert "### Heading 3" in markdown

    def test_lists_conversion(self) -> None:
        """Test list conversion."""
        converter = ConfluenceHTMLConverter()

        html = """
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>
        """
        markdown = converter.convert(html)

        assert "- Item 1" in markdown
        assert "- Item 2" in markdown
        assert "- Item 3" in markdown

    def test_code_blocks_conversion(self) -> None:
        """Test code block conversion."""
        converter = ConfluenceHTMLConverter()

        html = """
        <pre><code>def hello():
    print("Hello, World!")</code></pre>
        """
        markdown = converter.convert(html)

        assert "```" in markdown
        assert 'print("Hello, World!")' in markdown

    def test_links_conversion(self) -> None:
        """Test link conversion."""
        converter = ConfluenceHTMLConverter()

        html = '<p>Visit <a href="https://example.com">Example</a></p>'
        markdown = converter.convert(html)

        assert "[Example](https://example.com)" in markdown

    def test_confluence_code_macro(self) -> None:
        """Test Confluence code macro conversion."""
        converter = ConfluenceHTMLConverter()

        html = """
        <ac:structured-macro ac:name="code">
            <ac:parameter ac:name="language">python</ac:parameter>
            <ac:plain-text-body><![CDATA[def hello():
    print("Hello")]]></ac:plain-text-body>
        </ac:structured-macro>
        """
        markdown = converter.convert(html)

        assert "```python" in markdown
        assert 'print("Hello")' in markdown

    def test_confluence_code_macro_without_language(self) -> None:
        """Test Confluence code macro without language parameter."""
        converter = ConfluenceHTMLConverter()

        html = """
        <ac:structured-macro ac:name="code">
            <ac:plain-text-body><![CDATA[code content]]></ac:plain-text-body>
        </ac:structured-macro>
        """
        markdown = converter.convert(html)

        assert "```" in markdown
        assert "code content" in markdown

    def test_confluence_info_macro(self) -> None:
        """Test Confluence info macro conversion."""
        converter = ConfluenceHTMLConverter()

        html = """
        <ac:structured-macro ac:name="info">
            <ac:parameter ac:name="title">Important</ac:parameter>
            <ac:rich-text-body><p>This is important information.</p></ac:rich-text-body>
        </ac:structured-macro>
        """
        markdown = converter.convert(html)

        assert "INFO" in markdown
        assert "Important" in markdown
        assert ">" in markdown  # Blockquote indicator

    def test_confluence_warning_macro(self) -> None:
        """Test Confluence warning macro conversion."""
        converter = ConfluenceHTMLConverter()

        html = """
        <ac:structured-macro ac:name="warning">
            <ac:rich-text-body><p>Be careful!</p></ac:rich-text-body>
        </ac:structured-macro>
        """
        markdown = converter.convert(html)

        assert "WARNING" in markdown
        assert ">" in markdown

    def test_confluence_toc_macro_removal(self) -> None:
        """Test that TOC macro is removed."""
        converter = ConfluenceHTMLConverter()

        html = """
        <p>Content before</p>
        <ac:structured-macro ac:name="toc"></ac:structured-macro>
        <p>Content after</p>
        """
        markdown = converter.convert(html)

        assert "Content before" in markdown
        assert "Content after" in markdown
        # TOC should not appear in output

    def test_confluence_page_link(self) -> None:
        """Test Confluence page link conversion."""
        converter = ConfluenceHTMLConverter()

        html = """
        <ac:link><ri:page ri:content-title="Other Page" /></ac:link>
        """
        markdown = converter.convert(html)

        # Should be converted to a link
        assert "Other Page" in markdown

    def test_confluence_url_link(self) -> None:
        """Test Confluence URL link conversion."""
        converter = ConfluenceHTMLConverter()

        html = """
        <ac:link><ri:url ri:value="https://example.com" /></ac:link>
        """
        markdown = converter.convert(html)

        assert "https://example.com" in markdown

    def test_confluence_image_attachment(self) -> None:
        """Test Confluence image attachment conversion."""
        converter = ConfluenceHTMLConverter()

        html = """
        <ac:image><ri:attachment ri:filename="screenshot.png" /></ac:image>
        """
        markdown = converter.convert(html)

        assert "screenshot.png" in markdown
        assert "!" in markdown  # Markdown image indicator

    def test_confluence_image_url(self) -> None:
        """Test Confluence URL image conversion."""
        converter = ConfluenceHTMLConverter()

        html = """
        <ac:image ac:alt="Example Image">
            <ri:url ri:value="https://example.com/image.png" />
        </ac:image>
        """
        markdown = converter.convert(html)

        assert "https://example.com/image.png" in markdown

    def test_postprocess_removes_excess_blank_lines(self) -> None:
        """Test that post-processing removes excess blank lines."""
        converter = ConfluenceHTMLConverter()

        # Markdown with many blank lines
        markdown_input = "Line 1\n\n\n\n\nLine 2"
        processed = converter._postprocess_markdown(markdown_input)

        # Should have at most 2 consecutive newlines
        assert "\n\n\n" not in processed

    def test_postprocess_removes_trailing_whitespace(self) -> None:
        """Test that post-processing removes trailing whitespace."""
        converter = ConfluenceHTMLConverter()

        markdown_input = "Line 1   \nLine 2  \n"
        processed = converter._postprocess_markdown(markdown_input)

        assert "Line 1\n" in processed
        assert "   \n" not in processed

    def test_complex_confluence_page(self) -> None:
        """Test conversion of a complex Confluence page."""
        converter = ConfluenceHTMLConverter()

        html = """
        <h1>API Documentation</h1>
        <p>This page describes our API.</p>

        <ac:structured-macro ac:name="info">
            <ac:parameter ac:name="title">Note</ac:parameter>
            <ac:rich-text-body><p>This API is version 2.0</p></ac:rich-text-body>
        </ac:structured-macro>

        <h2>Authentication</h2>
        <p>Use API tokens for authentication.</p>

        <ac:structured-macro ac:name="code">
            <ac:parameter ac:name="language">python</ac:parameter>
            <ac:plain-text-body><![CDATA[import requests
headers = {"Authorization": "Bearer token"}]]></ac:plain-text-body>
        </ac:structured-macro>

        <h2>Endpoints</h2>
        <ul>
            <li>GET /api/users</li>
            <li>POST /api/users</li>
        </ul>
        """
        markdown = converter.convert(html)

        # Verify key elements are present
        assert "# API Documentation" in markdown
        assert "## Authentication" in markdown
        assert "INFO" in markdown
        assert "```python" in markdown
        assert "import requests" in markdown
        assert "- GET /api/users" in markdown


class TestHtmlToMarkdownFunction:
    """Tests for html_to_markdown convenience function."""

    def test_html_to_markdown_basic(self) -> None:
        """Test basic usage of html_to_markdown function."""
        html = "<h1>Title</h1><p>Content</p>"
        markdown = html_to_markdown(html)

        assert "# Title" in markdown
        assert "Content" in markdown

    def test_html_to_markdown_with_confluence_elements(self) -> None:
        """Test html_to_markdown with Confluence elements."""
        html = """
        <ac:structured-macro ac:name="code">
            <ac:parameter ac:name="language">javascript</ac:parameter>
            <ac:plain-text-body><![CDATA[console.log("Hello");]]></ac:plain-text-body>
        </ac:structured-macro>
        """
        markdown = html_to_markdown(html)

        assert "```javascript" in markdown
        assert 'console.log("Hello")' in markdown
