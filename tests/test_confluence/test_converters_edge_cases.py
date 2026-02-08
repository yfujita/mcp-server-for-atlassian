"""
Additional edge case tests for HTML to Markdown converters.

Tests error handling and edge cases in macro processing and link conversion.
"""

import pytest

from src.confluence.converters import ConfluenceHTMLConverter, html_to_markdown
from src.exceptions import ConversionError


class TestConverterErrorHandling:
    """Test suite for converter error handling."""

    def test_convert_raises_conversion_error_on_failure(self) -> None:
        """Test that conversion errors are properly wrapped (lines 78-83)."""
        converter = ConfluenceHTMLConverter()

        # Create a scenario that causes markdownify to fail
        # by patching markdownify to raise an exception
        from src.confluence import converters
        original_md = converters.md

        def failing_md(html, **kwargs):
            raise ValueError("Markdownify failed")

        converters.md = failing_md

        try:
            with pytest.raises(ConversionError) as exc_info:
                converter.convert("<h1>Test</h1>")

            assert "Failed to convert content" in str(exc_info.value)
            assert "ValueError" in exc_info.value.details
        finally:
            converters.md = original_md

    def test_html_to_markdown_function_propagates_error(self) -> None:
        """Test that html_to_markdown function propagates ConversionError."""
        from src.confluence import converters
        original_md = converters.md

        def failing_md(html, **kwargs):
            raise RuntimeError("Conversion failure")

        converters.md = failing_md

        try:
            with pytest.raises(ConversionError):
                html_to_markdown("<p>Test</p>")
        finally:
            converters.md = original_md


class TestMacroExtractionEdgeCases:
    """Test edge cases in macro parameter and body extraction."""

    def test_extract_macro_body_without_cdata(self) -> None:
        """Test macro body extraction when CDATA is not present (lines 277-279)."""
        converter = ConfluenceHTMLConverter()

        # Macro with body but no CDATA
        html = '<ac:rich-text-body><p>Test content</p></ac:rich-text-body>'
        result = converter._extract_macro_body(html, "rich-text-body")
        assert "<p>Test content</p>" in result

    def test_extract_macro_body_empty(self) -> None:
        """Test macro body extraction when body is empty."""
        converter = ConfluenceHTMLConverter()

        html = '<ac:rich-text-body></ac:rich-text-body>'
        result = converter._extract_macro_body(html, "rich-text-body")
        assert result == ""

    def test_extract_macro_parameter_not_found(self) -> None:
        """Test parameter extraction when parameter doesn't exist."""
        converter = ConfluenceHTMLConverter()

        html = '<ac:parameter ac:name="title">Test</ac:parameter>'
        result = converter._extract_macro_parameter(html, "nonexistent")
        assert result == ""


class TestLinkConversionEdgeCases:
    """Test edge cases in Confluence link conversion."""

    def test_page_link_without_title(self) -> None:
        """Test page link when content-title is missing (line 318)."""
        converter = ConfluenceHTMLConverter()

        # Link without content-title attribute
        html = '<ac:link><ri:page /></ac:link>'
        result = converter._handle_confluence_links(html)

        # Should return original HTML when title is missing
        assert '<ac:link>' in result

    def test_page_link_with_complex_link_text(self) -> None:
        """Test page link with nested HTML in link text."""
        converter = ConfluenceHTMLConverter()

        # Link with nested tags in link text (should use title instead)
        html = '<ac:link><strong>Bold</strong><ri:page ri:content-title="Target Page" /></ac:link>'
        result = converter._handle_confluence_links(html)

        # Should use title when link text contains HTML
        assert 'href="#Target Page"' in result
        assert '>Target Page</a>' in result

    def test_url_link_without_value(self) -> None:
        """Test URL link when ri:value is missing (line 342)."""
        converter = ConfluenceHTMLConverter()

        # Link without URL value
        html = '<ac:link><ri:url /></ac:link>'
        result = converter._handle_confluence_links(html)

        # Should return original HTML when URL is missing
        assert '<ac:link>' in result

    def test_url_link_with_complex_link_text(self) -> None:
        """Test URL link with nested HTML in link text."""
        converter = ConfluenceHTMLConverter()

        # Link with nested tags in link text
        html = '<ac:link><em>Italic</em><ri:url ri:value="https://example.com" /></ac:link>'
        result = converter._handle_confluence_links(html)

        # Should use URL when link text contains HTML
        assert 'href="https://example.com"' in result
        assert '>https://example.com</a>' in result


class TestImageConversionEdgeCases:
    """Test edge cases in Confluence image conversion."""

    def test_image_attachment_without_filename(self) -> None:
        """Test image attachment when filename is missing (line 379)."""
        converter = ConfluenceHTMLConverter()

        # Image without filename attribute
        html = '<ac:image><ri:attachment /></ac:image>'
        result = converter._handle_confluence_images(html)

        # Should return original HTML when filename is missing
        assert '<ac:image>' in result

    def test_image_attachment_with_alt_text(self) -> None:
        """Test image attachment with custom alt text."""
        converter = ConfluenceHTMLConverter()

        html = '<ac:image ac:alt="Custom alt text"><ri:attachment ri:filename="image.png" /></ac:image>'
        result = converter._handle_confluence_images(html)

        assert 'src="image.png"' in result
        assert 'alt="Custom alt text"' in result

    def test_url_image_without_value(self) -> None:
        """Test URL-based image when ri:value is missing (line 400)."""
        converter = ConfluenceHTMLConverter()

        # Image without URL value
        html = '<ac:image><ri:url /></ac:image>'
        result = converter._handle_confluence_images(html)

        # Should return original HTML when URL is missing
        assert '<ac:image>' in result

    def test_url_image_with_alt_text(self) -> None:
        """Test URL-based image with custom alt text."""
        converter = ConfluenceHTMLConverter()

        html = '<ac:image ac:alt="External image"><ri:url ri:value="https://example.com/image.jpg" /></ac:image>'
        result = converter._handle_confluence_images(html)

        assert 'src="https://example.com/image.jpg"' in result
        assert 'alt="External image"' in result

    def test_url_image_without_alt_text(self) -> None:
        """Test URL-based image without alt text uses default."""
        converter = ConfluenceHTMLConverter()

        html = '<ac:image><ri:url ri:value="https://example.com/image.jpg" /></ac:image>'
        result = converter._handle_confluence_images(html)

        assert 'src="https://example.com/image.jpg"' in result
        assert 'alt="image"' in result


class TestComplexMacroHandling:
    """Test complex macro scenarios."""

    def test_unhandled_macro_without_body(self) -> None:
        """Test unhandled macro without rich-text-body."""
        converter = ConfluenceHTMLConverter()

        # Macro without body content
        html = '<ac:structured-macro ac:name="unknown"><ac:parameter ac:name="param">value</ac:parameter></ac:structured-macro>'
        result = converter._handle_confluence_macros(html)

        # Should extract empty string for missing body
        assert result == ""

    def test_nested_macros(self) -> None:
        """Test handling of nested macros."""
        converter = ConfluenceHTMLConverter()

        # Info macro with code inside
        html = '''
        <ac:structured-macro ac:name="info">
            <ac:rich-text-body>
                <ac:structured-macro ac:name="code">
                    <ac:parameter ac:name="language">python</ac:parameter>
                    <ac:plain-text-body><![CDATA[print("nested")]]></ac:plain-text-body>
                </ac:structured-macro>
            </ac:rich-text-body>
        </ac:structured-macro>
        '''
        result = converter.convert(html)

        # Should handle both macros
        assert "INFO" in result
        assert "python" in result
        assert "nested" in result
