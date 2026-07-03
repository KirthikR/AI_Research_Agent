"""
PDF export module.

Exports a ResearchReport as a professionally formatted PDF file
using fpdf2. Safe for all unicode and smart punctuation markers.
Designed with premium formatting rules (clean margins, grid spacing,
styled header rules, and a dedicated executive callout container).
"""

import logging
import os
from datetime import datetime

from fpdf import FPDF

from agent.config import Config
from agent.models import ResearchReport

logger = logging.getLogger(__name__)


def to_latin1(text: str) -> str:
    """
    Cleans a string to make it safe for Latin-1 rendering in standard FPDF fonts.
    Replaces common smart punctuation marks with ASCII equivalents rather than replacing with '?'.
    """
    if not text:
        return ""
        
    replacements = {
        "\u2018": "'", "\u2019": "'",  # Smart single quotes
        "\u201c": '"', "\u201d": '"',  # Smart double quotes
        "\u2013": "-", "\u2014": "-",  # En and em dashes
        "\u2022": "*",                 # Bullet points
        "\u2212": "-",                 # Minus sign
    }
    
    cleaned = text
    for unicode_char, ascii_char in replacements.items():
        cleaned = cleaned.replace(unicode_char, ascii_char)
        
    return cleaned.encode("latin-1", errors="replace").decode("latin-1")


class ResearchPDF(FPDF):
    """Custom PDF class with elegant header, footer, and brand accent lines."""

    def header(self):
        # Top margin accent line (brand color)
        self.set_fill_color(30, 58, 138)  # Deep Navy
        self.rect(10, 8, 190, 1.5, "F")
        
        self.ln(2)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(100, 116, 139)  # Slate Grey
        self.cell(0, 10, to_latin1("KIRTHIK AI RESEARCH AGENT - SUMMARY"), align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        
        # Aligned footer layout
        self.cell(100, 10, to_latin1("Confidential - Kirthik AI Research Agent"), align="L")
        self.cell(90, 10, f"Page {self.page_no()}/{{nb}}", align="R")


class PDFExporter:
    """Exports research reports as clean corporate article PDFs."""

    def export(self, report: ResearchReport, filename: str | None = None) -> str:
        """
        Export a ResearchReport to an article-style PDF file.
        """
        output_dir = Config.get_output_dir()

        if not filename:
            safe_query = "".join(
                c if c.isalnum() or c in " -_" else "_"
                for c in report.query[:50]
            ).strip().replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_{safe_query}_{timestamp}.pdf"

        filepath = os.path.join(output_dir, filename)

        pdf = ResearchPDF(orientation="P", unit="mm", format="A4")
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=True, margin=20)
        
        # Set margins (20mm left/right for corporate format)
        pdf.set_margins(20, 20, 20)
        pdf.add_page()

        # Document Header Section
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(30, 58, 138)  # Deep Navy Accent
        pdf.multi_cell(0, 10, to_latin1(report.title), align="L")
        pdf.ln(4)

        # Metadata Subheader Bar
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(100, 116, 139)  # Slate Grey
        pdf.cell(0, 5, to_latin1(f"RESEARCH TOPIC: {report.query.upper()}"), new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("Helvetica", "", 8)
        sources_str = ", ".join(s.value.upper() for s in report.sources_used)
        pdf.cell(0, 5, to_latin1(f"DATE GENERATED: {report.timestamp[:16].replace('T', ' ')}  |  SOURCES USED: {sources_str}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        # Thick separator line
        pdf.set_draw_color(226, 232, 240)  # Light border color
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(8)

        # Executive Summary Box Callout
        if report.executive_summary:
            # Styled container card for the summary
            pdf.set_fill_color(248, 250, 252)  # Soft off-white / light slate grey
            pdf.set_draw_color(148, 163, 184)  # Slate border
            
            # Save top Y for container coordinates
            start_y = pdf.get_y()
            pdf.set_font("Helvetica", "BI", 10)
            pdf.set_text_color(51, 65, 85)
            
            # Print text content with side indentation
            pdf.set_x(25)
            pdf.multi_cell(140, 6, to_latin1(report.executive_summary))
            end_y = pdf.get_y()
            
            # Draw boundary callout rect around the summary text
            pdf.rect(20, start_y - 2, 170, (end_y - start_y) + 4, "DF")
            
            # Reprint text over the drawn rect
            pdf.set_y(start_y)
            pdf.set_x(25)
            pdf.multi_cell(160, 6, to_latin1(report.executive_summary))
            pdf.ln(10)

        # Key Points
        if report.key_points:
            self._add_section_header(pdf, "Key Findings & Insights")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(51, 65, 85)
            for point in report.key_points:
                # Custom bullet icon and clean line height
                pdf.set_x(25)
                pdf.cell(5, 6, to_latin1("-"), align="L")
                pdf.multi_cell(155, 6, to_latin1(point))
                pdf.ln(1)
            pdf.ln(6)

        # Important Findings
        if report.important_findings:
            self._add_section_header(pdf, "Detailed Synthesized Components")
            for i, finding in enumerate(report.important_findings, 1):
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(30, 58, 138)
                pdf.cell(0, 6, to_latin1(f"FINDING {i}:"), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(51, 65, 85)
                pdf.multi_cell(0, 6, to_latin1(finding))
                pdf.ln(3)
            pdf.ln(6)

        # Detailed Analysis
        if report.detailed_analysis:
            self._add_section_header(pdf, "Comprehensive Analysis")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(0, 6, to_latin1(report.detailed_analysis))
            pdf.ln(6)

        # Actionable Insights
        if report.actionable_insights:
            self._add_section_header(pdf, "Strategic Recommendations")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(51, 65, 85)
            for i, insight in enumerate(report.actionable_insights, 1):
                pdf.set_x(25)
                pdf.cell(7, 6, to_latin1(f"{i}."), align="L")
                pdf.multi_cell(153, 6, to_latin1(insight))
                pdf.ln(1)
            pdf.ln(6)

        # References
        if report.references:
            self._add_section_header(pdf, "Bibliography & Sources")
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(100, 116, 139)
            for ref in report.references:
                idx = ref.get("index", "")
                title = ref.get("title", "Unknown Link")
                url = ref.get("url", "")
                source_type = ref.get("source_type", "Web")
                
                ref_text = f"[{idx}] {title} — {url} (Class: {source_type.upper()})"
                pdf.multi_cell(0, 5, to_latin1(ref_text))
                pdf.ln(1.5)

        # Save
        pdf.output(filepath)
        logger.info(f"PDF report exported to: {filepath}")
        return filepath

    def _add_section_header(self, pdf: FPDF, title: str):
        """Add a clean, colored section header block with a bottom border line."""
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 58, 138)  # Deep Navy Accent
        pdf.cell(0, 10, to_latin1(title.upper()), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        
        # Accent separator rule
        pdf.set_draw_color(226, 232, 240)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(4)
