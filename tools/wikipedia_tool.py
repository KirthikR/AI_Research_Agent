"""
Wikipedia search tool.

Queries the Wikipedia API for encyclopedic information
on any topic. No API key required.
Includes automatic fallback to DuckDuckGo search restricted to Wikipedia
to prevent rate limit stalls and handle title mismatches.
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
        """Search Wikipedia and return structured results with automatic fallback."""
        results = []
        try:
            # Attempt to retrieve target page summary directly (fast path)
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
                logger.info(f"Wikipedia API: Found exact match for '{query}'")

        except Exception as e:
            logger.debug(f"Wikipedia API request bypassed (timeout or rate limit): {e}")

        # If no results found (due to API rate limit 429, timeout, or title mismatch),
        # execute self-healing fallback via Web Search restricted to Wikipedia.
        if not results:
            try:
                logger.info(f"Wikipedia: Bypassing to search-fallback for '{query}'")
                from tools.web_search import WebSearchTool
                ddg_search = WebSearchTool()
                
                # Search DDG restricted to Wikipedia
                search_query = f"site:en.wikipedia.org {query}"
                ddg_results = ddg_search.execute(search_query)
                
                for item in ddg_results:
                    item.source_type = SourceType.WIKIPEDIA
                    results.append(item)
                    
                logger.info(f"Wikipedia Fallback: Found {len(results)} results via search index")
            except Exception as fe:
                logger.error(f"Wikipedia search-fallback failed: {fe}")

        return results
