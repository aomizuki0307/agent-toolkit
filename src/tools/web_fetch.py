"""Web page fetcher with HTML-to-text conversion."""

from __future__ import annotations

import re
from typing import Any

import httpx


def html_to_text(html: str, max_length: int = 5000) -> str:
    """Convert HTML to plain text by stripping tags."""
    # Remove script and style blocks
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    # Convert common block elements to newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|h[1-6]|li|tr)>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode common entities
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = text.replace("&nbsp;", " ")
    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length] + "\n...[truncated]"
    return text


class WebFetch:
    """Fetch a web page and return its text content."""

    def __init__(self, timeout: int = 15) -> None:
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return (
            "Fetch a web page by URL and return its text content. "
            "HTML is converted to plain text automatically."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL of the web page to fetch",
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum text length (default: 5000)",
                    "default": 5000,
                },
            },
            "required": ["url"],
        }

    def execute(self, **kwargs: Any) -> str:
        url = kwargs.get("url", "")
        max_length = kwargs.get("max_length", 5000)
        if not url:
            return "Error: No URL provided"

        try:
            resp = httpx.get(
                url,
                timeout=self._timeout,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AgentToolkit/1.0)"},
                follow_redirects=True,
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            return f"Error: Fetch failed — {e}"

        return html_to_text(resp.text, max_length)
