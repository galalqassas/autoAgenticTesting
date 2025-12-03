"""Code utility functions for the Python Testing Pipeline."""

import ast
import re
from typing import Optional, Tuple

__all__ = ["validate_syntax", "sanitize_code"]


def validate_syntax(code: str) -> Tuple[bool, str, Optional[dict]]:
    """
    Validates Python syntax.

    Returns:
        tuple: (is_valid, error_message, error_details)
        error_details is a dict with keys: lineno, offset, text, msg
    """
    try:
        ast.parse(code)
        return True, "", None
    except SyntaxError as e:
        error_details = {
            "lineno": e.lineno or 0,
            "offset": e.offset or 0,
            "text": e.text or "",
            "msg": e.msg or "Unknown syntax error",
        }
        error_msg = f"Line {e.lineno}: {e.msg}"
        if e.offset:
            error_msg += f" (column {e.offset})"
        return False, error_msg, error_details


def sanitize_code(code: str) -> str:
    """Removes markdown formatting and ensures valid Python code."""
    # Remove markdown code fences
    code = code.strip()

    # Handle ```python ... ``` blocks
    if code.startswith("```"):
        # Find the end of the first line (language specifier)
        first_newline = code.find("\n")
        if first_newline != -1:
            code = code[first_newline + 1 :]

    # Remove trailing ``` if present
    if code.endswith("```"):
        code = code[:-3].rstrip()

    # Also try regex extraction as fallback
    if "```" in code:
        match = re.search(r"```(?:python)?\s*([\s\S]*?)```", code)
        if match:
            code = match.group(1).strip()

    # Remove any remaining backticks at start/end
    code = code.strip("`").strip()

    return code
