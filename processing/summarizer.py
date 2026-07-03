"""
LLM-powered structured summary generator.

Uses the Gemini LLM to synthesize all gathered content into
a structured research report with key points, findings,
actionable insights, and references.
"""

import logging

from agent.config import Config
from agent.llm_client import LLMClient
from agent.models import ExtractedContent, ResearchReport
from agent.utils import parse_llm_json

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """You are an expert research analyst. Synthesize the following information gathered 
from multiple sources into a comprehensive, well-structured research report.

RESEARCH QUERY: {query}

GATHERED INFORMATION:
{gathered_content}

SOURCE REFERENCES:
{references}

Generate a thorough research report. Respond with ONLY a valid JSON object (no markdown, no code fences):
{{
    "title": "A descriptive title for this research report",
    "executive_summary": "A concise 2-3 paragraph executive summary of the entire research",
    "key_points": [
        "Key point 1 — a clear, specific finding",
        "Key point 2 — another important finding",
        "... (provide 5-8 key points)"
    ],
    "important_findings": [
        "Finding 1 — detailed finding with supporting evidence",
        "Finding 2 — another detailed finding",
        "... (provide 4-6 important findings with detail)"
    ],
    "actionable_insights": [
        "Insight 1 — practical recommendation or action item",
        "Insight 2 — another actionable takeaway",
        "... (provide 3-5 actionable insights, or state 'N/A' if not applicable)"
    ],
    "detailed_analysis": "A detailed multi-paragraph analysis covering the topic in depth. Include context, nuances, different perspectives, and connections between findings. This should be the most substantial section."
}}

IMPORTANT RULES:
- Base your report ONLY on the provided information — do NOT hallucinate or invent facts.
- If the gathered information is insufficient, explicitly state what's missing.
- Include specific data points, numbers, or quotes when available.
- NEVER use unescaped double quotes inside the JSON string values. If you need to use quote marks in your summaries or text descriptions, write them as single quotes (') instead.
- Make the report actionable and useful for someone researching this topic.
- Write in clear, professional language.
"""


class Summarizer:
    """LLM-powered research summary generator."""

    def __init__(self):
        self._llm = LLMClient()

    def generate_report(
        self,
        contents: list[ExtractedContent],
        query: str,
        agent_reasoning: str = "",
    ) -> ResearchReport:
        """
        Generate a structured research report from gathered content.

        Args:
            contents: Deduplicated, relevant content items.
            query: The original research query.
            agent_reasoning: The agent's reasoning about source selection.

        Returns:
            A complete ResearchReport.
        """
        if not contents:
            return ResearchReport(
                query=query,
                title=f"Research Report: {query}",
                executive_summary="No relevant information was found for this query.",
                key_points=["No results found from the searched sources."],
                agent_reasoning=agent_reasoning,
            )

        try:
            # Build the gathered content string
            gathered_content = ""
            references = ""
            ref_list = []

            for i, item in enumerate(contents, 1):
                content_text = item.content
                if len(content_text) > 1500:
                    content_text = content_text[:1500] + "..."

                gathered_content += (
                    f"\n=== Source {i}: {item.title} ({item.source_type.value}) ===\n"
                    f"{content_text}\n"
                )

                references += f"[{i}] {item.title} — {item.url} (Source: {item.source_type.value})\n"
                ref_list.append({
                    "index": i,
                    "title": item.title,
                    "url": item.url,
                    "source_type": item.source_type.value,
                })

            prompt = SUMMARY_PROMPT.format(
                query=query,
                gathered_content=gathered_content,
                references=references,
            )

            response_text = self._llm.generate(prompt, model=Config.GROQ_QUALITY_MODEL)
            result = parse_llm_json(response_text)

            # Build the final report
            source_types = list(set(item.source_type for item in contents))

            report = ResearchReport(
                query=query,
                sources_used=source_types,
                total_sources_consulted=len(contents),
                title=result.get("title", f"Research Report: {query}"),
                executive_summary=result.get("executive_summary", ""),
                key_points=result.get("key_points", []),
                important_findings=result.get("important_findings", []),
                actionable_insights=result.get("actionable_insights", []),
                detailed_analysis=result.get("detailed_analysis", ""),
                references=ref_list,
                agent_reasoning=agent_reasoning,
            )

            logger.info(
                f"Generated report with {len(report.key_points)} key points, "
                f"{len(report.important_findings)} findings, "
                f"{len(report.actionable_insights)} insights"
            )

            return report

        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            # Return a basic report with raw content
            return ResearchReport(
                query=query,
                title=f"Research Report: {query}",
                executive_summary=f"Error generating structured summary: {e}",
                key_points=[item.content[:200] for item in contents[:5]],
                references=[
                    {"title": item.title, "url": item.url, "source_type": item.source_type.value}
                    for item in contents
                ],
                agent_reasoning=agent_reasoning,
            )
