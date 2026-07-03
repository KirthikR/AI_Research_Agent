# 🔬 Autonomous AI Research Agent

An autonomous AI agent that accepts a user query, **autonomously selects the best information sources**, gathers data in parallel, deduplicates and filters content, and generates a **structured, actionable research report** — all powered by LLM reasoning with **zero hardcoded rules**.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **Autonomous Source Selection** | LLM decides which sources to search based on query analysis |
| ⚡ **Parallel Information Gathering** | Searches multiple sources simultaneously |
| 🔍 **5 Search Tools** | Web Search, Wikipedia, ArXiv, News, URL Scraping |
| 🔎 **LLM Deduplication** | Semantic duplicate detection and relevance filtering |
| 📝 **Structured Reports** | Key Points, Findings, Actionable Insights, References |
| 📄 **Export: PDF & Markdown** | Professional report export in multiple formats |
| 💾 **Memory Store** | SQLite-based search history for past research |
| 🌐 **Web UI + CLI** | Beautiful Streamlit interface and command-line tool |
| 🔄 **Follow-up Research** | LLM evaluates if additional searches are needed |

## 🏗️ Architecture

```
User Query → LLM Source Selection → Parallel Gathering → Extraction → LLM Dedup → LLM Summary → Report
```

```
AI_research_agent/
├── app.py                  # Streamlit web UI
├── main.py                 # CLI entry point
├── agent/
│   ├── controller.py       # Main orchestrator
│   ├── reasoning.py        # LLM reasoning engine
│   ├── config.py           # Configuration
│   └── models.py           # Data models
├── tools/
│   ├── web_search.py       # DuckDuckGo search
│   ├── wikipedia_tool.py   # Wikipedia API
│   ├── arxiv_tool.py       # ArXiv papers
│   ├── news_search.py      # News search
│   └── web_scraper.py      # URL scraping
├── processing/
│   ├── extractor.py        # Content extraction
│   ├── deduplicator.py     # LLM deduplication
│   └── summarizer.py       # Summary generation
├── export/
│   ├── markdown_export.py  # Markdown export
│   └── pdf_export.py       # PDF export
├── memory/
│   └── store.py            # SQLite memory
└── outputs/                # Generated reports
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10 or higher
- A **Groq API key** (free at https://console.groq.com/keys)

### 2. Install Dependencies

```bash
cd AI_research_agent
pip install -r requirements.txt
```

### 3. Set Your API Key

Create a `.env` file:

```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

Or set it as an environment variable:

```bash
export GROQ_API_KEY="your_key_here"
```

### 4. Run the Agent

#### Web UI (Recommended)
```bash
streamlit run app.py
```

#### CLI — Single Query
```bash
python main.py "What are the latest advances in quantum computing?"
```

#### CLI — Interactive Mode
```bash
python main.py --interactive
```

## 📖 Usage Examples

### Web UI

1. Open the Streamlit app in your browser
2. The agent automatically loads your Groq key from `.env`
3. Type your research query and click **Run Pipeline**
4. View the structured report with clean, expandable tabs
5. Export as a professional article-style PDF using the download button
6. Browse previous searches in the sidebar

### CLI

```bash
# Single query with both exports
python main.py "Impact of AI on healthcare" --export both

# Only Markdown export
python main.py "Climate change solutions" --export md

# Interactive mode
python main.py -i

# Verbose logging
python main.py "Quantum computing" -v
```

### Interactive Mode Commands

| Command | Description |
|---------|-------------|
| Any text | Runs a research query |
| `history` | Shows previous searches |
| `export` | Exports the last report (PDF) |
| `export pdf` | Exports as PDF only |
| `quit` | Exit the agent |

## 🧠 How It Works (No Hardcoded Rules)

### 1. Autonomous Source Selection
The LLM analyzes your query and decides which sources are most appropriate:
- **Academic query** → ArXiv + Wikipedia + Web Search
- **Current events** → News + Web Search
- **General knowledge** → Wikipedia + Web Search
- The LLM reasons about this — no if/else rules!

### 2. Query Refinement
The LLM generates **optimized search terms** for each source:
- Wikipedia: concise topic names
- ArXiv: technical terms
- News: current-event phrasing

### 3. Parallel Gathering
All selected sources are searched **simultaneously** using Python's ThreadPoolExecutor.

### 4. Deduplication
The LLM semantically identifies overlapping information across sources and removes duplicates.

### 5. Structured Report
The LLM synthesizes all gathered content into:
- 📖 Executive Summary
- 🔑 Key Points (5-8 items)
- 🔬 Important Findings (4-6 detailed findings)
- 💡 Actionable Insights (3-5 recommendations)
- 📊 Detailed Analysis
- 📚 References with source links

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | Required | Groq API key |
| `GROQ_FAST_MODEL` | `llama-3.1-8b-instant` | Groq model for reasoning, routing & deduplication |
| `GROQ_QUALITY_MODEL` | `llama-3.1-8b-instant` | Groq model for final report generation (falls back to 70B if needed) |
| `MAX_SOURCES` | `3` | Max sources per search |
| `MAX_RESULTS_PER_TOOL` | `3` | Max results per tool |
| `MAX_CONTENT_LENGTH` | `2000` | Max content chars per source |
| `ENABLE_FOLLOWUP` | `False` | Toggle follow-up research rounds |
| `REQUEST_TIMEOUT` | `10` | HTTP request timeout (seconds) |
| `MAX_WORKERS` | `5` | Parallel worker threads |
| `OUTPUT_DIR` | `outputs` | Report output directory |

## 📊 Technology Stack

- **LLM**: Groq (via `groq` client)
- **Web Search**: DuckDuckGo (free, no API key)
- **Wikipedia**: `wikipedia-api`
- **Academic**: `arxiv` Python client
- **Scraping**: `requests` + `BeautifulSoup4`
- **PDF**: `fpdf2`
- **UI**: `Streamlit`
- **Memory**: `SQLite`
- **Data Models**: `Pydantic`

## 📝 License

This project was built as an assessment submission. All code is original work.
