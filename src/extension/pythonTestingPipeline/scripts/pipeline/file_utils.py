"""File utility functions for the Python Testing Pipeline."""

import ast
import os
from pathlib import Path
from typing import List

__all__ = ["gather_python_files", "read_file_contents", "read_file_contents_chunked"]


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
    files: List[Path], max_lines_per_chunk: int = 200
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
                tree = ast.parse(file_content)

                # Extract top-level definitions with their line ranges
                definitions = []
                for node in ast.iter_child_nodes(tree):
                    if isinstance(
                        node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)
                    ):
                        # Get the line range of this definition
                        start_line = node.lineno - 1  # Convert to 0-indexed
                        end_line = (
                            node.end_lineno if node.end_lineno else start_line + 1
                        )

                        definitions.append(
                            {
                                "type": node.__class__.__name__,
                                "name": node.name,
                                "start": start_line,
                                "end": end_line,
                                "lines": end_line - start_line,
                            }
                        )

                # Group definitions into chunks
                if definitions:
                    current_chunk_defs = []
                    current_chunk_lines = 0

                    for defn in definitions:
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
