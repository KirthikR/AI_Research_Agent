"""
ArXiv academic paper search tool.

Searches the ArXiv preprint repository for academic papers.
Best for scientific, mathematical, and technical research queries.
No API key required.
"""

import logging
import socket

import arxiv

from agent.config import Config
from agent.models import SearchResult, SourceType
from tools.base import BaseTool

logger = logging.getLogger(__name__)

# Set default socket timeout to prevent slow academic repository endpoints from hanging the app
socket.setdefaulttimeout(10.0)


class ArxivTool(BaseTool):
    """ArXiv academic paper search tool."""

    @property
    def name(self) -> str:
        return "ArXiv"

    @property
    def description(self) -> str:
        return (
            "Academic preprint repository for scientific and technical papers. "
            "Best for cutting-edge research, machine learning, AI, physics, "
            "mathematics, computer science, and any topic requiring peer-reviewed "
            "or academic sources."
        )

    def execute(self, query: str) -> list[SearchResult]:
        """Search ArXiv for academic papers matching the query."""
        results = []
        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=Config.MAX_RESULTS_PER_TOOL,
                sort_by=arxiv.SortCriterion.Relevance,
            )

            for paper in client.results(search):
                # Build a rich content string from paper metadata
                authors = ", ".join(a.name for a in paper.authors[:5])
                if len(paper.authors) > 5:
                    authors += f" and {len(paper.authors) - 5} others"

                categories = ", ".join(paper.categories)
                published = paper.published.strftime("%Y-%m-%d") if paper.published else "N/A"

                content = (
                    f"Title: {paper.title}\n"
                    f"Authors: {authors}\n"
                    f"Published: {published}\n"
                    f"Categories: {categories}\n"
                    f"Abstract: {paper.summary}\n"
                )

                if len(content) > Config.MAX_CONTENT_LENGTH:
                    content = content[: Config.MAX_CONTENT_LENGTH] + "..."

                results.append(
                    SearchResult(
                        title=paper.title,
                        url=paper.entry_id,
                        snippet=paper.summary[:500],
                        source_type=SourceType.ARXIV,
                        raw_content=content,
                    )
                )

            logger.info(f"ArXiv: Found {len(results)} papers for '{query}'")

        except Exception as e:
            logger.error(f"ArXiv error for '{query}': {e}")

        return results
