"""
DuckDuckGo news search tool.

Searches for recent news articles using DuckDuckGo's news search.
Best for current events, breaking news, and trending topics.
No API key required.
"""

import logging

from ddgs import DDGS

from agent.config import Config
from agent.models import SearchResult, SourceType
from tools.base import BaseTool

logger = logging.getLogger(__name__)


class NewsSearchTool(BaseTool):
    """News search using DuckDuckGo News."""

    @property
    def name(self) -> str:
        return "News Search"

    @property
    def description(self) -> str:
        return (
            "News article search for current events and recent developments. "
            "Best for breaking news, recent announcements, market updates, "
            "political events, industry trends, and any time-sensitive topic."
        )

    def execute(self, query: str) -> list[SearchResult]:
        """Search for recent news articles matching the query."""
        results = []
        try:
            ddgs = DDGS()
            news_results = list(
                ddgs.news(
                    query,
                    max_results=Config.MAX_RESULTS_PER_TOOL,
                )
            )

            for item in news_results:
                content = (
                    f"Source: {item.get('source', 'Unknown')}\n"
                    f"Date: {item.get('date', 'Unknown')}\n"
                    f"Title: {item.get('title', '')}\n"
                    f"Summary: {item.get('body', '')}\n"
                )

                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("body", ""),
                        source_type=SourceType.NEWS,
                        raw_content=content,
                    )
                )

            logger.info(f"NewsSearch: Found {len(results)} articles for '{query}'")

        except Exception as e:
            logger.error(f"NewsSearch error for '{query}': {e}")

        return results
