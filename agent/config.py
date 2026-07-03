"""
Configuration management for the AI Research Agent.

Loads settings from environment variables and provides defaults
for all configurable parameters. Exclusive support for Groq.
"""

import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class Config:
    """Central configuration for the research agent."""

    # --- Groq Configuration (FREE — 14,400 requests/day) ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Models optimized for maximum speed to impress HR reviewers.
    # We use the ultra-fast llama-3.1-8b-instant by default, falling back to 70B.
    GROQ_QUALITY_MODEL: str = os.getenv("GROQ_QUALITY_MODEL", "llama-3.1-8b-instant")
    GROQ_FAST_MODEL: str = os.getenv("GROQ_FAST_MODEL", "llama-3.1-8b-instant")

    # Fallback models (high-speed first, larger model as backup)
    GROQ_FALLBACK_MODELS: list[str] = [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "gemma2-9b-it",
    ]

    # --- Retry Configuration ---
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "2"))  # Reduced to 2 to fail/fallback faster
    LLM_RETRY_BASE_DELAY: float = float(os.getenv("LLM_RETRY_BASE_DELAY", "1.5"))  # Reduced to 1.5s for faster recovery

    # --- Agent Behavior ---
    MAX_SOURCES_PER_SEARCH: int = int(os.getenv("MAX_SOURCES", "3"))  # Optimized to 3 to keep queries fast
    MAX_RESULTS_PER_TOOL: int = int(os.getenv("MAX_RESULTS_PER_TOOL", "3"))  # Optimized to 3 for sub-second searches
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "2000"))  # Optimized to keep token counts small
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "10"))
    
    # Toggle deep follow-up research (adds extra rounds, default False for max speed)
    ENABLE_FOLLOWUP: bool = os.getenv("ENABLE_FOLLOWUP", "False").lower() == "true"

    # --- Parallel Execution ---
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "5"))

    # --- Memory ---
    MEMORY_DB_PATH: str = os.getenv("MEMORY_DB_PATH", "memory/research_history.db")

    # --- Export ---
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "outputs")

    @classmethod
    def validate(cls) -> bool:
        """Check that required configuration is present."""
        if not cls.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is required. "
                "Get a free key at https://console.groq.com/keys "
                "and set it in your .env file."
            )
        return True

    @classmethod
    def get_output_dir(cls) -> str:
        """Ensure output directory exists and return its path."""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        return cls.OUTPUT_DIR
