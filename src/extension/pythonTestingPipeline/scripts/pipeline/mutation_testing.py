"""Mutation testing module for the Python Testing Pipeline.

Uses mutmut to measure test effectiveness by injecting small bugs (mutants)
into the source code and checking whether tests catch them.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from pipeline.coverage import FileCoverageReport, analyze_coverage
from pipeline.models import MutantInfo, MutationCoverageReport

__all__ = [
    "should_enable_mutation_testing",
    "should_mutate_file",
    "run_mutation_testing",
    "format_mutation_feedback",
]


def should_enable_mutation_testing(
    current_coverage: float,
    previous_coverage: float,
    iteration: int,
) -> bool:
    """Determine whether mutation testing should run this iteration.

    Mutation testing is expensive. It is enabled only when:
    - We have completed at least 2 full iterations (iteration >= 3), AND
    - Coverage improvement has plateaued (delta < 3%), OR
    - Coverage is already high enough (>= 92%) that quality matters more.

    Args:
        current_coverage: Coverage percentage from the latest test run.
        previous_coverage: Coverage percentage from the previous iteration.
        iteration: 1-based current iteration number.

    Returns:
        True if mutation testing should be executed.
    """
    if iteration < 3:
        return False

    coverage_delta = current_coverage - previous_coverage

    if coverage_delta < 3.0:
        print(
            f"   Coverage delta ({coverage_delta:.1f}%) < 3% "
            "- Enabling mutation testing"
        )
        return True

    if current_coverage >= 92.0:
        print(
            f"   Coverage at {current_coverage:.1f}% "
            "- Enabling mutation testing"
        )
        return True

    return False


def should_mutate_file(file_coverage: FileCoverageReport) -> bool:
    """Determine if a file has enough coverage to benefit from mutation testing.

    Only files with >= 95% line coverage are worth mutating.  Mutating
    poorly-covered code wastes time because uncovered mutants cannot be
    killed by tests that never execute those lines.

    Args:
        file_coverage: Coverage report for the file.

    Returns:
        True if the file should be included in mutation testing.
    """
    return file_coverage.coverage_percentage >= 95.0


def _generate_coverage_xml(test_file: Path, codebase_path: Path) -> Optional[Path]:
    """Generate coverage.xml required by mutmut's ``--use-coverage`` flag.

    Args:
        test_file: Path to the test file.
        codebase_path: Root path of the source code.

    Returns:
        Path to the generated coverage.xml, or None on failure.
    """
    xml_path = codebase_path / "coverage.xml"
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        "-q",
        "--timeout=30",
        f"--cov={codebase_path}",
        "--cov-report=xml",
        "--no-header",
    ]
    try:
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=test_file.parent.parent,
        )
        if xml_path.exists():
            return xml_path
    except (subprocess.TimeoutExpired, Exception) as exc:
        print(f"   Failed to generate coverage.xml: {exc}")
    return None


def _parse_mutmut_output(output: str) -> Dict[str, int]:
    """Parse mutmut CLI output to extract result counts.

    Mutmut prints a summary such as::

        284 mutants tested.  Dead: 250  Survived: 30  Timeout: 4

    This function extracts those counts.

    Args:
        output: Combined stdout+stderr from a mutmut run.

    Returns:
        Dict with keys: killed, survived, timeout, suspicious, total.
    """
    counts = {
        "killed": 0,
        "survived": 0,
        "timeout": 0,
        "suspicious": 0,
        "total": 0,
    }

    # mutmut summary line
    killed_match = re.search(r"Dead:\s*(\d+)", output, re.IGNORECASE)
    survived_match = re.search(r"Survived:\s*(\d+)", output, re.IGNORECASE)
    timeout_match = re.search(r"Timeout:\s*(\d+)", output, re.IGNORECASE)
    suspicious_match = re.search(r"Suspicious:\s*(\d+)", output, re.IGNORECASE)
    total_match = re.search(r"(\d+)\s*mutants?\s*tested", output, re.IGNORECASE)

    if killed_match:
        counts["killed"] = int(killed_match.group(1))
    if survived_match:
        counts["survived"] = int(survived_match.group(1))
    if timeout_match:
        counts["timeout"] = int(timeout_match.group(1))
    if suspicious_match:
        counts["suspicious"] = int(suspicious_match.group(1))
    if total_match:
        counts["total"] = int(total_match.group(1))
    else:
        counts["total"] = (
            counts["killed"]
            + counts["survived"]
            + counts["timeout"]
            + counts["suspicious"]
        )

    return counts


def _collect_survived_mutants(codebase_path: Path, limit: int = 20) -> List[MutantInfo]:
    """Collect details of survived mutants via ``mutmut show``.

    Args:
        codebase_path: Root directory where mutmut was run.
        limit: Maximum number of survived mutants to retrieve.

    Returns:
        List of MutantInfo dataclass instances for survived mutants.
    """
    survived: List[MutantInfo] = []

    # First, get the list of survived mutant IDs via ``mutmut results``
    try:
        result = subprocess.run(
            [sys.executable, "-m", "mutmut", "results"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(codebase_path),
        )
        output = result.stdout
    except Exception:
        return survived

    # mutmut results outputs lines like:
    # Survived mutants:
    #   mutmut 1
    #   mutmut 5
    mutant_ids: List[str] = []
    in_survived_section = False
    for line in output.splitlines():
        stripped = line.strip()
        if "survived" in stripped.lower() and ":" in stripped:
            in_survived_section = True
            continue
        if in_survived_section:
            # Lines look like "mutmut 1" or just an id
            id_match = re.search(r"(\d+)", stripped)
            if id_match:
                mutant_ids.append(id_match.group(1))
            elif stripped == "" or ":" in stripped:
                # End of survived section or start of another section
                in_survived_section = False

    # Retrieve details for each survived mutant (up to limit)
    for mid in mutant_ids[:limit]:
        try:
            show_result = subprocess.run(
                [sys.executable, "-m", "mutmut", "show", mid],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(codebase_path),
            )
            show_output = show_result.stdout

            # Parse the diff-like output from mutmut show
            file_path = ""
            line_number = 0
            original_code = ""
            mutated_code = ""

            for show_line in show_output.splitlines():
                if show_line.startswith("--- "):
                    file_path = show_line[4:].strip()
                elif show_line.startswith("-") and not show_line.startswith("---"):
                    original_code = show_line[1:].strip()
                elif show_line.startswith("+") and not show_line.startswith("+++"):
                    mutated_code = show_line[1:].strip()
                elif show_line.startswith("@@"):
                    line_match = re.search(r"\+(\d+)", show_line)
                    if line_match:
                        line_number = int(line_match.group(1))

            survived.append(
                MutantInfo(
                    mutant_id=mid,
                    status="survived",
                    file_path=file_path,
                    line_number=line_number,
                    original_code=original_code,
                    mutated_code=mutated_code,
                )
            )
        except Exception:
            continue

    return survived


def run_mutation_testing(
    codebase_path: Path,
    test_file: Path,
    min_file_coverage: float = 95.0,
    timeout: int = 600,
) -> MutationCoverageReport:
    """Run mutation testing on well-covered source files.

    Only files with line coverage >= *min_file_coverage* are mutated.
    Uses ``mutmut run`` under the hood.

    Args:
        codebase_path: Root of the source code under test.
        test_file: Path to the pytest test file.
        min_file_coverage: Minimum line-coverage percentage for a file
            to be included in mutation testing.
        timeout: Maximum wall-clock seconds for the mutmut run.

    Returns:
        A populated MutationCoverageReport.
    """
    empty_report = MutationCoverageReport(
        mutation_score=0.0,
        total_mutants=0,
        killed=0,
        survived=0,
        timeout=0,
        suspicious=0,
        survived_mutants=[],
    )

    # --- Determine which files to mutate ---
    coverage_json_path = codebase_path / "coverage.json"
    if coverage_json_path.exists():
        reports = analyze_coverage(coverage_json_path, codebase_path)
        files_to_mutate = [
            fp for fp, report in reports.items() if report.coverage_percentage >= min_file_coverage
        ]
    else:
        # No coverage data available – mutate everything
        files_to_mutate = [
            str(p) for p in codebase_path.rglob("*.py")
            if "test" not in p.name.lower() and "__pycache__" not in str(p)
        ]

    if not files_to_mutate:
        print(
            f"   No files with >={min_file_coverage}% coverage "
            "- skipping mutation testing"
        )
        return empty_report

    print(
        f"   Mutating {len(files_to_mutate)} file(s) "
        f"with >={min_file_coverage}% coverage"
    )

    # --- Generate coverage.xml for mutmut ---
    coverage_xml = _generate_coverage_xml(test_file, codebase_path)

    # --- Build mutmut command ---
    paths_arg = ",".join(files_to_mutate)
    cmd = [
        sys.executable,
        "-m",
        "mutmut",
        "run",
        f"--paths-to-mutate={paths_arg}",
        f"--tests-dir={test_file.parent}",
    ]
    if coverage_xml and coverage_xml.exists():
        cmd.append("--use-coverage")

    # --- Execute mutmut ---
    print("   Running mutation testing (this may take several minutes)...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(codebase_path),
        )
        output = result.stdout + "\n" + result.stderr
    except subprocess.TimeoutExpired:
        print(f"   Mutation testing timed out after {timeout}s")
        return empty_report
    except Exception as exc:
        print(f"   Mutation testing failed: {exc}")
        return empty_report

    # --- Parse results ---
    counts = _parse_mutmut_output(output)

    killed = counts["killed"]
    survived_count = counts["survived"]
    timeout_count = counts["timeout"]
    suspicious = counts["suspicious"]
    total = counts["total"]

    denominator = killed + survived_count
    mutation_score = (killed / denominator * 100) if denominator > 0 else 0.0

    print(f"   Mutation Score: {mutation_score:.1f}%")
    print(
        f"   Total: {total} | Killed: {killed} | "
        f"Survived: {survived_count} | Timeout: {timeout_count}"
    )

    # --- Collect survived mutant details ---
    survived_mutants: List[MutantInfo] = []
    if survived_count > 0:
        survived_mutants = _collect_survived_mutants(codebase_path, limit=20)

    return MutationCoverageReport(
        mutation_score=round(mutation_score, 1),
        total_mutants=total,
        killed=killed,
        survived=survived_count,
        timeout=timeout_count,
        suspicious=suspicious,
        survived_mutants=survived_mutants,
    )


def format_mutation_feedback(report: MutationCoverageReport) -> str:
    """Format a MutationCoverageReport into a human-readable string.

    The output is designed to be included in LLM prompts so the
    evaluation and implementation agents can act on weak spots.

    Args:
        report: The mutation coverage report to format.

    Returns:
        A formatted multi-line string summarising the mutation results.
    """
    if report.total_mutants == 0:
        return "Mutation testing was not run or produced no mutants."

    lines = [
        f"Mutation Coverage: {report.mutation_score:.1f}%",
        f"Total Mutants: {report.total_mutants} | "
        f"Killed: {report.killed} | "
        f"Survived: {report.survived} | "
        f"Timeout: {report.timeout}",
    ]

    if report.survived_mutants:
        lines.append("")
        lines.append("Survived Mutants (weaknesses in tests):")
        for i, mutant in enumerate(report.survived_mutants, 1):
            location = mutant.file_path or "unknown"
            if mutant.line_number:
                location += f":{mutant.line_number}"
            lines.append(f"  {i}. {location}")
            if mutant.original_code:
                lines.append(f"     Original: {mutant.original_code}")
            if mutant.mutated_code:
                lines.append(f"     Mutant:   {mutant.mutated_code}")
            lines.append(
                "     -> Tests did not detect this change. "
                "Add an assertion that covers this behaviour."
            )

    return "\n".join(lines)
