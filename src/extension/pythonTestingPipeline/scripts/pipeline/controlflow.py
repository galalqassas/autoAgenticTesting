"""Control-flow coverage analysis – branch coverage.

Walks the AST to identify branch constructs (if/elif/else, try/except,
for/while with else, match/case) and determines whether each arm was
executed by checking the coverage.json executed-lines set.
"""

import ast
from typing import List, Set

from pipeline.models import BranchArmReport, BranchCoverageReport, BranchReport

__all__ = ["analyze_branch_coverage"]


def _calc_pct(covered: int, total: int) -> float:
    return round((covered / total * 100) if total > 0 else 0.0, 1)


def _body_lines(nodes: List[ast.AST]) -> Set[int]:
    """Collect all line numbers spanned by a list of AST body nodes."""
    lines: Set[int] = set()
    for node in nodes:
        if hasattr(node, "lineno"):
            start = node.lineno
            end = getattr(node, "end_lineno", start) or start
            lines.update(range(start, end + 1))
    return lines


def _arm_covered(arm_lines: Set[int], executed: Set[int]) -> bool:
    """An arm is covered if *any* of its lines were executed."""
    return bool(arm_lines & executed)


def _analyze_if(node: ast.If, executed: Set[int]) -> List[BranchReport]:
    """Analyze an if/elif/else chain, returning one BranchReport per level."""
    reports: List[BranchReport] = []

    current: ast.AST = node
    while isinstance(current, ast.If):
        arms: List[BranchArmReport] = []

        # True-branch (body)
        body_lines = _body_lines(current.body)
        arms.append(BranchArmReport(
            arm_name="if-body" if current is node else "elif-body",
            start_line=current.lineno,
            covered=_arm_covered(body_lines, executed),
        ))

        orelse = current.orelse
        if orelse:
            if len(orelse) == 1 and isinstance(orelse[0], ast.If):
                # elif – will be handled in next iteration
                current = orelse[0]
                # Still record the body/True arm for this level
                reports.append(BranchReport(
                    lineno=arms[0].start_line,
                    construct="if",
                    arms=arms,
                    fully_covered=all(a.covered for a in arms),
                ))
                continue
            else:
                # else block
                else_lines = _body_lines(orelse)
                else_start = orelse[0].lineno if hasattr(orelse[0], "lineno") else current.lineno
                arms.append(BranchArmReport(
                    arm_name="else",
                    start_line=else_start,
                    covered=_arm_covered(else_lines, executed),
                ))
        else:
            # Implicit else (no else clause) – counts as an arm that is
            # "covered" when the if-condition evaluates to False, which we
            # approximate as "covered" if the if-body was NOT the only path.
            # Since we cannot know from line traces alone, we still record it
            # so the report is informative, but mark it covered when the
            # if-header line is executed (the branch was evaluated).
            arms.append(BranchArmReport(
                arm_name="implicit-else",
                start_line=current.lineno,
                covered=current.lineno in executed,
            ))

        reports.append(BranchReport(
            lineno=current.lineno,
            construct="if",
            arms=arms,
            fully_covered=all(a.covered for a in arms),
        ))
        break  # No more elif chain

    return reports


def _analyze_try(node: ast.Try, executed: Set[int]) -> BranchReport:
    """Analyze a try/except/else/finally construct."""
    arms: List[BranchArmReport] = []

    # try body
    body_lines = _body_lines(node.body)
    arms.append(BranchArmReport(
        arm_name="try-body",
        start_line=node.lineno,
        covered=_arm_covered(body_lines, executed),
    ))

    # except handlers
    for handler in node.handlers:
        handler_lines = _body_lines(handler.body)
        exc_name = handler.type.id if handler.type and isinstance(handler.type, ast.Name) else "bare"
        arms.append(BranchArmReport(
            arm_name=f"except:{exc_name}",
            start_line=handler.lineno,
            covered=_arm_covered(handler_lines, executed),
        ))

    # else
    if node.orelse:
        else_lines = _body_lines(node.orelse)
        else_start = node.orelse[0].lineno if hasattr(node.orelse[0], "lineno") else node.lineno
        arms.append(BranchArmReport(
            arm_name="try-else",
            start_line=else_start,
            covered=_arm_covered(else_lines, executed),
        ))

    # finally
    if node.finalbody:
        finally_lines = _body_lines(node.finalbody)
        finally_start = node.finalbody[0].lineno if hasattr(node.finalbody[0], "lineno") else node.lineno
        arms.append(BranchArmReport(
            arm_name="finally",
            start_line=finally_start,
            covered=_arm_covered(finally_lines, executed),
        ))

    return BranchReport(
        lineno=node.lineno,
        construct="try",
        arms=arms,
        fully_covered=all(a.covered for a in arms),
    )


