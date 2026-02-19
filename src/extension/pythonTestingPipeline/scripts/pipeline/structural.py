"""Statement-level coverage analysis.

Walks the AST to identify individual statement nodes and maps them to the
executed-lines set produced by coverage.py's JSON reporter.  This gives a
more granular view than plain line coverage because it counts *statements*
rather than raw lines (comments, blank lines, decorators, docstrings are
excluded).
"""

import ast
from typing import Set

from pipeline.models import StatementCoverageReport

__all__ = ["analyze_statement_coverage"]

# AST node types that represent executable statements.
_STATEMENT_TYPES = (
    ast.Assign,
    ast.AugAssign,
    ast.AnnAssign,
    ast.Return,
    ast.Expr,
    ast.Raise,
    ast.Assert,
    ast.Delete,
    ast.Pass,
    ast.Break,
    ast.Continue,
    ast.Import,
    ast.ImportFrom,
    ast.Global,
    ast.Nonlocal,
    # Compound statements whose *header line* counts as a statement
    ast.If,
    ast.For,
    ast.While,
    ast.With,
    ast.Try,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
)

# Python 3.10+
if hasattr(ast, "Match"):
    _STATEMENT_TYPES = (*_STATEMENT_TYPES, ast.Match)
if hasattr(ast, "TryStar"):
    _STATEMENT_TYPES = (*_STATEMENT_TYPES, ast.TryStar)


def _calc_pct(covered: int, total: int) -> float:
    return round((covered / total * 100) if total > 0 else 0.0, 1)


def _collect_statement_lines(source_code: str) -> Set[int]:
    """Return the set of lines that contain an executable statement."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return set()

    lines: Set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, _STATEMENT_TYPES) and hasattr(node, "lineno"):
            lines.add(node.lineno)
    return lines


def analyze_statement_coverage(
    source_code: str,
    executed_lines: Set[int],
    missing_lines: Set[int],
    excluded_lines: Set[int],
) -> StatementCoverageReport:
    """Compute statement coverage for a single source file.

    Args:
        source_code: The full text of the Python source file.
        executed_lines: Lines executed during testing (from coverage.json).
        missing_lines: Lines that are executable but were not executed.
        excluded_lines: Lines excluded from coverage measurement.

    Returns:
        A populated StatementCoverageReport.
    """
    stmt_lines = _collect_statement_lines(source_code)

    # Intersect with the set of executable lines known to coverage.py so we
    # don't count lines that the runtime never considers executable (e.g.
    # lines inside ``if TYPE_CHECKING`` blocks that coverage itself skips).
    executable = (executed_lines | missing_lines) - excluded_lines
    relevant_stmts = stmt_lines & executable

    covered = relevant_stmts & executed_lines
    uncovered = sorted(relevant_stmts - executed_lines)

    return StatementCoverageReport(
        total_statements=len(relevant_stmts),
        covered_statements=len(covered),
        uncovered_statement_lines=uncovered,
        coverage_percentage=_calc_pct(len(covered), len(relevant_stmts)),
    )
