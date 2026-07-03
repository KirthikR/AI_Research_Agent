"""
Utility functions for the AI Research Agent.

Includes robust JSON parsing helpers to handle malformed LLM responses
(e.g., literal newlines in strings, unescaped characters, or markdown fences).
"""

import json
import logging
import re

logger = logging.getLogger(__name__)


def repair_unescaped_quotes(json_str: str) -> str:
    """
    Scans a JSON-like string and escapes double quotes that appear inside string values.
    Uses a state machine to distinguish between structural JSON quotes and unescaped content quotes.
    """
    chars = list(json_str)
    length = len(chars)
    in_string = False
    escape_next = False
    
    # State tracking
    i = 0
    while i < length:
        char = chars[i]
        
        if escape_next:
            escape_next = False
            i += 1
            continue
            
        if char == '\\':
            escape_next = True
            i += 1
            continue
            
        if char == '"':
            if not in_string:
                # Entering a string (could be a key or a value)
                in_string = True
            else:
                # We are inside a string and hit a quote.
                # Let's inspect what follows to determine if it's a structural quote.
                # Look ahead for: optional spaces followed by colon (:), comma (,), closing brace (}), or closing bracket (])
                lookahead = ""
                j = i + 1
                while j < length and chars[j].isspace():
                    j += 1
                if j < length:
                    lookahead = chars[j]
                
                # Structural quote checks
                is_structural = (
                    lookahead in (':', ',', '}', ']')
                    or lookahead == ""  # End of string
                )
                
                if is_structural:
                    # Exiting the string safely
                    in_string = False
                else:
                    # Unescaped quote inside string! Escape it by replacing " with \"
                    chars[i] = '\\"'
        i += 1
        
    return "".join(chars)


def parse_llm_json(response_text: str) -> dict:
    """
    Parses a JSON string returned by the LLM.
    Handles markdown code blocks, literal control characters, and unescaped quotes.
    """
    if not response_text:
        return {}

    cleaned = response_text.strip()

    # Remove markdown code fences if present
    if cleaned.startswith("```"):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if match:
            cleaned = match.group(1).strip()
        else:
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

    # Clean up non-JSON leading/trailing garbage text
    if not (cleaned.startswith("{") or cleaned.startswith("[")):
        start_idx = min(
            [cleaned.find(char) for char in ["{", "["] if cleaned.find(char) != -1]
            or [0]
        )
        end_idx = max(
            [cleaned.rfind(char) for char in ["}", "]"] if cleaned.rfind(char) != -1]
            or [len(cleaned)]
        )
        cleaned = cleaned[start_idx : end_idx + 1].strip()

    # Key normalization: normalize any unquoted or single-quoted keys for standard JSON properties
    target_fields = [
        "title", "executive_summary", "key_points", "important_findings",
        "actionable_insights", "detailed_analysis", "keep_indices",
        "removed_reasons", "reasoning", "selected_sources", "refined_queries"
    ]
    for field in target_fields:
        cleaned = re.sub(rf"['\"]?{field}['\"]?\s*:", f'"{field}":', cleaned)

    # First attempt: strict json load
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Second attempt: permit control characters (strict=False)
    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError as err:
        # Demoted to DEBUG to keep terminal stdout clean
        logger.debug(f"Strict JSON parsing failed: {err}. Attempting recovery.")

    # Third attempt: repair unescaped quotes and escape control characters
    try:
        repaired = repair_unescaped_quotes(cleaned)
        # Escape raw newlines inside values
        repaired = re.sub(
            r'"([^"\\]|\\.)*"', 
            lambda m: m.group(0).replace("\n", "\\n").replace("\r", "\\r"), 
            repaired
        )
        return json.loads(repaired, strict=False)
    except Exception as err:
        # Demoted to DEBUG to keep terminal stdout clean
        logger.debug(f"Failed to recover JSON parsing via string repair: {err}")
        # Return fallback parsed dict from regex if possible to ensure the pipeline NEVER fails
        return _extract_fallback_fields(cleaned)


def _extract_fallback_fields(raw_text: str) -> dict:
    """Fallback parser using regex to salvage fields if JSON is critically malformed."""
    result = {}
    # Simple regex matches for text keys
    for field in ["title", "executive_summary", "detailed_analysis", "reasoning"]:
        match = re.search(rf'"{field}"\s*:\s*"([\s\S]*?)"\s*[,}}]', raw_text)
        if match:
            result[field] = match.group(1).replace('\\"', '"').replace('\\n', '\n').strip()
            
    # List fields extraction
    for field in ["key_points", "important_findings", "actionable_insights", "keep_indices"]:
        match = re.search(rf'"{field}"\s*:\s*\[([\s\S]*?)\]', raw_text)
        if match:
            items = re.findall(r'"([\s\S]*?)"', match.group(1))
            if not items and field == "keep_indices":
                # Handle numeric indices
                items = re.findall(r'(\d+)', match.group(1))
                result[field] = [int(item) for item in items]
            else:
                result[field] = [item.replace('\\"', '"').strip() for item in items]
            
    return result
