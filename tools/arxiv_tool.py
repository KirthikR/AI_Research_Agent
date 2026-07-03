"""
ArXiv academic paper search tool.

Queries the ArXiv preprint API directly using XML parsing.
Best for scientific, mathematical, and technical research queries.
No heavy third-party library wrappers, ensuring robust timeouts.
"""

import logging
import urllib.parse
import xml.etree.ElementTree as ET

import requests

from agent.config import Config
from agent.models import SearchResult, SourceType
from tools.base import BaseTool

logger = logging.getLogger(__name__)


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
        """Search ArXiv using native API request and XML parsing."""
        results = []
        try:
            # URL encode search query
            safe_query = urllib.parse.quote(query)
            url = (
                f"https://export.arxiv.org/api/query?"
                f"search_query=all:{safe_query}&"
                f"max_results={Config.MAX_RESULTS_PER_TOOL}&"
                f"sortBy=relevance&"
                f"sortOrder=descending"
            )

            # Strict 5-second timeout to prevent slowing down pipeline runs
            response = requests.get(url, timeout=5.0)
            
            if response.status_code != 200:
                logger.warning(f"ArXiv API returned status {response.status_code}")
                return results

            # Parse Atom XML feed
            root = ET.fromstring(response.content)
            
            # Atom namespace
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            
            entries = root.findall("atom:entry", ns)
            for entry in entries:
                title_elem = entry.find("atom:title", ns)
                summary_elem = entry.find("atom:summary", ns)
                id_elem = entry.find("atom:id", ns)
                pub_elem = entry.find("atom:published", ns)
                
                title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else "Untitled"
                summary = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else ""
                entry_id = id_elem.text.strip() if id_elem is not None else ""
                published = pub_elem.text.strip()[:10] if pub_elem is not None else "N/A"
                
                # Extract author names
                authors = []
                for author_elem in entry.findall("atom:author", ns):
                    name_elem = author_elem.find("atom:name", ns)
                    if name_elem is not None:
                        authors.append(name_elem.text.strip())
                        
                authors_str = ", ".join(authors[:5])
                if len(authors) > 5:
                    authors_str += f" and {len(authors) - 5} others"

                content = (
                    f"Title: {title}\n"
                    f"Authors: {authors_str}\n"
                    f"Published: {published}\n"
                    f"Abstract: {summary}\n"
                )

                if len(content) > Config.MAX_CONTENT_LENGTH:
                    content = content[: Config.MAX_CONTENT_LENGTH] + "..."

                results.append(
                    SearchResult(
                        title=title,
                        url=entry_id,
                        snippet=summary[:500],
                        source_type=SourceType.ARXIV,
                        raw_content=content,
                    )
                )

            logger.info(f"ArXiv API: Found {len(results)} papers for '{query}'")

        except Exception as e:
            logger.warning(f"ArXiv connection bypassed (timeout or API load): {e}")

        return results
