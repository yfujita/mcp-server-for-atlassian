"""
HTML to Markdown conversion utilities.

Converts Confluence HTML content (storage format) to Markdown.
This makes content more readable for LLMs and reduces token consumption.

Uses markdownify library with custom handling for Confluence-specific
elements like macros, tables, and code blocks.
"""

import logging
import re
from typing import Match

from markdownify import markdownify as md

from src.exceptions import ConversionError

logger = logging.getLogger(__name__)


class ConfluenceHTMLConverter:
    """
    Converter for Confluence HTML to Markdown.

    Handles Confluence-specific HTML elements and macros,
    providing clean Markdown output suitable for LLM consumption.
    """

    def __init__(self) -> None:
        """Initialize converter with custom settings."""
        # Markdownify options for optimal conversion
        self.md_options = {
            "heading_style": "ATX",  # Use # style headings
            "bullets": "-",  # Use - for unordered lists
            "code_language": "",  # Don't add default language to code blocks
            "strip": ["script", "style"],  # Remove these tags
        }

    def convert(self, html: str) -> str:
        """
        Convert Confluence HTML to Markdown.

        Args:
            html: HTML content in Confluence storage format

        Returns:
            str: Cleaned Markdown content

        Raises:
            ConversionError: If conversion fails

        Example:
            >>> converter = ConfluenceHTMLConverter()
            >>> markdown = converter.convert("<h1>Title</h1><p>Content</p>")
            >>> print(markdown)
            # Title
            Content
        """
        if not html:
            return ""

        try:
            logger.debug("Starting HTML to Markdown conversion")

            # 1. Preprocess HTML to handle Confluence-specific elements
            preprocessed = self._preprocess_html(html)

            # 2. Convert to Markdown using markdownify
            markdown = md(preprocessed, **self.md_options)

            # 3. Post-process Markdown to clean up formatting
            cleaned = self._postprocess_markdown(markdown)

            logger.debug("Conversion completed successfully")
            return cleaned

        except Exception as e:
            logger.error(f"Failed to convert HTML to Markdown: {e}")
            raise ConversionError(
                "Failed to convert content",
                details=f"Conversion error: {type(e).__name__}: {str(e)}",
            ) from e

    def _preprocess_html(self, html: str) -> str:
        """
        Preprocess Confluence HTML before conversion.

        Handles Confluence-specific elements:
        - Macros (code, info, warning, etc.)
        - Structured macros
        - Attachments and images
        - Page links

        Args:
            html: Raw Confluence HTML

        Returns:
            str: Preprocessed HTML
        """
        processed = html

        # Handle Confluence macros
        processed = self._handle_confluence_macros(processed)

        # Handle Confluence links (ac:link elements)
        processed = self._handle_confluence_links(processed)

        # Handle Confluence images (ri:attachment, ac:image)
        processed = self._handle_confluence_images(processed)

        # Remove empty structured macro wrappers
        processed = re.sub(r'<ac:structured-macro[^>]*>\s*</ac:structured-macro>', '', processed)

        return processed

    def _postprocess_markdown(self, markdown: str) -> str:
        """
        Post-process converted Markdown.

        Cleans up formatting issues and normalizes output:
        - Remove excessive blank lines
        - Fix list indentation
        - Normalize heading spacing
        - Clean up code blocks

        Args:
            markdown: Raw Markdown output

        Returns:
            str: Cleaned Markdown
        """
        # Remove more than 2 consecutive blank lines
        cleaned = re.sub(r"\n{3,}", "\n\n", markdown)

        # Remove trailing whitespace from each line
        cleaned = "\n".join(line.rstrip() for line in cleaned.split("\n"))

        # Ensure consistent spacing around headings
        # Add blank line before headings (if not at start)
        cleaned = re.sub(r"([^\n])\n(#{1,6} )", r"\1\n\n\2", cleaned)

        # Ensure blank line after headings
        cleaned = re.sub(r"(#{1,6} .+)\n([^\n#])", r"\1\n\n\2", cleaned)

        # Fix code block spacing
        cleaned = re.sub(r"```\n\n", "```\n", cleaned)
        cleaned = re.sub(r"\n\n```", "\n```", cleaned)

        return cleaned.strip()

    def _extract_macro_parameter(self, html: str, param_name: str) -> str:
        """
        Extract a parameter value from a Confluence macro.

        Args:
            html: HTML content containing the macro
            param_name: Name of the parameter to extract

        Returns:
            str: Parameter value if found, empty string otherwise
        """
        pattern = rf'<ac:parameter ac:name="{param_name}">([^<]+)</ac:parameter>'
        match = re.search(pattern, html)
        return match.group(1) if match else ""

    def _extract_macro_body(self, html: str, body_type: str = "rich-text-body") -> str:
        """
        Extract the body content from a Confluence macro.

        Args:
            html: HTML content containing the macro
            body_type: Type of body to extract (rich-text-body, plain-text-body, etc.)

        Returns:
            str: Body content if found, empty string otherwise
        """
        # Try with CDATA first (common in plain-text-body)
        pattern_cdata = rf'<ac:{body_type}><!\[CDATA\[(.*?)\]\]></ac:{body_type}>'
        match = re.search(pattern_cdata, html, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try without CDATA
        pattern = rf'<ac:{body_type}>(.*?)</ac:{body_type}>'
        match = re.search(pattern, html, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _handle_confluence_macros(self, html: str) -> str:
        """
        Handle Confluence-specific macros.

        Converts Confluence macros to Markdown equivalents or removes them:
        - Code macro -> ```language blocks
        - Info/Warning/Note -> Blockquotes with indicators
        - TOC macro -> Remove (not useful in Markdown)
        - Include macro -> Note about included content

        Args:
            html: HTML with Confluence macros

        Returns:
            str: HTML with macros converted
        """
        processed = html

        # Code macro: <ac:structured-macro ac:name="code">
        # Extract language and content
        def replace_code_macro(match: re.Match) -> str:
            """Replace code macro with markdown code block."""
            full_match = match.group(0)

            # Extract language parameter using helper
            language = self._extract_macro_parameter(full_match, "language")

            # Extract code content using helper
            code_content = self._extract_macro_body(full_match, "plain-text-body")

            return f"\n```{language}\n{code_content}\n```\n"

        processed = re.sub(
            r'<ac:structured-macro ac:name="code"[^>]*>.*?</ac:structured-macro>',
            replace_code_macro,
            processed,
            flags=re.DOTALL
        )

        # Info/Warning/Note macros -> Blockquotes with emoji indicators
        macro_replacements = {
            "info": ("ℹ️ INFO", "info"),
            "warning": ("⚠️ WARNING", "warning"),
            "note": ("📝 NOTE", "note"),
            "tip": ("💡 TIP", "tip"),
        }

        for macro_name, (indicator, _) in macro_replacements.items():

            def replace_panel_macro(match: re.Match, _indicator: str = indicator) -> str:
                """Replace panel/info macros with blockquote."""
                full_match = match.group(0)

                # Extract title parameter using helper
                title = self._extract_macro_parameter(full_match, "title")

                # Extract body content using helper
                body = self._extract_macro_body(full_match, "rich-text-body")

                # Convert body to markdown
                body_md = md(body, **self.md_options) if body else ""

                # Format as blockquote
                header = f"{_indicator}: {title}" if title else _indicator
                quoted = "\n".join(
                    f"> {line}" if line else ">" for line in body_md.split("\n")
                )

                return f"\n> **{header}**\n{quoted}\n"

            processed = re.sub(
                rf'<ac:structured-macro ac:name="{macro_name}"[^>]*>.*?</ac:structured-macro>',
                replace_panel_macro,
                processed,
                flags=re.DOTALL,
            )

        # TOC macro - remove (not useful in plain text)
        processed = re.sub(
            r'<ac:structured-macro ac:name="toc"[^>]*>.*?</ac:structured-macro>',
            "",
            processed,
            flags=re.DOTALL
        )

        # Remove other unhandled macros (keep content if available)
        def extract_macro_content(match: re.Match) -> str:
            """Extract content from unhandled macros."""
            full_match = match.group(0)
            # Use helper to extract rich-text-body
            return self._extract_macro_body(full_match, "rich-text-body")

        processed = re.sub(
            r'<ac:structured-macro[^>]*>.*?</ac:structured-macro>',
            extract_macro_content,
            processed,
            flags=re.DOTALL
        )

        return processed

    def _handle_confluence_links(self, html: str) -> str:
        """
        Handle Confluence link elements.

        Converts <ac:link> elements to standard HTML <a> tags.

        Args:
            html: HTML with Confluence links

        Returns:
            str: HTML with standard links
        """
        # Page links: <ac:link><ri:page ri:content-title="Page Title" /></ac:link>
        def replace_page_link(match: re.Match) -> str:
            """Replace page link with standard anchor."""
            full_match = match.group(0)

            # Extract page title
            title_match = re.search(r'ri:content-title="([^"]+)"', full_match)
            if title_match:
                title = title_match.group(1)
                # Link text might be in link body or use title
                link_text_match = re.search(r'<ac:link[^>]*>(.*?)<ri:page', full_match, re.DOTALL)
                link_text = link_text_match.group(1).strip() if link_text_match else title
                if not link_text or '<' in link_text:
                    link_text = title
                return f'<a href="#{title}">{link_text}</a>'

            return full_match

        processed = re.sub(
            r'<ac:link>.*?<ri:page[^>]+/>.*?</ac:link>',
            replace_page_link,
            html,
            flags=re.DOTALL
        )

        # External links: <ac:link><ri:url ri:value="http://..." /></ac:link>
        def replace_url_link(match: re.Match) -> str:
            """Replace URL link with standard anchor."""
            full_match = match.group(0)

            url_match = re.search(r'ri:value="([^"]+)"', full_match)
            if url_match:
                url = url_match.group(1)
                # Try to extract link text
                link_text_match = re.search(r'<ac:link[^>]*>(.*?)<ri:url', full_match, re.DOTALL)
                link_text = link_text_match.group(1).strip() if link_text_match else url
                if not link_text or '<' in link_text:
                    link_text = url
                return f'<a href="{url}">{link_text}</a>'

            return full_match

        processed = re.sub(
            r'<ac:link>.*?<ri:url[^>]+/>.*?</ac:link>',
            replace_url_link,
            processed,
            flags=re.DOTALL
        )

        return processed

    def _handle_confluence_images(self, html: str) -> str:
        """
        Handle Confluence image elements.

        Converts image attachments to markdown image syntax.

        Args:
            html: HTML with Confluence images

        Returns:
            str: HTML with standard images
        """
        # Image attachment: <ac:image><ri:attachment ri:filename="image.png" /></ac:image>
        def replace_image(match: re.Match) -> str:
            """Replace Confluence image with standard img tag."""
            full_match = match.group(0)

            # Extract filename
            filename_match = re.search(r'ri:filename="([^"]+)"', full_match)
            if filename_match:
                filename = filename_match.group(1)
                # Extract alt text if present
                alt_match = re.search(r'ac:alt="([^"]+)"', full_match)
                alt_text = alt_match.group(1) if alt_match else filename
                return f'<img src="{filename}" alt="{alt_text}" />'

            return full_match

        processed = re.sub(
            r'<ac:image[^>]*>.*?<ri:attachment[^>]+/>.*?</ac:image>',
            replace_image,
            html,
            flags=re.DOTALL
        )

        # URL-based images
        def replace_url_image(match: re.Match) -> str:
            """Replace URL-based image with standard img tag."""
            full_match = match.group(0)

            url_match = re.search(r'ri:value="([^"]+)"', full_match)
            if url_match:
                url = url_match.group(1)
                alt_match = re.search(r'ac:alt="([^"]+)"', full_match)
                alt_text = alt_match.group(1) if alt_match else "image"
                return f'<img src="{url}" alt="{alt_text}" />'

            return full_match

        processed = re.sub(
            r'<ac:image[^>]*>.*?<ri:url[^>]+/>.*?</ac:image>',
            replace_url_image,
            processed,
            flags=re.DOTALL
        )

        return processed


def html_to_markdown(html: str) -> str:
    """
    Convenience function to convert HTML to Markdown.

    Args:
        html: Confluence HTML content

    Returns:
        str: Markdown content

    Raises:
        ConversionError: If conversion fails

    Example:
        >>> markdown = html_to_markdown("<h1>Title</h1>")
        >>> print(markdown)
        # Title
    """
    converter = ConfluenceHTMLConverter()
    return converter.convert(html)
