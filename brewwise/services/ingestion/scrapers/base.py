import re
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel
import httpx


class RawContent(BaseModel):
    url: str
    title: Optional[str] = None
    author: Optional[str] = None
    content: str
    status_code: int = 200


def clean_html(html_text: str) -> str:
    """Strip scripts, styles, navigation, and tags, returning clean text/markdown."""
    # Remove script and style blocks
    cleaned = re.sub(r"<(script|style|nav|header|footer|noscript|svg)[^>]*>.*?</\1>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
    # Replace headers and list items with readable markdown-like format
    cleaned = re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>", r"\n\n# \1\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<li[^>]*>(.*?)</li>", r"\n* \1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\n\1\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<br\s*/?>", r"\n", cleaned, flags=re.IGNORECASE)
    # Strip remaining tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Unescape HTML entities
    import html
    cleaned = html.unescape(cleaned)
    # Normalize excessive whitespace
    lines = [line.strip() for line in cleaned.splitlines()]
    clean_lines = [line for line in lines if line]
    return "\n\n".join(clean_lines)


class ScraperProvider(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> RawContent:
        pass


class HttpScraper(ScraperProvider):
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) BrewWise/1.0 pour-over-recipe-crawler"
        }

    async def fetch(self, url: str) -> RawContent:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers=self.headers) as client:
            resp = await client.get(url)
            resp.raise_for_status()

            html_text = resp.text
            # Extract title tag
            title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else None

            # Extract author if present
            author_match = re.search(r'<meta[^>]*name=["\']author["\'][^>]*content=["\'](.*?)["\']', html_text, re.IGNORECASE)
            author = author_match.group(1).strip() if author_match else None

            clean_text = clean_html(html_text)
            return RawContent(
                url=url,
                title=title,
                author=author,
                content=clean_text,
                status_code=resp.status_code
            )
