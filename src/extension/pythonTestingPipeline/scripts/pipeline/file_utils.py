"""File utility functions for the Python Testing Pipeline."""

import os
import re
from pathlib import Path
from typing import List

__all__ = [
    "gather_python_files",
    "read_file_contents",
    "read_file_contents_chunked",
    "truncate_at_boundary",
]


def truncate_at_boundary(code: str, max_chars: int) -> str:
    """
    Truncate code at a logical boundary (end of function/class or blank line).

    Args:
        code: Source code string to truncate
        max_chars: Maximum character limit

    Returns:
        Truncated code ending at a logical boundary
    """
    if len(code) <= max_chars:
        return code

    # Get the substring up to max_chars
    truncated = code[:max_chars]

    # Try to find the last complete function/class definition
    # Look for patterns like "\ndef " or "\nclass " that indicate a new definition
    definition_pattern = re.compile(r"\n(?=def |class )", re.MULTILINE)
    matches = list(definition_pattern.finditer(truncated))

    if matches:
        # Cut at the start of the last definition (keeping complete previous definitions)
        last_def_start = matches[-1].start()
        if last_def_start > max_chars // 2:  # Only if we're keeping at least half the content
            return truncated[:last_def_start].rstrip() + "\n# ... (truncated)"

    # Fallback: find the last blank line (double newline)
    last_blank = truncated.rfind("\n\n")
    if last_blank > max_chars // 2:
        return truncated[:last_blank].rstrip() + "\n# ... (truncated)"

    # Final fallback: find the last newline
    last_newline = truncated.rfind("\n")
    if last_newline > 0:
        return truncated[:last_newline].rstrip() + "\n# ... (truncated)"

    return truncated + "\n# ... (truncated)"


def gather_python_files(codebase_path: Path) -> List[Path]:
    """Gathers all Python files from the codebase."""
    python_files = []
    excluded_dirs = {
        ".git",
        "__pycache__",
        "venv",
        ".venv",
        "node_modules",
        ".pytest_cache",
        "tests",
        "test",
        "__tests__",
    }

    for root, dirs, files in os.walk(codebase_path):
        # Filter out excluded directories (test directories, hidden dirs, etc.)
        dirs[:] = [d for d in dirs if d not in excluded_dirs and not d.startswith(".")]

        for file in files:
            # Exclude test files: test_*.py, *_test.py, conftest.py
            if file.endswith(".py"):
                is_test_file = (
                    file.startswith("test_")
                    or file.endswith("_test.py")
                    or file == "conftest.py"
                )
                if not is_test_file:
                    python_files.append(Path(root) / file)

    return python_files


def read_file_contents(files: List[Path]) -> str:
    """Reads and combines content from multiple files."""
    contents = []
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                contents.append(f"# File: {file_path}\n{f.read()}")
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
    return "\n\n".join(contents)


def read_file_contents_chunked(
    files: List[Path], max_lines_per_chunk: int = 100
) -> List[str]:
    """
    Reads files and chunks them by logical boundaries (functions/classes).

    Args:
        files: List of Python files to read
        max_lines_per_chunk: Target maximum lines per chunk (default: 200)

    Returns:
        List of code chunks, each containing logical units under ~max_lines_per_chunk
    """
    chunks = []

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
                file_lines = file_content.splitlines()

            # Try to parse with AST
            try:
                from pipeline.code_utils import extract_code_definitions

                definitions = extract_code_definitions(file_content, recursive=False)

                # Convert CodeDefinition objects to dict format for compatibility
                def_dicts = [
                    {
                        "type": d.type,
                        "name": d.name,
                        "start": d.start_line - 1,  # Convert to 0-indexed
                        "end": d.end_line,
                        "lines": d.end_line - d.start_line + 1,
                    }
                    for d in definitions
                ]

                # Group definitions into chunks
                if def_dicts:
                    current_chunk_defs = []
                    current_chunk_lines = 0

                    for defn in def_dicts:
                        # If adding this definition exceeds the limit and we have existing defs
                        if (
                            current_chunk_lines + defn["lines"] > max_lines_per_chunk
                            and current_chunk_defs
                        ):
                            # Flush current chunk
                            start_idx = current_chunk_defs[0]["start"]
                            end_idx = current_chunk_defs[-1]["end"]
                            chunk_content = "\n".join(file_lines[start_idx:end_idx])
                            chunks.append(f"# File: {file_path}\n{chunk_content}")

                            # Start new chunk with current definition
                            current_chunk_defs = [defn]
                            current_chunk_lines = defn["lines"]
                        else:
                            # Add to current chunk
                            current_chunk_defs.append(defn)
                            current_chunk_lines += defn["lines"]

                    # Flush remaining chunk
                    if current_chunk_defs:
                        start_idx = current_chunk_defs[0]["start"]
                        end_idx = current_chunk_defs[-1]["end"]
                        chunk_content = "\n".join(file_lines[start_idx:end_idx])
                        chunks.append(f"# File: {file_path}\n{chunk_content}")
                else:
                    # No definitions found, chunk by line count
                    for i in range(0, len(file_lines), max_lines_per_chunk):
                        chunk_lines = file_lines[i : i + max_lines_per_chunk]
                        chunks.append(
                            f"# File: {file_path} (lines {i + 1}-{i + len(chunk_lines)})\n"
                            + "\n".join(chunk_lines)
                        )

            except SyntaxError:
                # If AST parsing fails, fall back to simple line-based chunking
                print(
                    f"   ⚠️  Could not parse {file_path.name}, using line-based chunking"
                )
                for i in range(0, len(file_lines), max_lines_per_chunk):
                    chunk_lines = file_lines[i : i + max_lines_per_chunk]
                    chunks.append(
                        f"# File: {file_path} (lines {i + 1}-{i + len(chunk_lines)})\n"
                        + "\n".join(chunk_lines)
                    )

        except Exception as e:
            print(f"   Warning: Could not read {file_path}: {e}")

    return chunks
