"""
LLM Reasoning Engine — the autonomous brain of the research agent.

Uses the LLM to make ALL decisions about:
- Which sources to search based on the query
- What refined queries to use for each source
- How to evaluate and prioritize gathered information

NO hardcoded rules — the LLM reasons about everything.
"""

import logging

from agent.config import Config
from agent.llm_client import LLMClient
from agent.models import SourceDecision, SourceType
from agent.utils import parse_llm_json

logger = logging.getLogger(__name__)

# Available tools described for the LLM
TOOL_DESCRIPTIONS = {
    SourceType.WEB_SEARCH: {
        "name": "Web Search",
        "id": "web_search",
        "description": (
            "General-purpose web search engine (DuckDuckGo). Best for broad queries, "
            "how-to guides, recent information, product comparisons, technical documentation, "
            "tutorials, and any topic that needs diverse web sources."
        ),
    },
    SourceType.WIKIPEDIA: {
        "name": "Wikipedia",
        "id": "wikipedia",
        "description": (
            "Encyclopedia search for factual, well-established knowledge. Best for definitions, "
            "historical events, scientific concepts, biographies, geographical information, "
            "and background context on well-known topics."
        ),
    },
    SourceType.ARXIV: {
        "name": "ArXiv",
        "id": "arxiv",
        "description": (
            "Academic preprint repository for scientific and technical research papers. Best for "
            "cutting-edge research, machine learning, AI, physics, mathematics, computer science, "
            "and any topic requiring peer-reviewed or academic sources."
        ),
    },
    SourceType.NEWS: {
        "name": "News Search",
        "id": "news",
        "description": (
            "News article search for current events and recent developments. Best for breaking news, "
            "recent announcements, market updates, political events, industry trends, "
            "and any time-sensitive topic."
        ),
    },
}

SOURCE_SELECTION_PROMPT = """You are an expert research strategist. Given a user's research query, 
your job is to decide WHICH information sources to use and WHAT specific search terms to use for each source.

AVAILABLE SOURCES:
{tool_descriptions}

USER'S RESEARCH QUERY: "{query}"

Think step-by-step:
1. What TYPE of information does this query need? (factual, current events, academic, technical, etc.)
2. Which sources would provide the BEST information for this specific query?
3. What specific search terms should be used for EACH selected source? (These may differ from the original query to get better results.)

Respond with ONLY a valid JSON object (no markdown, no code fences):
{{
    "selected_sources": ["source_id_1", "source_id_2", ...],
    "reasoning": "Your step-by-step reasoning for why you chose these sources",
    "refined_queries": {{
        "source_id_1": "optimized search query for this specific source",
        "source_id_2": "optimized search query for this specific source"
    }}
}}

RULES:
- Select 2-4 sources that are most relevant to the query.
- ALWAYS include "web_search" as a baseline unless the query is purely academic.
- Use source IDs from: web_search, wikipedia, arxiv, news
- Tailor search queries for each source (e.g., Wikipedia needs concise topic names, ArXiv needs technical terms).
"""

FOLLOW_UP_PROMPT = """You are a research strategist analyzing initial research results.
Based on the initial findings, determine if additional searches are needed.

ORIGINAL QUERY: "{query}"

INITIAL FINDINGS SUMMARY:
{findings_summary}

SOURCES ALREADY SEARCHED: {sources_searched}

Should we do any follow-up searches? If yes, suggest specific queries and sources.

Respond with ONLY a valid JSON object (no markdown, no code fences):
{{
    "needs_followup": true/false,
    "reasoning": "Why follow-up is or isn't needed",
    "follow_up_searches": [
        {{
            "source": "source_id",
            "query": "specific follow-up query"
        }}
    ]
}}
"""


class ReasoningEngine:
    """LLM-powered reasoning engine for autonomous source selection and query refinement."""

    def __init__(self):
        self._llm = LLMClient()

    def select_sources(self, query: str) -> SourceDecision:
        """
        Use the LLM to autonomously decide which sources to search
        and generate optimized queries for each source.

        Args:
            query: The user's research query.

        Returns:
            SourceDecision with selected sources and refined queries.
        """
        try:
            # Build tool descriptions for the prompt
            tool_desc_text = ""
            for source_type, info in TOOL_DESCRIPTIONS.items():
                tool_desc_text += f"- **{info['name']}** (id: {info['id']}): {info['description']}\n"

            prompt = SOURCE_SELECTION_PROMPT.format(
                tool_descriptions=tool_desc_text,
                query=query,
            )

            response_text = self._llm.generate(prompt)
            result = parse_llm_json(response_text)

            # Map source IDs back to SourceType enums
            source_id_map = {
                "web_search": SourceType.WEB_SEARCH,
                "wikipedia": SourceType.WIKIPEDIA,
                "arxiv": SourceType.ARXIV,
                "news": SourceType.NEWS,
            }

            selected = []
            for source_id in result.get("selected_sources", ["web_search"]):
                if source_id in source_id_map:
                    selected.append(source_id_map[source_id])

            # Ensure at least one source is selected
            if not selected:
                selected = [SourceType.WEB_SEARCH]

            decision = SourceDecision(
                selected_sources=selected,
                reasoning=result.get("reasoning", ""),
                refined_queries=result.get("refined_queries", {}),
            )

            logger.info(
                f"Source selection: {[s.value for s in decision.selected_sources]}. "
                f"Reasoning: {decision.reasoning}"
            )

            return decision

        except Exception as e:
            logger.error(f"Source selection error: {e}. Defaulting to web search + wikipedia.")
            return SourceDecision(
                selected_sources=[SourceType.WEB_SEARCH, SourceType.WIKIPEDIA],
                reasoning=f"Defaulting due to error: {e}",
                refined_queries={
                    "web_search": query,
                    "wikipedia": query,
                },
            )

    def evaluate_followup(
        self, query: str, findings_summary: str, sources_searched: list[str]
    ) -> dict:
        """
        Determine if follow-up searches are needed based on initial results.

        Args:
            query: Original research query.
            findings_summary: Summary of what was found so far.
            sources_searched: List of source IDs already searched.

        Returns:
            Dict with follow-up decisions.
        """
        try:
            prompt = FOLLOW_UP_PROMPT.format(
                query=query,
                findings_summary=findings_summary[:2000],
                sources_searched=", ".join(sources_searched),
            )

            response_text = self._llm.generate(prompt)
            result = parse_llm_json(response_text)
            
            logger.info(f"Follow-up evaluation: needs_followup={result.get('needs_followup', False)}")
            return result

        except Exception as e:
            logger.error(f"Follow-up evaluation error: {e}")
            return {"needs_followup": False, "reasoning": f"Error: {e}", "follow_up_searches": []}
