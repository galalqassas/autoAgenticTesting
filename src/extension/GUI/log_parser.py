"""Log parser for extracting metrics from pipeline output."""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParseResult:
    """Parsed data from a log line."""

    phase_update: Optional[tuple[str, str]] = None  # (phase_name, state) - last update
    phase_updates: Optional[list[tuple[str, str]]] = None  # All phase updates
    coverage: Optional[str] = None
    tests: Optional[tuple[str, str, int]] = None  # (passed, total, failed)
    scenarios: Optional[str] = None
    security_issues: Optional[str] = None
    security_severity: Optional[str] = None  # "none", "low", or count


class LogParser:
    """Parses pipeline log output and extracts metrics."""

    # Phase detection patterns: (regex, [(phase, state), ...])
    # Multiple phase updates can be triggered by a single pattern
    PHASE_PATTERNS = [
        (r"Agent 1: Identifying|Identifying test scenarios", [("identify", "active")]),
        (
            r"Agent 2: Generating|Generating PyTest",
            [("identify", "completed"), ("implement", "active")],
        ),
        (
            r"Iteration|Running tests",
            [("implement", "completed"), ("verify", "active")],
        ),
        (r"Pipeline Complete|All targets met", [("verify", "completed")]),
    ]

    # Metric extraction patterns
    COVERAGE_PATTERN = re.compile(
        r"(?:Coverage|coverage)(?:\s*measured)?:\s*(\d+(?:\.\d+)?)\s*%"
    )
    TESTS_PATTERN = re.compile(r"Tests:\s*(\d+)/(\d+)\s*passed", re.IGNORECASE)
    SCENARIOS_PATTERN = re.compile(
        r"(?:Identified|Scenarios:)\s*(\d+)\s*(?:scenarios)?"
    )
    SECURITY_FOUND_PATTERN = re.compile(r"Security issues found:\s*(\d+)")
    SECURITY_MINOR_PATTERN = re.compile(r"Minor security issues.*?:\s*(\d+)")
    SECURITY_SEVERE_PATTERN = re.compile(r"Severe security issues:\s*(\w+)")

    def parse(self, line: str) -> ParseResult:
        """Parse a log line and return extracted data."""
        result = ParseResult()

        # Check phase updates - patterns can trigger multiple phase changes
        for pattern, updates in self.PHASE_PATTERNS:
            if re.search(pattern, line):
                result.phase_update = updates[-1]
                result.phase_updates = updates
                break

        # Extract metrics using pattern matching
        if match := self.COVERAGE_PATTERN.search(line):
            result.coverage = match.group(1)

        if match := self.TESTS_PATTERN.search(line):
            passed, total = match.groups()
            result.tests = (passed, total, int(total) - int(passed))

        if match := self.SCENARIOS_PATTERN.search(line):
            result.scenarios = match.group(1)

        # Extract security info (check patterns in priority order)
        for pattern, extractor in [
            (
                self.SECURITY_FOUND_PATTERN,
                lambda m: setattr(result, "security_issues", m.group(1)),
            ),
            (
                self.SECURITY_MINOR_PATTERN,
                lambda m: setattr(result, "security_severity", m.group(1)),
            ),
            (
                self.SECURITY_SEVERE_PATTERN,
                lambda m: setattr(
                    result,
                    "security_severity",
                    "none" if m.group(1).lower() == "none" else m.group(1),
                ),
            ),
        ]:
            if match := pattern.search(line):
                extractor(match)
                break

        return result
