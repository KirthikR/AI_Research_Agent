"""
Agent Controller — the main orchestrator of the research agent.

Implements the full autonomous agent loop:
1. Accept user query
2. LLM selects sources and refines queries
3. Parallel information gathering from selected sources
4. Content extraction and cleaning
5. LLM-based deduplication and relevance filtering
6. LLM-generated structured summary
7. Export and memory storage

All decisions are made by the LLM — no hardcoded rules.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from agent.config import Config
from agent.models import (
    ExtractedContent,
    ResearchReport,
    SearchResult,
    SourceType,
)
from agent.reasoning import ReasoningEngine
from export.pdf_export import PDFExporter
from memory.store import MemoryStore
from processing.deduplicator import ContentDeduplicator
from processing.extractor import ContentExtractor
from processing.summarizer import Summarizer
from tools.arxiv_tool import ArxivTool
from tools.base import BaseTool
from tools.news_search import NewsSearchTool
from tools.web_scraper import WebScraperTool
from tools.web_search import WebSearchTool
from tools.wikipedia_tool import WikipediaTool

logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    Autonomous AI Research Agent.

    Orchestrates the full research pipeline from query to structured report,
    with all decisions made by the LLM reasoning engine.
    """

    def __init__(self, progress_callback: Callable[[str, str], None] | None = None):
        """
        Initialize the research agent.

        Args:
            progress_callback: Optional callback function(stage, message) for
                               reporting progress to the UI.
        """
        Config.validate()

        # Core components
        self._reasoning = ReasoningEngine()
        self._extractor = ContentExtractor()
        self._deduplicator = ContentDeduplicator()
        self._summarizer = Summarizer()
        self._memory = MemoryStore()
        self._pdf_exporter = PDFExporter()

        # Available tools — the LLM will select from these
        self._tools: dict[SourceType, BaseTool] = {
            SourceType.WEB_SEARCH: WebSearchTool(),
            SourceType.WIKIPEDIA: WikipediaTool(),
            SourceType.ARXIV: ArxivTool(),
            SourceType.NEWS: NewsSearchTool(),
        }
        self._scraper = WebScraperTool()

        # Progress callback
        self._progress = progress_callback or (lambda stage, msg: None)

    def research(self, query: str) -> ResearchReport:
        """
        Execute a full autonomous research pipeline for the given query.

        This is the main entry point. The agent will:
        1. Use the LLM to select the best sources for this query
        2. Search all selected sources in parallel
        3. Extract and clean the content
        4. Use the LLM to deduplicate and filter
        5. Use the LLM to generate a structured report
        6. Store the report in memory

        Args:
            query: The user's research query/topic.

        Returns:
            A complete ResearchReport with structured findings.
        """
        logger.info(f"Starting research for: '{query}'")

        # 1. Source selection
        self._progress("source_selection", "🧠 Analyzing query and selecting optimal sources...")
        source_decision = self._reasoning.select_sources(query)
        self._progress(
            "source_selection",
            f"✅ Selected sources: {', '.join(s.value for s in source_decision.selected_sources)}\n"
            f"Reasoning: {source_decision.reasoning}"
        )

        # 2. Information gathering
        self._progress("gathering", "🔍 Gathering information from multiple sources in parallel...")
        all_results = self._gather_parallel(query, source_decision)
        self._progress("gathering", f"✅ Gathered {len(all_results)} results from {len(source_decision.selected_sources)} sources")

        if not all_results:
            self._progress("error", "⚠️ No results found from any source")
            return ResearchReport(
                query=query,
                title=f"Research Report: {query}",
                executive_summary="No results were found from any of the searched sources.",
                key_points=["No information found for this query."],
                agent_reasoning=source_decision.reasoning,
            )

        # 3. Content extraction and cleaning
        self._progress("extraction", "📄 Extracting and cleaning content...")
        extracted = self._extractor.extract(all_results)
        self._progress("extraction", f"✅ Extracted content from {len(extracted)} sources")

        # 4. Semantic deduplication
        self._progress("deduplication", "🔎 Analyzing content for duplicates and relevance...")
        deduplicated = self._deduplicator.deduplicate(extracted, query)
        self._progress("deduplication", f"✅ Kept {len(deduplicated)} relevant, unique content items")

        # 5. Check if we need follow-up queries (if enabled)
        if Config.ENABLE_FOLLOWUP:
            self._progress("followup", "🤔 Evaluating if follow-up research is needed...")
            deduplicated = self._maybe_followup(query, deduplicated, source_decision)
        else:
            self._progress("followup", "⏩ Skipping follow-up check for faster execution")

        # 6. Generate report structure
        self._progress("summarization", "📝 Generating structured research report...")
        report = self._summarizer.generate_report(
            contents=deduplicated,
            query=query,
            agent_reasoning=source_decision.reasoning,
        )
        self._progress("summarization", "✅ Research report generated successfully!")

        # 7. Store results
        self._progress("storage", "💾 Storing research in memory...")
        self._memory.store(report)
        self._progress("storage", "✅ Research stored for future reference")

        logger.info(f"Research complete for: '{query}'")
        return report

    def _gather_parallel(self, query: str, source_decision) -> list[SearchResult]:
        """
        Execute all selected tools in parallel using ThreadPoolExecutor.

        Args:
            query: The original query.
            source_decision: The LLM's source selection decision.

        Returns:
            Combined list of SearchResult from all tools.
        """
        all_results = []

        with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            futures = {}

            for source_type in source_decision.selected_sources:
                tool = self._tools.get(source_type)
                if not tool:
                    continue

                # Use the LLM-refined query for this source, or the original
                refined_query = source_decision.refined_queries.get(
                    source_type.value, query
                )

                future = executor.submit(tool.execute, refined_query)
                futures[future] = source_type

            for future in as_completed(futures):
                source_type = futures[future]
                try:
                    results = future.result(timeout=30)
                    all_results.extend(results)
                    self._progress(
                        "gathering",
                        f"  📥 {source_type.value}: found {len(results)} results"
                    )
                except Exception as e:
                    logger.error(f"Error from {source_type.value}: {e}")
                    self._progress(
                        "gathering",
                        f"  ⚠️ {source_type.value}: error — {e}"
                    )

        return all_results

    def _maybe_followup(
        self, query: str, contents: list[ExtractedContent], source_decision
    ) -> list[ExtractedContent]:
        """
        Ask the LLM if follow-up searches are needed and execute them if so.

        Args:
            query: Original query.
            contents: Current content items.
            source_decision: Original source decision.

        Returns:
            Updated content list (with follow-up results added if needed).
        """
        try:
            # Build summary of current findings
            findings_summary = "\n".join(
                f"- {item.title}: {item.content[:200]}" for item in contents[:10]
            )
            sources_searched = [s.value for s in source_decision.selected_sources]

            followup = self._reasoning.evaluate_followup(
                query, findings_summary, sources_searched
            )

            if followup.get("needs_followup") and followup.get("follow_up_searches"):
                self._progress("followup", "🔄 Performing follow-up searches...")

                source_id_map = {
                    "web_search": SourceType.WEB_SEARCH,
                    "wikipedia": SourceType.WIKIPEDIA,
                    "arxiv": SourceType.ARXIV,
                    "news": SourceType.NEWS,
                }

                for search in followup["follow_up_searches"][:2]:  # Limit follow-ups
                    source_id = search.get("source", "web_search")
                    follow_query = search.get("query", query)
                    source_type = source_id_map.get(source_id, SourceType.WEB_SEARCH)

                    tool = self._tools.get(source_type)
                    if tool:
                        results = tool.execute(follow_query)
                        follow_extracted = self._extractor.extract(results)
                        contents.extend(follow_extracted)
                        self._progress(
                            "followup",
                            f"  📥 Follow-up {source_type.value}: +{len(follow_extracted)} items"
                        )
            else:
                self._progress("followup", "✅ Initial results are sufficient, no follow-up needed")

        except Exception as e:
            logger.error(f"Follow-up error: {e}")
            self._progress("followup", f"⚠️ Follow-up evaluation skipped: {e}")

        return contents

    def export_pdf(self, report: ResearchReport, filename: str | None = None) -> str:
        """Export a report as PDF. Returns the file path."""
        return self._pdf_exporter.export(report, filename)

    def get_history(self, limit: int = 20):
        """Get previous research history."""
        return self._memory.get_history(limit)

    def get_report_by_id(self, record_id: int) -> ResearchReport | None:
        """Retrieve a stored report by ID."""
        return self._memory.get_report_by_id(record_id)

    def search_history(self, query: str):
        """Search through past research."""
        return self._memory.search_history(query)

    def clear_history(self):
        """Clear all stored research history."""
        self._memory.clear_history()
