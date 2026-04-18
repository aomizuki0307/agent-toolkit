"""DuckDuckGo HTML search tool (no API key required)."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus

import httpx


def _extract_results(html: str, max_results: int = 5) -> list[dict[str, str]]:
    """Extract search results from DuckDuckGo HTML."""
    results: list[dict[str, str]] = []
    # Match result blocks — DuckDuckGo lite/html
    snippets = re.findall(
        r'<a[^>]+href="([^"]+)"[^>]*class="result__a"[^>]*>(.*?)</a>'
        r'.*?<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
        html,
        re.DOTALL,
    )
    for url, title, snippet in snippets[:max_results]:
        clean_title = re.sub(r"<[^>]+>", "", title).strip()
        clean_snippet = re.sub(r"<[^>]+>", "", snippet).strip()
        results.append({
            "title": clean_title,
            "url": url,
            "snippet": clean_snippet,
        })

    # Fallback: simpler pattern for different page structures
    if not results:
        links = re.findall(
            r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>',
            html,
        )
        seen: set[str] = set()
        for url, title in links:
            if "duckduckgo" in url:
                continue
            clean_title = re.sub(r"<[^>]+>", "", title).strip()
            if clean_title and url not in seen:
                seen.add(url)
                results.append({
                    "title": clean_title,
                    "url": url,
                    "snippet": "",
                })
            if len(results) >= max_results:
                break

    return results


class WebSearch:
    """Search the web using DuckDuckGo HTML (no API key)."""

    def __init__(self, timeout: int = 10) -> None:
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the web using DuckDuckGo. "
            "Returns titles, URLs, and snippets for top results."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)
        if not query:
            return "Error: No query provided"

        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            resp = httpx.get(
                url,
                timeout=self._timeout,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AgentToolkit/1.0)"},
                follow_redirects=True,
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            return f"Error: Search request failed — {e}"

        results = _extract_results(resp.text, max_results)
        if not results:
            return "No results found."

        lines: list[str] = []
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']}")
            lines.append(f"   URL: {r['url']}")
            if r["snippet"]:
                lines.append(f"   {r['snippet']}")
            lines.append("")
        return "\n".join(lines).strip()
