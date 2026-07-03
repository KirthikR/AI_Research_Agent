"""
Data models for the AI Research Agent.

Defines structured types using Pydantic for type safety and
serialization across all agent components.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Types of information sources the agent can use."""
    WEB_SEARCH = "web_search"
    WIKIPEDIA = "wikipedia"
    ARXIV = "arxiv"
    NEWS = "news"
    WEB_SCRAPE = "web_scrape"


class SearchResult(BaseModel):
    """A single result from any search tool."""
    title: str = ""
    url: str = ""
    snippet: str = ""
    source_type: SourceType = SourceType.WEB_SEARCH
    raw_content: str = ""
    relevance_score: float = 0.0


class ExtractedContent(BaseModel):
    """Cleaned and extracted content from a source."""
    title: str = ""
    url: str = ""
    source_type: SourceType = SourceType.WEB_SEARCH
    content: str = ""
    key_points: list[str] = Field(default_factory=list)
    is_relevant: bool = True


class SourceDecision(BaseModel):
    """LLM's decision on which sources to use for a query."""
    selected_sources: list[SourceType] = Field(default_factory=list)
    reasoning: str = ""
    refined_queries: dict[str, str] = Field(default_factory=dict)


class ResearchReport(BaseModel):
    """The final structured research report."""
    query: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    sources_used: list[SourceType] = Field(default_factory=list)
    total_sources_consulted: int = 0

    # --- Structured Summary ---
    title: str = ""
    executive_summary: str = ""
    key_points: list[str] = Field(default_factory=list)
    important_findings: list[str] = Field(default_factory=list)
    actionable_insights: list[str] = Field(default_factory=list)
    detailed_analysis: str = ""

    # --- References ---
    references: list[dict] = Field(default_factory=list)

    # --- Metadata ---
    agent_reasoning: str = ""


class MemoryRecord(BaseModel):
    """A stored research record in memory."""
    id: Optional[int] = None
    query: str = ""
    timestamp: str = ""
    sources_used: str = ""
    summary: str = ""
    full_report_json: str = ""
