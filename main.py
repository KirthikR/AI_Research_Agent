import argparse
import logging
import sys
import os

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.controller import ResearchAgent
from agent.config import Config


def setup_logging(verbose: bool = False):
    """Configure logging for the CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def print_progress(stage: str, message: str):
    """Print progress updates to the console."""
    print(f"  {message}")


def print_report(report):
    """Print a formatted research report to the console."""
    print("\n" + "=" * 80)
    print(f"  {report.title}")
    print("=" * 80)

    print(f"\n📋 Query: {report.query}")
    print(f"📅 Generated: {report.timestamp}")
    sources = ", ".join(s.value for s in report.sources_used)
    print(f"🔗 Sources: {sources}")
    print(f"📊 Total Sources Consulted: {report.total_sources_consulted}")

    if report.executive_summary:
        print(f"\n{'─' * 60}")
        print("📖 EXECUTIVE SUMMARY")
        print(f"{'─' * 60}")
        print(report.executive_summary)

    if report.key_points:
        print(f"\n{'─' * 60}")
        print("🔑 KEY POINTS")
        print(f"{'─' * 60}")
        for i, point in enumerate(report.key_points, 1):
            print(f"  {i}. {point}")

    if report.important_findings:
        print(f"\n{'─' * 60}")
        print("🔬 IMPORTANT FINDINGS")
        print(f"{'─' * 60}")
        for i, finding in enumerate(report.important_findings, 1):
            print(f"\n  Finding {i}:")
            print(f"  {finding}")

    if report.detailed_analysis:
        print(f"\n{'─' * 60}")
        print("📊 DETAILED ANALYSIS")
        print(f"{'─' * 60}")
        print(report.detailed_analysis)

    if report.actionable_insights:
        print(f"\n{'─' * 60}")
        print("💡 ACTIONABLE INSIGHTS")
        print(f"{'─' * 60}")
        for i, insight in enumerate(report.actionable_insights, 1):
            print(f"  {i}. {insight}")

    if report.references:
        print(f"\n{'─' * 60}")
        print("📚 REFERENCES")
        print(f"{'─' * 60}")
        for ref in report.references:
            idx = ref.get("index", "")
            title = ref.get("title", "")
            url = ref.get("url", "")
            src = ref.get("source_type", "")
            print(f"  [{idx}] {title}")
            print(f"      {url} ({src})")

    if report.agent_reasoning:
        print(f"\n{'─' * 60}")
        print("🧠 AGENT REASONING")
        print(f"{'─' * 60}")
        print(f"  {report.agent_reasoning}")

    print("\n" + "=" * 80)


def run_interactive():
    """Run the agent in interactive mode."""
    print("\n" + "=" * 60)
    print("  🤖 Autonomous AI Research Agent")
    print("  Type your research query and press Enter.")
    print("  Commands: 'history', 'export', 'quit'")
    print("=" * 60 + "\n")

    agent = ResearchAgent(progress_callback=print_progress)
    last_report = None

    while True:
        try:
            user_input = input("\n🔍 Research Query > ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("👋 Goodbye!")
                break

            if user_input.lower() == "history":
                history = agent.get_history(10)
                if not history:
                    print("  No previous searches found.")
                else:
                    print("\n📜 Previous Searches:")
                    for record in history:
                        print(f"  [{record.id}] {record.timestamp[:16]} — {record.query}")
                        print(f"      Sources: {record.sources_used}")
                        print(f"      Summary: {record.summary[:100]}...")
                continue

            if user_input.lower().startswith("export"):
                if not last_report:
                    print("  ⚠️ No report to export. Run a research query first.")
                    continue

                path = agent.export_pdf(last_report)
                print(f"  📄 PDF exported: {path}")
                continue

            # Run research
            print(f"\n🚀 Starting research on: \"{user_input}\"\n")
            last_report = agent.research(user_input)
            print_report(last_report)

            # Auto-export PDF only
            pdf_path = agent.export_pdf(last_report)
            print(f"\n📄 PDF report saved: {pdf_path}")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logging.exception("CLI error")


def run_single_query(query: str, export_format: str = "pdf"):
    """Run a single research query and export."""
    agent = ResearchAgent(progress_callback=print_progress)

    print(f"\n🚀 Starting research on: \"{query}\"\n")
    report = agent.research(query)
    print_report(report)

    if export_format in ("pdf", "both"):
        pdf_path = agent.export_pdf(report)
        print(f"\n📄 PDF report saved: {pdf_path}")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="🤖 Autonomous AI Research Agent — Gather, analyze, and summarize information."
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Research query to investigate. Omit for interactive mode.",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode with continuous prompting.",
    )
    parser.add_argument(
        "--export", "-e",
        choices=["pdf"],
        default="pdf",
        help="Export format (default: pdf)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug logging.",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.interactive or not args.query:
        run_interactive()
    else:
        run_single_query(args.query, args.export)


if __name__ == "__main__":
    main()
