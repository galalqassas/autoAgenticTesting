"""Code utility functions for the Python Testing Pipeline."""

import ast
import re
from pathlib import Path
from typing import List, Optional, Tuple

__all__ = ["validate_syntax", "sanitize_code", "detect_hallucinations"]


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
    code = code.strip()

    if code.startswith("```"):
        first_newline = code.find("\n")
        if first_newline != -1:
            code = code[first_newline + 1 :]

    if code.endswith("```"):
        code = code[:-3].rstrip()

    if "```" in code:
        match = re.search(r"```(?:python)?\s*([\s\S]*?)```", code)
        if match:
            code = match.group(1).strip()

    code = code.strip("`").strip()
    return code


def detect_hallucinations(generated_code: str, codebase_path: Path) -> List[dict]:
    """
    Detect hallucinated imports, functions, or classes in LLM-generated code.

    Checks for:
    1. Imports of non-existent modules
    2. Calls to functions/classes that don't exist in the codebase

    Returns:
        List of hallucination records with type, name, and reason.
    """
    hallucinations = []

    # === 1. Build knowledge of actual codebase ===
    existing_modules = set()
    existing_symbols = set()  # Functions and classes in codebase

    if codebase_path.exists():
        for py_file in codebase_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            if "test" in py_file.stem.lower():
                continue

            existing_modules.add(py_file.stem)

            # Parse AST to extract function/class names
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        existing_symbols.add(node.name)
                    elif isinstance(node, ast.ClassDef):
                        existing_symbols.add(node.name)
            except (SyntaxError, UnicodeDecodeError):
                pass

    # === 2. Check imports ===
    import_pattern = r"^from\s+(\w+)\s+import|^import\s+(\w+)"
    stdlib_modules = {
        "os",
        "sys",
        "re",
        "json",
        "time",
        "datetime",
        "pathlib",
        "typing",
        "unittest",
        "pytest",
        "mock",
        "subprocess",
        "io",
        "collections",
        "functools",
        "itertools",
        "threading",
        "asyncio",
        "socket",
        "http",
        "urllib",
        "logging",
        "warnings",
        "contextlib",
        "dataclasses",
        "enum",
        "abc",
        "copy",
        "hashlib",
        "random",
        "math",
        "string",
        "tempfile",
    }

    for line in generated_code.splitlines():
        line = line.strip()
        match = re.match(import_pattern, line)
        if match:
            module = match.group(1) or match.group(2)
            if module in stdlib_modules or module.startswith("pytest"):
                continue
            if module not in existing_modules:
                hallucinations.append(
                    {
                        "type": "hallucinated_import",
                        "name": module,
                        "reason": f"Module '{module}' not found in codebase",
                    }
                )

    # === 3. Check function/class calls via AST ===
    try:
        tree = ast.parse(generated_code)

        # Collect imported names (these are valid references)
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)

        # Common test/stdlib functions to ignore
        common_funcs = {
            "print",
            "len",
            "range",
            "str",
            "int",
            "float",
            "list",
            "dict",
            "set",
            "tuple",
            "open",
            "isinstance",
            "hasattr",
            "getattr",
            "setattr",
            "type",
            "super",
            "enumerate",
            "zip",
            "map",
            "filter",
            "sorted",
            "any",
            "all",
            "min",
            "max",
            "sum",
            "abs",
            "round",
            "id",
            "repr",
            "callable",
            "fixture",
            "patch",
            "MagicMock",
            "Mock",
            "PropertyMock",
        }

        # Check function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                func_name = node.func.id
                # Skip if it's imported, stdlib, or exists in codebase
                if func_name in imported_names:
                    continue
                if func_name in common_funcs:
                    continue
                if func_name in existing_symbols:
                    continue
                # Check if it looks like a class (PascalCase) or function
                if func_name[0].isupper():
                    hallucinations.append(
                        {
                            "type": "hallucinated_class",
                            "name": func_name,
                            "reason": f"Class '{func_name}' not defined in codebase",
                        }
                    )
                else:
                    hallucinations.append(
                        {
                            "type": "hallucinated_function",
                            "name": func_name,
                            "reason": f"Function '{func_name}' not defined in codebase",
                        }
                    )
    except SyntaxError:
        pass  # Already caught by syntax validation

    return hallucinations
