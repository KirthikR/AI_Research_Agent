"""
Content extractor and cleaner.

Takes raw search results and cleans/normalizes the content
for downstream LLM processing.
"""

import logging
import re

from agent.models import ExtractedContent, SearchResult

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Cleans and normalizes raw content from search results."""

    # Patterns to remove from content
    _NOISE_PATTERNS = [
        r"Cookie\s*(policy|consent|settings).*?\n",
        r"Accept\s*(all)?\s*cookies.*?\n",
        r"Subscribe\s*(to)?\s*(our)?\s*newsletter.*?\n",
        r"Sign\s*up\s*(for|to).*?\n",
        r"Follow\s*us\s*on.*?\n",
        r"Share\s*(this|on).*?\n",
        r"\b(Advertisement|Sponsored|Ad)\b.*?\n",
    ]

    def extract(self, results: list[SearchResult]) -> list[ExtractedContent]:
        """
        Extract and clean content from search results.

        Args:
            results: Raw search results from tools.

        Returns:
            List of cleaned ExtractedContent objects.
        """
        extracted = []
        seen_urls = set()

        for result in results:
            # Skip duplicate URLs
            if result.url in seen_urls:
                continue
            seen_urls.add(result.url)

            # Clean the content
            content = self._clean_content(result.raw_content or result.snippet)

            # Skip results with very little content
            if len(content.strip()) < 50:
                logger.debug(f"Skipping thin content from {result.url}")
                continue

            extracted.append(
                ExtractedContent(
                    title=result.title.strip(),
                    url=result.url,
                    source_type=result.source_type,
                    content=content,
                    is_relevant=True,  # Will be filtered by LLM later
                )
            )

        logger.info(
            f"Extracted {len(extracted)} content items from {len(results)} results"
        )
        return extracted

    def _clean_content(self, text: str) -> str:
        """Remove noise and normalize whitespace."""
        if not text:
            return ""

        cleaned = text

        # Remove common noise patterns
        for pattern in self._NOISE_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        # Normalize whitespace
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r" {2,}", " ", cleaned)

        # Remove very short lines (likely menu items or fragments)
        lines = cleaned.split("\n")
        meaningful_lines = []
        for line in lines:
            stripped = line.strip()
            # Keep lines that are either empty (paragraph breaks) or substantial
            if not stripped or len(stripped) > 20:
                meaningful_lines.append(stripped)

        cleaned = "\n".join(meaningful_lines).strip()

        return cleaned
