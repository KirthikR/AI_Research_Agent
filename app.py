import os
import sys
import json
import logging
import streamlit as st

# Add workspace directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.controller import ResearchAgent
from agent.config import Config
from agent.models import ResearchReport
from memory.store import MemoryStore

st.set_page_config(
    page_title="Kirthik AI Research Agent",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
<style>
    /* Global Background & Theme overrides */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    
    /* Sleek futuristic header banner */
    .console-header {
        background: linear-gradient(135deg, rgba(30, 27, 75, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        padding: 2.5rem;
        border-radius: 24px;
        margin-bottom: 2rem;
        backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
    }
    
    .console-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899);
    }
    
    .console-header h1 {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        background: linear-gradient(to right, #ffffff, #c7d2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .console-header p {
        color: #9ca3af;
        font-size: 1.1rem;
        font-weight: 400;
        max-width: 800px;
    }

    /* Glassmorphic Cards & Sections */
    .glass-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 2rem;
        border-radius: 18px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        margin-bottom: 1.5rem;
    }
    
    .section-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 1.4rem;
        color: #818cf8;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Bullet and finding containers to prevent crowding */
    .badge-point {
        background: rgba(99, 102, 241, 0.08);
        border: 1px solid rgba(99, 102, 241, 0.15);
        padding: 1rem 1.25rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        line-height: 1.6;
        font-size: 1rem;
        color: #e5e7eb;
        transition: transform 0.2s ease;
    }
    
    .badge-point:hover {
        transform: translateX(4px);
        border-color: rgba(99, 102, 241, 0.3);
    }
    
    .finding-block {
        background: rgba(245, 158, 11, 0.05);
        border: 1px solid rgba(245, 158, 11, 0.15);
        padding: 1.25rem 1.5rem;
        border-radius: 14px;
        margin-bottom: 1rem;
        line-height: 1.6;
    }
    
    .insight-block {
        background: rgba(16, 185, 129, 0.05);
        border: 1px solid rgba(16, 185, 129, 0.15);
        padding: 1.25rem 1.5rem;
        border-radius: 14px;
        margin-bottom: 1rem;
        line-height: 1.6;
    }

    /* Tabs styling overrides */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: transparent;
        padding: 0.5rem 0;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 8px 20px;
        color: #9ca3af;
        font-weight: 500;
        transition: all 0.3s;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #fff;
        background-color: rgba(99, 102, 241, 0.15);
        border-color: rgba(99, 102, 241, 0.3);
    }

    .stTabs [aria-selected="true"] {
        background-color: #6366f1 !important;
        color: #ffffff !important;
        border-color: #6366f1 !important;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
    }

    /* Styled inputs */
    .stTextInput>div>div>input {
        background-color: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #fff;
        border-radius: 12px;
        padding: 12px 16px;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }

    /* Sidebar visual fixes */
    .css-163gp78, .stSidebar {
        background-color: #070a13 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

if "report" not in st.session_state:
    st.session_state.report = None
if "progress" not in st.session_state:
    st.session_state.progress = []
if "status_container" not in st.session_state:
    st.session_state.status_container = None

def log_progress(stage: str, message: str):
    """Safely append steps to the UI status trace in real-time."""
    st.session_state.progress.append(message)
    if st.session_state.status_container:
        st.session_state.status_container.write(message)

# Initialize controller and storage
agent = ResearchAgent(progress_callback=log_progress)
store = MemoryStore()

st.markdown("""
<div class="console-header">
    <h1>🧬 Kirthik AI Research Agent</h1>
    <p>An autonomous system utilizing distributed tools to collect, synthesize, and compile information on complex topics.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Core Configuration")
    
    #  Groq Status indicator
    st.markdown("""
    <div style="background: rgba(99, 102, 241, 0.05); border: 1px solid rgba(99, 102, 241, 0.15); padding: 1rem; border-radius: 12px; margin-bottom: 0.5rem;">
        <span style="color: #a5b4fc; font-weight: bold; font-size: 0.9rem;">🧠 Reasoning Engine</span><br/>
        <span style="color: #38bdf8; font-size: 0.85rem; font-family: monospace;">Groq Llama-3.3-70B</span>
    </div>
    <div style="font-size: 0.8rem; color: #6b7280; padding: 0.25rem 0.5rem;">
        Credentials loaded securely from local configurations (.env).
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### 📜 System Logs")
    try:
        history = store.get_history(10)
        if history:
            for record in history:
                if st.button(
                    f"🔬 {record.query[:28]}...",
                    key=f"h_{record.id}",
                    use_container_width=True
                ):
                    stored_report = store.get_report_by_id(record.id)
                    if stored_report:
                        st.session_state.report = stored_report
                        st.session_state.progress = []
                        st.rerun()
        else:
            st.info("No previous queries compiled.")
    except Exception:
        st.info("Log manager inactive.")

    st.divider()
    
    if st.button("🗑️ Reset Log History", use_container_width=True):
        try:
            store.clear_history()
            st.session_state.report = None
            st.session_state.progress = []
            st.rerun()
        except Exception:
            pass

input_col, action_col = st.columns([5, 1])

with input_col:
    query = st.text_input(
        "Query Input",
        placeholder="Enter research topic, technology stack, or analysis subject...",
        label_visibility="collapsed"
    )

with action_col:
    trigger_research = st.button("Run Pipeline", type="primary", use_container_width=True)

# Run logic
if trigger_research and query:
    st.session_state.progress = []
    st.session_state.report = None
    
    with st.status("Initializing Kirthik AI Research Agent...", expanded=True) as status:
        st.session_state.status_container = status
        try:
            # Execute pipeline
            report = agent.research(query)
            st.session_state.report = report
            status.update(label="Workflow completed successfully.", state="complete", expanded=False)
        except Exception as err:
            status.update(label="Workflow runtime failure.", state="error")
            st.error(f"Runtime error encountered: {err}")
        finally:
            st.session_state.status_container = None

report = st.session_state.report

if report:
    st.markdown("---")
    
    # Title & Metadata Card
    st.markdown(f"""
    <div class="glass-card" style="padding: 1.5rem 2rem; border-left: 5px solid #6366f1; margin-bottom: 2rem;">
        <h2 style="margin:0; font-family:'Space Grotesk',sans-serif; color:#ffffff; font-size:1.8rem;">{report.title}</h2>
        <div style="display: flex; gap: 2rem; margin-top: 1rem; color: #9ca3af; font-size: 0.9rem;">
            <span>⏱️ <b>Compiled:</b> {report.timestamp[:16].replace('T', ' ')}</span>
            <span>📡 <b>Sources Analysed:</b> {report.total_sources_consulted}</span>
            <span>🧠 <b>Engine:</b> GROQ Model Pipeline</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Clean, Segmented Output Tabs to avoid clashing information
    tab_summary, tab_findings, tab_analysis, tab_detailed_findings, tab_insights, tab_sources = st.tabs([
        "📖 Executive Summary",
        "🔑 Key Takeaways",
        "📝 Detailed Analysis",
        "🔬 Detailed Findings",
        "💡 Actionable Steps",
        "📚 References & Logs"
    ])

    # Tab 1: Executive Summary
    with tab_summary:
        st.markdown('<div class="section-title">📖 Synthesis Summary</div>', unsafe_allow_html=True)
        if report.executive_summary:
            st.markdown(f"<div style='font-size: 1.1rem; line-height: 1.8; color: #d1d5db;'>{report.executive_summary}</div>", unsafe_allow_html=True)
        else:
            st.info("No executive summary compiled for this run.")

    # Tab 2: Key Takeaways
    with tab_findings:
        st.markdown('<div class="section-title">🔑 Core Insights</div>', unsafe_allow_html=True)
        if report.key_points:
            for point in report.key_points:
                st.markdown(f'<div class="badge-point">📌 {point}</div>', unsafe_allow_html=True)
        else:
            st.info("No primary bullet points provided.")

    # Tab 3: Detailed Analysis
    with tab_analysis:
        st.markdown('<div class="section-title">📝 Comprehensive Analysis</div>', unsafe_allow_html=True)
        if report.detailed_analysis:
            st.markdown(f"<div style='font-size: 1.1rem; line-height: 1.8; color: #d1d5db;'>{report.detailed_analysis}</div>", unsafe_allow_html=True)
        else:
            st.info("No comprehensive detailed analysis compiled.")

    # Tab 4: Detailed Findings
    with tab_detailed_findings:
        st.markdown('<div class="section-title">🔬 Detailed Findings</div>', unsafe_allow_html=True)
        if report.important_findings:
            for finding in report.important_findings:
                st.markdown(f'<div class="finding-block"><b>Analysis Report:</b> {finding}</div>', unsafe_allow_html=True)
        else:
            st.info("No detailed analytical components found.")

    # Tab 5: Actionable Steps
    with tab_insights:
        st.markdown('<div class="section-title">💡 Actionable Recommendations</div>', unsafe_allow_html=True)
        if report.actionable_insights:
            for insight in report.actionable_insights:
                st.markdown(f'<div class="insight-block">💡 {insight}</div>', unsafe_allow_html=True)
        else:
            st.info("No direct takeaways recommended for this subject.")

    # Tab 5: References & Logs
    with tab_sources:
        col_ref, col_agent = st.columns([2, 1])
        
        with col_ref:
            st.markdown('<div class="section-title">📚 Source Citations</div>', unsafe_allow_html=True)
            if report.references:
                for ref in report.references:
                    idx = ref.get("index", "*")
                    title = ref.get("title", "External Link")
                    url = ref.get("url", "#")
                    src = ref.get("source_type", "web")
                    st.markdown(f"""
                    <div style="background: rgba(30, 41, 59, 0.4); padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border: 1px solid rgba(255,255,255,0.03);">
                        <span style="color:#818cf8; font-weight:bold;">[{idx}]</span> <b>{title}</b><br/>
                        <a href="{url}" target="_blank" style="color:#38bdf8; text-decoration:none; font-size:0.85rem; word-break:break-all;">{url}</a><br/>
                        <span style="font-size:0.75rem; color:#6b7280; text-transform:uppercase;">Source Class: {src}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No bibliography references found.")
                
        with col_agent:
            st.markdown('<div class="section-title">🧠 Decision Rationale</div>', unsafe_allow_html=True)
            if report.agent_reasoning:
                st.markdown(f"""
                <div style="background: rgba(99, 102, 241, 0.05); border: 1px solid rgba(99, 102, 241, 0.1); padding: 1rem; border-radius: 8px; font-size: 0.9rem; color: #a5b4fc; line-height: 1.6;">
                    {report.agent_reasoning}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No reasoning diagnostics logged.")

    # Export & Download Actions
    st.markdown("---")
    col_pdf, _ = st.columns([2, 3])
    
    with col_pdf:
        try:
            pdf_path = agent.export_pdf(report)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Professional PDF Report",
                    data=f.read(),
                    file_name=f"research_report_{report.query[:20].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception as e:
            st.caption(f"PDF compiler inactive: {e}")

else:
    # Warm Welcome Dashboard State
    st.markdown("""
    <div style="margin: 2rem 0; text-align: center;">
        <h3 style="font-family:'Space Grotesk',sans-serif; color: #818cf8;">Systems Ready to Query</h3>
        <p style="color: #6b7280; max-width: 600px; margin: 0.5rem auto 2rem auto;">
            Provide a query above to dispatch autonomous workers. Information will be collected, cleaned, deduplicated, and summarized on the fly.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    pass
