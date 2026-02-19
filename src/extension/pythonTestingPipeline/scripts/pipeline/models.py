"""Data models for Python Testing Pipeline."""

from dataclasses import dataclass, field
from typing import List, Optional

__all__ = [
    "TestScenario",
    "TestScenariosOutput",
    "ExecutionSummary",
    "SecurityIssue",
    "TestEvaluationOutput",
    "MutantInfo",
    "MutationCoverageReport",
    # Statement coverage
    "StatementCoverageReport",
    # Branch coverage
    "BranchArmReport",
    "BranchReport",
    "BranchCoverageReport",
]


@dataclass
class TestScenario:
    """Represents a single test scenario."""

    scenario_description: str
    priority: str  # "High", "Medium", or "Low"


@dataclass
class TestScenariosOutput:
    """Output from the Test Case Identification Agent."""

    test_scenarios: List[TestScenario]


@dataclass
class ExecutionSummary:
    """Summary of test execution."""

    total_tests: int
    passed: int
    failed: int


@dataclass
class MutantInfo:
    """Information about a single mutant."""

    mutant_id: str
    status: str  # 'killed', 'survived', 'timeout', 'suspicious'
    file_path: str
    line_number: int
    original_code: str
    mutated_code: str


@dataclass
class MutationCoverageReport:
    """Mutation testing results."""

    mutation_score: float  # percentage of mutants killed
    total_mutants: int
    killed: int
    survived: int
    timeout: int
    suspicious: int
    survived_mutants: List[MutantInfo] = field(default_factory=list)


@dataclass
class SecurityIssue:
    """Represents a security issue found in the code."""

    severity: str  # "critical", "high", "medium", "low"
    issue: str
    location: str
    recommendation: str


@dataclass
class TestEvaluationOutput:
    """Output from the Test Case Evaluation Agent."""

    execution_summary: ExecutionSummary
    code_coverage_percentage: float
    actionable_recommendations: List[str]
    security_issues: List[SecurityIssue] = field(default_factory=list)
    has_severe_security_issues: bool = False
    mutation_score: float = 0.0
    mutation_report: Optional[MutationCoverageReport] = None


# ── Statement Coverage ──────────────────────────────────────────────


@dataclass
class StatementCoverageReport:
    """Statement-level coverage for a single file.

    Each AST statement node (Assign, Return, Expr, Raise, Assert, …) is
    mapped to executed_lines from coverage.json.  Multiple statements
    sharing the same ``lineno`` are counted once per line.
    """

    total_statements: int
    covered_statements: int
    uncovered_statement_lines: List[int] = field(default_factory=list)
    coverage_percentage: float = 0.0


# ── Branch Coverage ─────────────────────────────────────────────────


@dataclass
class BranchArmReport:
    """One arm of a branch construct (e.g. the 'body' or 'orelse' of an if)."""

    arm_name: str  # e.g. "if-body", "else", "except:ValueError"
    start_line: int
    covered: bool


@dataclass
class BranchReport:
    """A single branch construct (if, try, for/while with else, match)."""

    lineno: int
    construct: str  # "if", "try", "for", "while", "match"
    arms: List[BranchArmReport] = field(default_factory=list)
    fully_covered: bool = False


@dataclass
class BranchCoverageReport:
    """Aggregated branch coverage for a single file."""

    total_branches: int
    fully_covered: int
    partially_covered: int
    uncovered: int
    branches: List[BranchReport] = field(default_factory=list)
    coverage_percentage: float = 0.0