def _analyze_loop(node, executed: Set[int]) -> BranchReport:
    """Analyze for/while with optional else."""
    construct = "for" if isinstance(node, ast.For) else "while"
    arms: List[BranchArmReport] = []

    body_lines = _body_lines(node.body)
    arms.append(BranchArmReport(
        arm_name=f"{construct}-body",
        start_line=node.lineno,
        covered=_arm_covered(body_lines, executed),
    ))

    if node.orelse:
        else_lines = _body_lines(node.orelse)
        else_start = node.orelse[0].lineno if hasattr(node.orelse[0], "lineno") else node.lineno
        arms.append(BranchArmReport(
            arm_name=f"{construct}-else",
            start_line=else_start,
            covered=_arm_covered(else_lines, executed),
        ))

    return BranchReport(
        lineno=node.lineno,
        construct=construct,
        arms=arms,
        fully_covered=all(a.covered for a in arms),
    )


def _analyze_match(node, executed: Set[int]) -> BranchReport:
    """Analyze match/case (Python 3.10+)."""
    arms: List[BranchArmReport] = []

    for case_node in node.cases:
        case_lines = _body_lines(case_node.body)
        # Use the pattern description if available
        pattern_str = ast.dump(case_node.pattern) if case_node.pattern else "default"
        # Truncate for readability
        if len(pattern_str) > 40:
            pattern_str = pattern_str[:37] + "..."
        arms.append(BranchArmReport(
            arm_name=f"case:{pattern_str}",
            start_line=case_node.lineno if hasattr(case_node, "lineno") else node.lineno,
            covered=_arm_covered(case_lines, executed),
        ))

    return BranchReport(
        lineno=node.lineno,
        construct="match",
        arms=arms,
        fully_covered=all(a.covered for a in arms),
    )


def analyze_branch_coverage(
    source_code: str,
    executed_lines: Set[int],
) -> BranchCoverageReport:
    """Compute branch coverage for a single source file.

    Args:
        source_code: The full text of the Python source file.
        executed_lines: Lines executed during testing (from coverage.json).

    Returns:
        A populated BranchCoverageReport.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return BranchCoverageReport(
            total_branches=0,
            fully_covered=0,
            partially_covered=0,
            uncovered=0,
            branches=[],
            coverage_percentage=0.0,
        )

    all_branches: List[BranchReport] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            # Only process top-level ifs; elif chains are handled inside _analyze_if
            # Skip nodes that are the orelse of a parent If (they'll be visited
            # by _analyze_if when processing the parent).
            all_branches.extend(_analyze_if(node, executed_lines))
        elif isinstance(node, ast.Try):
            all_branches.append(_analyze_try(node, executed_lines))
        elif isinstance(node, (ast.For, ast.While)):
            # Only create a branch report if there's an else clause or if
            # we want to track body execution; loops with else are true
            # branch constructs.
            if node.orelse:
                all_branches.append(_analyze_loop(node, executed_lines))
        elif hasattr(ast, "Match") and isinstance(node, ast.Match):
            all_branches.append(_analyze_match(node, executed_lines))

    # Deduplicate: _analyze_if may re-visit elif nodes already seen via
    # ast.walk.  Deduplicate by (lineno, construct).
    seen = set()
    unique: List[BranchReport] = []
    for br in all_branches:
        key = (br.lineno, br.construct)
        if key not in seen:
            seen.add(key)
            unique.append(br)
    all_branches = unique

    fully = sum(1 for b in all_branches if b.fully_covered)
    total = len(all_branches)
    # A branch with at least one covered arm but not all
    partial = sum(
        1 for b in all_branches
        if not b.fully_covered and any(a.covered for a in b.arms)
    )
    uncovered = total - fully - partial

    return BranchCoverageReport(
        total_branches=total,
        fully_covered=fully,
        partially_covered=partial,
        uncovered=uncovered,
        branches=all_branches,
        coverage_percentage=_calc_pct(fully, total),
    )
