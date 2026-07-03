"""
DuckDuckGo web search tool.

Performs general web searches using the DuckDuckGo search engine.
No API key required.
"""

import logging

from ddgs import DDGS

from agent.config import Config
from agent.models import SearchResult, SourceType
from tools.base import BaseTool

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """General-purpose web search using DuckDuckGo."""

    @property
    def name(self) -> str:
        return "Web Search"

    @property
    def description(self) -> str:
        return (
            "General-purpose web search engine. Best for broad queries, "
            "how-to guides, recent information, product comparisons, "
            "technical documentation, and any topic that needs diverse web sources."
        )

    def execute(self, query: str) -> list[SearchResult]:
        """Search the web using DuckDuckGo and return results."""
        results = []
        try:
            ddgs = DDGS()
            search_results = list(
                ddgs.text(
                    query,
                    max_results=Config.MAX_RESULTS_PER_TOOL,
                )
            )

            for item in search_results:
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("href", ""),
                    snippet=item.get("body", ""),
                    source_type=SourceType.WEB_SEARCH,
                    raw_content=item.get("body", ""),
                )
                results.append(result)

            logger.info(f"WebSearch: Found {len(results)} results for '{query}'")

        except Exception as e:
            logger.error(f"WebSearch error for '{query}': {e}")

        return results
