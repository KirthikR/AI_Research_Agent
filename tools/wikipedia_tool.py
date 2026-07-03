"""
Wikipedia search tool.

Queries the Wikipedia API for encyclopedic information
on any topic. No API key required.
"""

import logging

import wikipediaapi

from agent.config import Config
from agent.models import SearchResult, SourceType
from tools.base import BaseTool

logger = logging.getLogger(__name__)


class WikipediaTool(BaseTool):
    """Wikipedia encyclopedia search tool."""

    def __init__(self):
        # Configure native wikipediaapi parameters:
        # max_retries=0 to avoid stalling on rate limits
        # timeout=2.0 (forwarded to httpx.Client) to prevent hangs
        self._wiki = wikipediaapi.Wikipedia(
            user_agent="AIResearchAgent/1.0 (Educational Project)",
            language="en",
            max_retries=0,
            timeout=2.0,
        )

    @property
    def name(self) -> str:
        return "Wikipedia"

    @property
    def description(self) -> str:
        return (
            "Encyclopedia search for factual, well-established knowledge. "
            "Best for definitions, historical events, scientific concepts, "
            "biographies, geographical information, and background context "
            "on well-known topics."
        )

    def execute(self, query: str) -> list[SearchResult]:
        """Search Wikipedia and return structured results."""
        results = []
        try:
            # Fetch the main page summary (avoids nested link crawl delays)
            page = self._wiki.page(query)
            if page.exists():
                content = page.summary
                if len(content) > Config.MAX_CONTENT_LENGTH:
                    content = content[: Config.MAX_CONTENT_LENGTH] + "..."

                results.append(
                    SearchResult(
                        title=page.title,
                        url=page.fullurl,
                        snippet=page.summary[:500],
                        source_type=SourceType.WIKIPEDIA,
                        raw_content=content,
                    )
                )

            logger.info(f"Wikipedia: Found {len(results)} results for '{query}'")

        except Exception as e:
            logger.warning(f"Wikipedia connection bypassed (timeout or rate limit): {e}")

        return results
