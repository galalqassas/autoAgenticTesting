"""Coverage analysis module for the Python Testing Pipeline."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

from pipeline.code_utils import extract_code_definitions

__all__ = ["FileCoverageReport", "FunctionCoverageReport", "analyze_coverage", "format_uncovered_areas", "get_overall_percentage"]


@dataclass
class FunctionCoverageReport:
    """Coverage report for a single function or class."""
    name: str
    type: str
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


def _calc_pct(covered: int, total: int) -> float:
    """Calculate percentage, handling zero division."""
    return round((covered / total * 100) if total > 0 else 0.0, 1)


def _group_lines_to_ranges(lines: List[int]) -> str:
    """Group consecutive line numbers into ranges like '5-10, 15, 20-25'."""
    if not lines:
        return ""

    ranges, start, end = [], lines[0], lines[0]
    for line in lines[1:]:
        if line == end + 1:
            end = line
        else:
            ranges.append(f"{start}-{end}" if start != end else str(start))
            start = end = line
    ranges.append(f"{start}-{end}" if start != end else str(start))
    return ", ".join(ranges)


def analyze_coverage(coverage_json_path: Path, source_root: Path) -> Dict[str, FileCoverageReport]:
    """Analyze coverage data and map it to code definitions."""
    if not coverage_json_path.exists():
        return {}

    with open(coverage_json_path, "r", encoding="utf-8") as f:
        coverage_data = json.load(f)

    reports = {}
    for file_path, file_data in coverage_data.get("files", {}).items():
        executed: Set[int] = set(file_data.get("executed_lines", []))
        missing: Set[int] = set(file_data.get("missing_lines", []))
        excluded: Set[int] = set(file_data.get("excluded_lines", []))

        # Resolve source path
        source_path = Path(file_path)
        if not source_path.exists():
            source_path = source_root / file_path
            if not source_path.exists():
                continue

        try:
            source_code = source_path.read_text(encoding="utf-8")
        except Exception:
            continue

        # Analyze each function/class
        function_reports = []
        for defn in extract_code_definitions(source_code, recursive=True):
            defn_lines = set(range(defn.start_line, defn.end_line + 1))
            executable = ((executed | missing) & defn_lines) - excluded
            defn_covered = executable & executed
            defn_uncovered = executable & missing

            function_reports.append(FunctionCoverageReport(
                name=defn.name,
                type=defn.type,
                start_line=defn.start_line,
                end_line=defn.end_line,
                total_lines=len(executable),
                covered_lines=len(defn_covered),
                uncovered_lines=sorted(defn_uncovered),
                coverage_percentage=_calc_pct(len(defn_covered), len(executable)),
            ))

        # File-level stats
        all_lines = (executed | missing) - excluded
        covered_count = len(executed - excluded)

        reports[file_path] = FileCoverageReport(
            file_path=file_path,
            total_lines=len(all_lines),
            covered_lines=covered_count,
            uncovered_lines=sorted(missing),
            coverage_percentage=_calc_pct(covered_count, len(all_lines)),
            functions=function_reports,
        )

    return reports


def format_uncovered_areas(reports: Dict[str, FileCoverageReport]) -> str:
    """Format uncovered areas into a string for LLM consumption."""
    lines = [
        f"{fp}: lines {_group_lines_to_ranges(r.uncovered_lines)}"
        for fp, r in reports.items() if r.uncovered_lines
    ]
    return "\n".join(lines) if lines else "No specific uncovered areas identified"


def get_overall_percentage(reports: Dict[str, FileCoverageReport]) -> float:
    """Calculate overall coverage percentage across all files."""
    total = sum(r.total_lines for r in reports.values())
    covered = sum(r.covered_lines for r in reports.values())
    return _calc_pct(covered, total)
