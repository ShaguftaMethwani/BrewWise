import re
import asyncio
import logging
from typing import Optional, Dict
from urllib.parse import urlparse
import httpx

from brewwise.services.ingestion.scrapers.base import clean_html, RawContent
from brewwise.services.discovery.access_checker import AccessChecker

logger = logging.getLogger(__name__)


def sanitize_for_prompt_safety(text: str) -> str:
    """Neutralizes potential prompt injection patterns in external web content."""
    # List of known adversarial prompt injection phrases
    injection_patterns = [
        r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions?",
        r"(?i)system\s*:\s*you\s+are",
        r"(?i)disregard\s+(all\s+)?(previous|prior)\s+instructions?",
        r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
        r"(?i)new\s+system\s+prompt\s*:",
        r"(?i)stop\s+being\s+a\s+coffee\s+assistant",
    ]

    sanitized = text
    for pattern in injection_patterns:
        sanitized = re.sub(pattern, "[FILTERED_INSTRUCTION]", sanitized)

    return sanitized


class PageFetcher:
    def __init__(
        self,
        timeout: float = 6.0,
        user_agent: str = "BrewWise/1.0 pour-over-crawler",
        access_checker: Optional[AccessChecker] = None
    ):
        self.timeout = timeout
        self.user_agent = user_agent
        self.access_checker = access_checker or AccessChecker(user_agent=user_agent)
        self.domain_semaphores: Dict[str, asyncio.Semaphore] = {}

    def _get_semaphore(self, domain: str) -> asyncio.Semaphore:
        if domain not in self.domain_semaphores:
            self.domain_semaphores[domain] = asyncio.Semaphore(2)  # max 2 concurrent fetches per domain
        return self.domain_semaphores[domain]

    async def fetch(self, url: str) -> Optional[RawContent]:
        """Fetches page content respecting robots.txt, timeouts, and auth-walls."""
        # 1. Check robots.txt compliance
        allowed = await self.access_checker.is_allowed(url)
        if not allowed:
            logger.info(f"Skipping {url}: Disallowed by robots.txt")
            return None

        domain = urlparse(url).netloc
        sem = self._get_semaphore(domain)

        async with sem:
            try:
                headers = {
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8"
                }
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                    resp = await client.get(url)

                    # 2. Check auth wall / paywall
                    if self.access_checker.is_auth_walled(resp.status_code, resp.text):
                        logger.info(f"Skipping {url}: Auth-wall or paywall detected (status {resp.status_code})")
                        return None

                    if resp.status_code != 200:
                        logger.warning(f"Failed to fetch {url}: HTTP {resp.status_code}")
                        return None

                    # 3. Validate content-type
                    content_type = resp.headers.get("content-type", "").lower()
                    if "text/html" not in content_type and "text/plain" not in content_type:
                        logger.info(f"Skipping non-HTML/text content type ({content_type}) for {url}")
                        return None

                    html_text = resp.text
                    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
                    title = title_match.group(1).strip() if title_match else None

                    # Extract author if present
                    author_match = re.search(r'<meta[^>]*name=["\']author["\'][^>]*content=["\'](.*?)["\']', html_text, re.IGNORECASE)
                    author = author_match.group(1).strip() if author_match else None

                    clean_text = clean_html(html_text)
                    sanitized_text = sanitize_for_prompt_safety(clean_text)

                    return RawContent(
                        url=url,
                        title=title,
                        author=author,
                        content=sanitized_text,
                        status_code=resp.status_code
                    )

            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url} (limit: {self.timeout}s)")
                return None
            except Exception as e:
                logger.warning(f"Error fetching {url}: {e}")
                return None
