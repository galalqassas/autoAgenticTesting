"""Coverage analysis module for the Python Testing Pipeline."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Set

from pipeline.code_utils import extract_code_definitions, CodeDefinition

__all__ = [
    "FileCoverageReport",
    "FunctionCoverageReport",
    "analyze_coverage",
    "format_uncovered_areas",
]


@dataclass
class FunctionCoverageReport:
    """Coverage report for a single function or class."""

    name: str
    type: str  # 'FunctionDef', 'ClassDef', 'AsyncFunctionDef'
    start_line: int
    end_line: int
    total_lines: int
    covered_lines: int
    uncovered_lines: List[int]
    coverage_percentage: float


@dataclass
class FileCoverageReport:
    """Coverage report for a single file."""

    file_path: str
    total_lines: int
    covered_lines: int
    uncovered_lines: List[int]
    coverage_percentage: float
    functions: List[FunctionCoverageReport]


def analyze_coverage(
    coverage_json_path: Path, source_root: Path
) -> Dict[str, FileCoverageReport]:
    """
    Analyzes coverage data and maps it to code definitions.

    Args:
        coverage_json_path: Path to the coverage.json file.
        source_root: Root path of the source code being tested.

    Returns:
        Dictionary mapping file paths to FileCoverageReport objects.
    """
    if not coverage_json_path.exists():
        return {}

    with open(coverage_json_path, "r", encoding="utf-8") as f:
        coverage_data = json.load(f)

    reports = {}

    for file_path, file_data in coverage_data.get("files", {}).items():
        executed_lines: Set[int] = set(file_data.get("executed_lines", []))
        missing_lines: Set[int] = set(file_data.get("missing_lines", []))
        excluded_lines: Set[int] = set(file_data.get("excluded_lines", []))

        # Read source file for AST parsing
        source_path = Path(file_path)
        if not source_path.exists():
            # Try relative to source root
            source_path = source_root / file_path
            if not source_path.exists():
                continue

        try:
            source_code = source_path.read_text(encoding="utf-8")
        except Exception:
            continue

        # Get all function/class definitions
        definitions = extract_code_definitions(source_code, recursive=True)

        # Analyze each function/class
        function_reports = []
        for defn in definitions:
            defn_lines = set(range(defn.start_line, defn.end_line + 1))
            function_executable_lines = (executed_lines | missing_lines) & defn_lines
            
            valid_executable_lines = function_executable_lines - excluded_lines
            
            defn_covered = valid_executable_lines & executed_lines
            defn_uncovered = valid_executable_lines & missing_lines

            total = len(valid_executable_lines)
            covered = len(defn_covered)
            pct = (covered / total * 100) if total > 0 else 0.0

            function_reports.append(
                FunctionCoverageReport(
                    name=defn.name,
                    type=defn.type,
                    start_line=defn.start_line,
                    end_line=defn.end_line,
                    total_lines=total,
                    covered_lines=covered,
                    uncovered_lines=sorted(defn_uncovered),
                    coverage_percentage=round(pct, 1),
                )
            )

        # File-level stats
        all_lines = executed_lines | missing_lines
        total_lines = len(all_lines - excluded_lines)
        covered_count = len(executed_lines - excluded_lines)
        file_pct = (covered_count / total_lines * 100) if total_lines > 0 else 0.0

        reports[file_path] = FileCoverageReport(
            file_path=file_path,
            total_lines=total_lines,
            covered_lines=covered_count,
            uncovered_lines=sorted(missing_lines),
            coverage_percentage=round(file_pct, 1),
            functions=function_reports,
        )

    return reports


def format_uncovered_areas(reports: Dict[str, FileCoverageReport]) -> str:
    """
    Formats uncovered areas into a string for LLM consumption.

    This maintains backward compatibility with the previous format.

    Args:
        reports: Dictionary of FileCoverageReport objects.

    Returns:
        String describing uncovered lines per file.
    """
    lines = []
    for file_path, report in reports.items():
        if report.uncovered_lines:
            # Group consecutive lines into ranges for readability
            ranges = _group_lines_to_ranges(report.uncovered_lines)
            lines.append(f"{file_path}: lines {ranges}")
    return "\n".join(lines) if lines else "No specific uncovered areas identified"


def _group_lines_to_ranges(line_numbers: List[int]) -> str:
    """Groups consecutive line numbers into ranges like '5-10, 15, 20-25'."""
    if not line_numbers:
        return ""

    ranges = []
    start = line_numbers[0]
    end = start

    for line in line_numbers[1:]:
        if line == end + 1:
            end = line
        else:
            ranges.append(f"{start}-{end}" if start != end else str(start))
            start = end = line

    ranges.append(f"{start}-{end}" if start != end else str(start))
    return ", ".join(ranges)


def get_overall_percentage(reports: Dict[str, FileCoverageReport]) -> float:
    """Calculates the overall coverage percentage across all files."""
    total = sum(r.total_lines for r in reports.values())
    covered = sum(r.covered_lines for r in reports.values())
    return round((covered / total * 100) if total > 0 else 0.0, 1)
