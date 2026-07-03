"""
Web scraper tool.
"""

import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from agent.config import Config
from agent.models import SearchResult, SourceType
from tools.base import BaseTool

logger = logging.getLogger(__name__)

# Elements commonly containing non-content
REMOVE_TAGS = [
    "script", "style", "nav", "footer", "header",
    "aside", "form", "iframe", "noscript",
]

REMOVE_CLASSES = [
    "nav", "navbar", "sidebar", "footer", "header", "menu",
    "advertisement", "ad", "cookie", "popup", "modal",
    "social", "share", "comment", "related",
]


class WebScraperTool(BaseTool):
    """Direct URL web scraper for extracting page content."""

    @property
    def name(self) -> str:
        return "Web Scraper"

    @property
    def description(self) -> str:
        return (
            "Fetches and extracts the main text content from a specific URL. "
            "Use this when you have a specific web page URL to scrape, "
            "or when other search tools return URLs that need deeper reading."
        )

    def execute(self, query: str) -> list[SearchResult]:
        """
        Scrape content from a URL.

        Args:
            query: A URL to scrape.

        Returns:
            List with a single SearchResult containing the page content.
        """
        results = []

        # Validate that query looks like a URL
        if not query.startswith(("http://", "https://")):
            logger.warning(f"WebScraper: '{query}' is not a valid URL, skipping")
            return results

        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            response = requests.get(
                query,
                headers=headers,
                timeout=Config.REQUEST_TIMEOUT,
                allow_redirects=True,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Remove non-content elements
            for tag_name in REMOVE_TAGS:
                for tag in soup.find_all(tag_name):
                    tag.decompose()

            # Remove elements with common non-content class names
            for class_name in REMOVE_CLASSES:
                for element in soup.find_all(class_=lambda c: c and class_name in str(c).lower()):
                    element.decompose()

            # Extract title
            title = ""
            if soup.title:
                title = soup.title.get_text(strip=True)

            # Extract main content — try common content containers first
            content = ""
            content_selectors = [
                "article", "main", "[role='main']",
                ".content", ".post-content", ".article-body",
                ".entry-content", "#content", "#main-content",
            ]

            for selector in content_selectors:
                container = soup.select_one(selector)
                if container:
                    content = container.get_text(separator="\n", strip=True)
                    break

            # Fallback: use body
            if not content:
                body = soup.find("body")
                if body:
                    content = body.get_text(separator="\n", strip=True)

            # Clean up excessive whitespace
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            content = "\n".join(lines)

            # Truncate if too long
            if len(content) > Config.MAX_CONTENT_LENGTH:
                content = content[: Config.MAX_CONTENT_LENGTH] + "..."

            domain = urlparse(query).netloc

            results.append(
                SearchResult(
                    title=title or domain,
                    url=query,
                    snippet=content[:300] if content else "",
                    source_type=SourceType.WEB_SCRAPE,
                    raw_content=content,
                )
            )

            logger.info(f"WebScraper: Scraped {len(content)} chars from {domain}")

        except Exception as e:
            logger.error(f"WebScraper error for '{query}': {e}")

        return results
