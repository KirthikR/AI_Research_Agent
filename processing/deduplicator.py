"""
LLM-powered content deduplication and relevance filtering.

Uses the LLM to semantically identify duplicate information
and filter out irrelevant content — no hardcoded rules.
"""

import logging

from agent.config import Config
from agent.llm_client import LLMClient
from agent.models import ExtractedContent
from agent.utils import parse_llm_json

logger = logging.getLogger(__name__)

DEDUP_PROMPT = """You are a research content analyst. Your job is to analyze a collection of text excerpts 
gathered from multiple sources about a specific research query, and:

1. IDENTIFY DUPLICATES: Find content items that convey the same core information, even if worded differently.
2. FILTER IRRELEVANT: Remove content that is NOT relevant to answering the research query.
3. RANK BY VALUE: Order the remaining content by how useful it is for answering the query.

RESEARCH QUERY: {query}

CONTENT ITEMS:
{content_items}

Respond with ONLY a valid JSON object (no markdown, no code fences):
{{
    "keep_indices": [list of 0-based indices of content items to KEEP, in order of relevance],
    "removed_reasons": {{
        "index": "reason for removal (duplicate of item X / not relevant because...)"
    }},
    "reasoning": "Brief explanation of your deduplication and filtering decisions"
}}
"""


class ContentDeduplicator:
    """Uses LLM to semantically deduplicate and filter content."""

    def __init__(self):
        self._llm = LLMClient()

    def deduplicate(
        self, contents: list[ExtractedContent], query: str
    ) -> list[ExtractedContent]:
        """
        Use the LLM to deduplicate and filter content items.

        Args:
            contents: List of extracted content to process.
            query: The original research query for relevance filtering.

        Returns:
            Filtered and deduplicated list of ExtractedContent.
        """
        if not contents:
            return []

        # If only a few items, skip LLM dedup (not worth the API call)
        if len(contents) <= 3:
            logger.info("Few content items, skipping LLM deduplication")
            return contents

        try:
            # Build content summary for LLM (truncate each to avoid token limits)
            content_items = ""
            for i, item in enumerate(contents):
                truncated = item.content[:800] if len(item.content) > 800 else item.content
                content_items += (
                    f"\n--- ITEM {i} ---\n"
                    f"Title: {item.title}\n"
                    f"Source: {item.source_type.value}\n"
                    f"Content: {truncated}\n"
                )

            prompt = DEDUP_PROMPT.format(
                query=query,
                content_items=content_items,
            )

            response_text = self._llm.generate(prompt)
            result = parse_llm_json(response_text)
            
            keep_indices = result.get("keep_indices", list(range(len(contents))))
            reasoning = result.get("reasoning", "")

            # Filter to kept items
            filtered = []
            for idx in keep_indices:
                if 0 <= idx < len(contents):
                    filtered.append(contents[idx])

            logger.info(
                f"Deduplication: kept {len(filtered)}/{len(contents)} items. "
                f"Reasoning: {reasoning}"
            )

            return filtered if filtered else contents  # Fallback to all if LLM returns empty

        except Exception as e:
            logger.error(f"Deduplication error: {e}. Returning all content.")
            return contents
