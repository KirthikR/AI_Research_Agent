"""
LLM Client with automatic retry and model fallback.

Uses Groq (groq SDK) for fast, free, high-limit inference (14,400 requests/day).
Supports fast/quality model splits for optimal pipeline performance.
"""

import logging
import time

from agent.config import Config

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Resilient Groq LLM client with retry logic and model fallback.

    Handles rate limiting by:
    1. Retrying with exponential backoff
    2. Falling back to alternative models
    """

    def __init__(self):
        from groq import Groq
        self._client = Groq(api_key=Config.GROQ_API_KEY)

    def generate(self, prompt: str, model: str | None = None) -> str:
        """
        Generate content with automatic retry and model fallback.

        Args:
            prompt: The prompt to send to the LLM.
            model: Specific model to use. Defaults to Config.GROQ_FAST_MODEL.

        Returns:
            The LLM response text.

        Raises:
            RuntimeError: If all retries and fallback models are exhausted.
        """
        default_model = model or Config.GROQ_FAST_MODEL
        
        models_to_try = [default_model] + [
            m for m in Config.GROQ_FALLBACK_MODELS
            if m != default_model
        ]

        last_error = None

        for model_name in models_to_try:
            for attempt in range(Config.LLM_MAX_RETRIES):
                try:
                    response = self._client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful research assistant. Always respond with the exact format requested.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.3,
                        max_tokens=4096,
                    )
                    return response.choices[0].message.content.strip()

                except Exception as e:
                    last_error = e
                    error_str = str(e)

                    if "429" in error_str or "rate" in error_str.lower():
                        delay = Config.LLM_RETRY_BASE_DELAY * (2 ** attempt)
                        logger.warning(
                            f"Rate limited on {model_name} (attempt {attempt + 1}/{Config.LLM_MAX_RETRIES}). "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"LLM error on {model_name}: {e}")
                        break

            logger.info(f"Model {model_name} exhausted, trying next fallback...")

        raise RuntimeError(f"All LLM models and retries exhausted. Last error: {last_error}")
