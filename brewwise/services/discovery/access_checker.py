import logging
import urllib.robotparser
from typing import Dict
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)


class AccessChecker:
    def __init__(self, user_agent: str = "BrewWise/1.0 pour-over-crawler"):
        self.user_agent = user_agent
        self.robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}

    async def is_allowed(self, url: str) -> bool:
        """Checks if URL path is allowed by robots.txt for our user agent."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            if not domain:
                return True

            scheme = parsed.scheme or "https"
            robots_url = f"{scheme}://{domain}/robots.txt"

            if domain not in self.robots_cache:
                rp = urllib.robotparser.RobotFileParser()
                try:
                    async with httpx.AsyncClient(timeout=4.0) as client:
                        resp = await client.get(robots_url, headers={"User-Agent": self.user_agent})
                        if resp.status_code == 200:
                            rp.parse(resp.text.splitlines())
                        else:
                            # If no robots.txt or 404, assume allowed
                            rp.allow_all = True
                except Exception as e:
                    logger.debug(f"Could not fetch robots.txt for {domain}: {e}")
                    rp.allow_all = True

                self.robots_cache[domain] = rp

            rp = self.robots_cache[domain]
            return rp.can_fetch(self.user_agent, url)
        except Exception as e:
            logger.debug(f"robots.txt check failed for {url}, defaulting to allowed: {e}")
            return True

    @staticmethod
    def is_auth_walled(status_code: int, html_or_text: str) -> bool:
        """Detects if response is blocked by an auth-wall, login requirement, or paywall."""
        if status_code in (401, 403, 407):
            return True

        lower = html_or_text.lower()
        paywall_signatures = [
            "sign in to read the full",
            "log in or subscribe to read",
            "create a free account to access",
            "you have reached your free article limit",
            "this content is exclusive to subscribers",
            "please log in to view this recipe",
            "paywall-overlay",
            "id=\"login-form\"",
            "class=\"subscriber-only\"",
        ]

        return any(sig in lower for sig in paywall_signatures)
