"""Code utility functions for the Python Testing Pipeline."""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

__all__ = [
    "validate_syntax",
    "sanitize_code",
    "detect_hallucinations",
    "CodeDefinition",
    "extract_code_definitions",
]

# Standard library modules to ignore in hallucination detection
_STDLIB_MODULES = frozenset({
    "os", "sys", "re", "json", "time", "datetime", "pathlib", "typing",
    "unittest", "pytest", "mock", "subprocess", "io", "collections",
    "functools", "itertools", "threading", "asyncio", "socket", "http",
    "urllib", "logging", "warnings", "contextlib", "dataclasses", "enum",
    "abc", "copy", "hashlib", "random", "math", "string", "tempfile",
})

# Common builtins/test functions to ignore
_COMMON_FUNCS = frozenset({
    "print", "len", "range", "str", "int", "float", "list", "dict", "set",
    "tuple", "open", "isinstance", "hasattr", "getattr", "setattr", "type",
    "super", "enumerate", "zip", "map", "filter", "sorted", "any", "all",
    "min", "max", "sum", "abs", "round", "id", "repr", "callable",
    "fixture", "patch", "MagicMock", "Mock", "PropertyMock",
})


@dataclass
class CodeDefinition:
    """Represents a function or class definition with its line range."""
    type: str  # 'FunctionDef', 'ClassDef', 'AsyncFunctionDef'
    name: str
    start_line: int  # 1-indexed
    end_line: int    # 1-indexed


def extract_code_definitions(source_code: str, recursive: bool = False) -> List[CodeDefinition]:
    """Extract function and class definitions from Python source code."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    target_types = (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)
    nodes = ast.walk(tree) if recursive else ast.iter_child_nodes(tree)

    return [
        CodeDefinition(
            type=node.__class__.__name__,
            name=node.name,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
        )
        for node in nodes
        if isinstance(node, target_types)
    ]


def validate_syntax(code: str) -> Tuple[bool, str, Optional[dict]]:
    """Validate Python syntax. Returns (is_valid, error_message, error_details)."""
    try:
        ast.parse(code)
        return True, "", None
    except SyntaxError as e:
        details = {"lineno": e.lineno or 0, "offset": e.offset or 0, "text": e.text or "", "msg": e.msg or "Unknown"}
        msg = f"Line {e.lineno}: {e.msg}" + (f" (column {e.offset})" if e.offset else "")
        return False, msg, details


def sanitize_code(code: str) -> str:
    """Remove markdown formatting and ensure valid Python code."""
    code = code.strip()

    # Remove markdown code blocks
    if code.startswith("```"):
        code = code.split("\n", 1)[-1] if "\n" in code else code[3:]
    if code.endswith("```"):
        code = code[:-3].rstrip()

    # Extract from inline code blocks
    if "```" in code:
        match = re.search(r"```(?:python)?\s*([\s\S]*?)```", code)
        if match:
            code = match.group(1).strip()

    return code.strip("`").strip()


def detect_hallucinations(generated_code: str, codebase_path: Path) -> List[dict]:
    """Detect hallucinated imports, functions, or classes in LLM-generated code."""
    hallucinations = []

    # Build knowledge of actual codebase
    existing_modules, existing_symbols = set(), set()

    if codebase_path.exists():
        for py_file in codebase_path.rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in py_file.stem.lower():
                continue
            existing_modules.add(py_file.stem)
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
                existing_symbols.update(
                    node.name for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                )
            except (SyntaxError, UnicodeDecodeError):
                pass

    # Check imports
    for line in generated_code.splitlines():
        match = re.match(r"^(?:from|import)\s+(\w+)", line.strip())
        if match:
            module = match.group(1)
            if module not in _STDLIB_MODULES and not module.startswith("pytest") and module not in existing_modules:
                hallucinations.append({
                    "type": "hallucinated_import",
                    "name": module,
                    "reason": f"Module '{module}' not found in codebase",
                })

    # Check function/class calls via AST
    try:
        tree = ast.parse(generated_code)
        imported_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_names.update(alias.asname or alias.name for alias in node.names)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                name = node.func.id
                if name in imported_names or name in _COMMON_FUNCS or name in existing_symbols:
                    continue
                h_type = "hallucinated_class" if name[0].isupper() else "hallucinated_function"
                hallucinations.append({
                    "type": h_type,
                    "name": name,
                    "reason": f"{'Class' if name[0].isupper() else 'Function'} '{name}' not defined in codebase",
                })
    except SyntaxError:
        pass

    return hallucinations
