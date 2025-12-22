#!/usr/bin/env python3
"""
Python Automated Testing Pipeline

Usage:
    python pythonTestingPipeline.py <codebase_path> [--coverage] [--auto-approve] [--no-run-tests]

Note:
    Generated tests are run by default unless --no-run-tests is supplied.

Example:
    python pythonTestingPipeline.py ./my_project --auto-approve
"""

import argparse

import json

import re

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

# Import LLM configuration and client
from llm_config import create_llm_client
# ==================== Type Definitions ====================

from pipeline.models import (
    TestScenariosOutput,
    TestEvaluationOutput,
)

# ==================== System Prompts ====================

from pipeline.test_runner import (
    extract_dependencies,
    install_dependencies,
    run_tests,
)
from pipeline.agents import (
    IdentificationAgent,
    ImplementationAgent,
    EvaluationAgent,
)


# ==================== Pipeline Implementation ====================


class PythonTestingPipeline:
    """Orchestrates the three-agent testing pipeline."""

    def __init__(self, model: Optional[str] = None):
        # Use the LLM client from llm_config for automatic API key rotation and model fallback
        self.llm_client = create_llm_client(use_mock_on_failure=False)
        self.prompt_history = []  # Track all prompts for later analysis

        # Initialize agents
        self.identification_agent = IdentificationAgent(
            self.llm_client, self.prompt_history
        )
        self.implementation_agent = ImplementationAgent(
            self.llm_client, self.prompt_history
        )
        self.evaluation_agent = EvaluationAgent(self.llm_client, self.prompt_history)

        # Print current configuration
        if self.llm_client.current_api_key:
            print(f"Using model: {self.llm_client.current_model}")

    @property
    def model(self) -> str:
        """Get current model from LLM client."""
        return self.llm_client.current_model

    def save_prompts(self, output_dir: Path, run_id: str = None) -> Path:
        """Saves all prompts from this run to a JSON file."""
        import time as time_module

        if run_id is None:
            run_id = time_module.strftime("%Y%m%d_%H%M%S")

        prompts_file = output_dir / f"prompts_{run_id}.json"

        prompt_data = {
            "run_id": run_id,
            "timestamp": time_module.strftime("%Y-%m-%d %H:%M:%S"),
            "model": self.model,
            "total_prompts": len(self.prompt_history),
            "prompts": self.prompt_history,
        }

        output_dir.mkdir(parents=True, exist_ok=True)
        with open(prompts_file, "w", encoding="utf-8") as f:
            json.dump(prompt_data, f, indent=2, default=str)

        print(f"   Prompts saved: {prompts_file}")
        return prompts_file

    def identify_test_scenarios(self, codebase_path: Path) -> TestScenariosOutput:
        """Agent 1: Identifies test scenarios from the codebase using parallel processing."""
        return self.identification_agent.run(codebase_path)

    def request_approval(self, scenarios: TestScenariosOutput) -> TestScenariosOutput:
        """
        Presents scenarios for human approval.
        """
        print("\n📋 Test Scenarios for Approval:")
        print("-" * 60)

        for i, scenario in enumerate(scenarios.test_scenarios, 1):
            print(f"{i}. [{scenario.priority}] {scenario.scenario_description}")

        print("-" * 60)
        print(f"\nTotal: {len(scenarios.test_scenarios)} scenarios")

        while True:
            response = input("\nApprove all scenarios? (yes/no/edit): ").strip().lower()

            if response in ("yes", "y"):
                return scenarios
            elif response in ("no", "n"):
                raise ValueError("Scenarios not approved")
            elif response in ("edit", "e"):
                # Simple editing - remove scenarios by number
                to_remove = input(
                    "Enter scenario numbers to remove (comma-separated): "
                ).strip()
                if to_remove:
                    indices_to_remove = set(
                        int(x.strip()) - 1 for x in to_remove.split(",")
                    )
                    scenarios.test_scenarios = [
                        s
                        for i, s in enumerate(scenarios.test_scenarios)
                        if i not in indices_to_remove
                    ]
                return scenarios
            else:
                print("Please enter 'yes', 'no', or 'edit'")

    def generate_test_code(
        self, scenarios: TestScenariosOutput, codebase_path: Path, output_dir: Path
    ) -> tuple[str, Path]:
        """Agent 2: Generates PyTest test code from approved scenarios."""
        return self.implementation_agent.run(scenarios, codebase_path, output_dir)

    def _extract_uncovered_areas(self, test_output: str) -> str:
        """Extracts uncovered lines/areas from pytest-cov output."""
        uncovered_lines = []

        # Try to extract from term-missing format: "file.py   10   2   80%   5-6"
        missing_pattern = r"^(.+\.py)\s+\d+\s+\d+\s+\d+%\s+(.+)$"
        for line in test_output.split("\n"):
            match = re.match(missing_pattern, line.strip())
            if match and match.group(2).strip():
                uncovered_lines.append(f"{match.group(1)}: lines {match.group(2)}")

        # Also check coverage.json for detailed missing lines
        try:
            coverage_json = Path("coverage.json")
            if coverage_json.exists():
                with open(coverage_json, "r") as f:
                    data = json.load(f)
                    for file_path, file_data in data.get("files", {}).items():
                        missing = file_data.get("missing_lines", [])
                        if missing:
                            uncovered_lines.append(f"{file_path}: lines {missing[:20]}")
        except Exception:
            pass

        return (
            "\n".join(uncovered_lines)
            if uncovered_lines
            else "No specific uncovered areas identified"
        )

    def evaluate_results(
        self, test_results: dict, scenarios: TestScenariosOutput, codebase_path: Path
    ) -> TestEvaluationOutput:
        """Agent 3: Evaluates test results, coverage, and security."""
        return self.evaluation_agent.run(test_results, scenarios, codebase_path)

    def generate_additional_tests(
        self,
        codebase_path: Path,
        existing_test_file: Path,
        coverage_percentage: float,
        uncovered_areas: str,
        syntax_errors: str = "",
        security_issues: list = None,
    ) -> tuple[str, Path]:
        """Generates additional tests to improve coverage and address security issues."""
        return self.implementation_agent.improve_tests(
            codebase_path,
            existing_test_file,
            coverage_percentage,
            uncovered_areas,
            syntax_errors,
            security_issues,
        )

    def run_pipeline(
        self,
        codebase_path: Path,
        output_dir: Optional[Path] = None,
        should_run_tests: bool = True,
        coverage: bool = False,
        auto_approve: bool = False,
    ) -> dict:
        """
        Runs the complete testing pipeline.
        """
        print("=" * 60)
        print("🚀 Python Automated Testing Pipeline")
        print("=" * 60)

        output_dir = output_dir or codebase_path / "tests"
        results = {"status": "started"}

        try:
            # Step 1: Identify scenarios
            scenarios = self.identify_test_scenarios(codebase_path)
            results["identified_scenarios"] = asdict(scenarios)

            # Step 2: Get approval
            if auto_approve:
                approved_scenarios = scenarios
            else:
                approved_scenarios = self.request_approval(scenarios)
            results["approved_scenarios"] = asdict(approved_scenarios)

            # Step 3: Generate tests
            test_code, test_file = self.generate_test_code(
                approved_scenarios, codebase_path, output_dir
            )
            results["test_file"] = str(test_file)
            results["test_code"] = test_code

            # Step 4: Install dependencies
            if should_run_tests:
                deps = extract_dependencies(test_code)
                if deps:
                    dep_output, dep_exit = install_dependencies(deps, codebase_path)
                    results["dependencies_installed"] = deps
                    results["dependency_output"] = dep_output

            # Step 5: Run tests with coverage and improvement loop
            if should_run_tests:
                target_coverage = 90.0
                max_iterations = 15  # Safety limit to prevent infinite loops
                current_test_file = test_file
                current_test_code = test_code
                iteration = 0

                # Track progress to prevent getting stuck
                best_coverage = 0.0
                best_test_code = None  # Will store snapshot of best test code
                best_severe_count = float("inf")
                consecutive_no_progress = 0

                while iteration < max_iterations:
                    iteration += 1
                    print(f"\n--- Iteration {iteration} ---")

                    # Run tests with coverage
                    test_results = run_tests(current_test_file, codebase_path)
                    results["test_output"] = test_results["output"]
                    results["exit_code"] = test_results["exit_code"]

                    # Step 6: Evaluate results (includes security analysis)
                    evaluation = self.evaluate_results(
                        test_results, approved_scenarios, codebase_path
                    )
                    results["evaluation"] = asdict(evaluation)

                    current_coverage = evaluation.code_coverage_percentage
                    has_severe_security = evaluation.has_severe_security_issues
                    security_issues = evaluation.security_issues

                    # Check completion criteria: coverage >= 90% AND no severe security issues
                    coverage_met = current_coverage >= target_coverage
                    security_met = not has_severe_security

                    if coverage_met and security_met:
                        print("\n✅ All targets met!")
                        print(
                            f"   Coverage: {current_coverage:.1f}% (≥{target_coverage}%)"
                        )
                        print("   Severe security issues: None")
                        if security_issues:
                            low_med = [
                                si
                                for si in security_issues
                                if si.severity in ("low", "medium")
                            ]
                            if low_med:
                                print(
                                    f"   ℹ️  Minor security issues (low/medium): {len(low_med)}"
                                )
                        break

                    # Check for progress
                    current_severe_count = sum(
                        1
                        for si in security_issues
                        if si.severity in ("critical", "high")
                    )

                    progress_made = False
                    if current_coverage > best_coverage:
                        best_coverage = current_coverage
                        # Snapshot the current test code (strings are immutable, so assignment is safe)
                        best_test_code = current_test_code
                        progress_made = True

                    if current_severe_count < best_severe_count:
                        best_severe_count = current_severe_count
                        progress_made = True

                    if progress_made:
                        consecutive_no_progress = 0
                    else:
                        consecutive_no_progress += 1

                    if consecutive_no_progress >= 5:
                        print(
                            f"\n⚠️  No progress made for {consecutive_no_progress} iterations. Stopping early to prevent infinite loop."
                        )
                        print(f"   Best coverage: {best_coverage:.1f}%")
                        print(f"   Lowest severe issues: {best_severe_count}")
                        break

                    # Log current status
                    status_parts = []
                    if not coverage_met:
                        status_parts.append(
                            f"coverage {current_coverage:.1f}% < {target_coverage}%"
                        )
                    if not security_met:
                        severe_count = sum(
                            1
                            for si in security_issues
                            if si.severity in ("critical", "high")
                        )
                        status_parts.append(f"{severe_count} severe security issue(s)")
                    print(f"   ⚠️  Needs improvement: {', '.join(status_parts)}")

                    # Extract uncovered areas from test output
                    uncovered_areas = self._extract_uncovered_areas(
                        test_results["output"]
                    )

                    # Check for syntax errors in output
                    syntax_errors = ""
                    if "SyntaxError" in test_results["output"]:
                        syntax_match = re.search(
                            r"(SyntaxError:.*?)(?:\n\n|\Z)",
                            test_results["output"],
                            re.DOTALL,
                        )
                        if syntax_match:
                            syntax_errors = syntax_match.group(1)
                        else:
                            syntax_errors = "SyntaxError detected in test file"

                    # Generate additional tests with coverage and security feedback
                    current_test_code, current_test_file = (
                        self.generate_additional_tests(
                            codebase_path,
                            current_test_file,
                            current_coverage,
                            uncovered_areas,
                            syntax_errors=syntax_errors,
                            security_issues=security_issues
                            if has_severe_security
                            else None,
                        )
                    )

                    # Re-extract and install any new dependencies
                    new_deps = extract_dependencies(current_test_code)
                    if new_deps:
                        install_dependencies(new_deps, codebase_path)

                else:
                    # Reached max iterations without meeting targets
                    print(f"\n⚠️ Max iterations ({max_iterations}) reached")
                    print(f"   Final coverage: {current_coverage:.1f}%")
                    if has_severe_security:
                        print("   ⚠️  Unresolved severe security issues remain")
                    recommendations = evaluation.actionable_recommendations
                    if recommendations:
                        print("   Recommendations:")
                        for rec in recommendations[:5]:
                            print(f"   • {rec}")

                # Restore best test code if final iteration is worse
                if best_test_code and best_coverage > current_coverage:
                    print(
                        f"\n🔄 Restoring test code with best coverage: {best_coverage:.1f}%"
                    )
                    with open(current_test_file, "w", encoding="utf-8") as f:
                        f.write(best_test_code)
                    current_test_code = best_test_code

            results["status"] = "completed"

            # Save all prompts to JSON for later analysis
            import time as time_module

            run_id = str(int(time_module.time()))
            prompts_file = self.save_prompts(output_dir, run_id)
            results["prompts_file"] = str(prompts_file)
            results["total_prompts"] = len(self.prompt_history)

            # Print summary
            print("\n" + "=" * 60)
            print("✅ Pipeline Complete!")
            print("=" * 60)
            print(f"   Test file: {test_file}")
            print(f"   Scenarios: {len(approved_scenarios.test_scenarios)}")

            if "evaluation" in results:
                eval_data = results["evaluation"]
                summary = eval_data["execution_summary"]
                print(f"   Tests: {summary['passed']}/{summary['total_tests']} passed")
                print(f"   Coverage: {eval_data['code_coverage_percentage']:.1f}%")

            print(f"   Prompts used: {len(self.prompt_history)}")

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            print(f"\n❌ Pipeline failed: {e}")

            # Still save prompts even on failure
            try:
                import time as time_module

                run_id = str(int(time_module.time()))
                prompts_file = self.save_prompts(
                    output_dir or codebase_path / "tests", run_id
                )
                print(f"   Prompts saved to: {prompts_file}")
            except Exception as save_error:
                print(f"   Could not save prompts: {save_error}")

        return results


# ==================== Main Entry Point ====================


def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Python Automated Testing Pipeline")
    parser.add_argument("codebase_path", type=Path, help="Path to Python codebase")
    # The pipeline will run generated tests by default. Use --no-run-tests to disable.
    parser.add_argument(
        "--run-tests",
        dest="run_tests",
        action="store_true",
        help="Run generated tests (deprecated; tests run by default)",
    )
    parser.add_argument(
        "--no-run-tests",
        dest="no_run_tests",
        action="store_true",
        help="Do not run generated tests",
    )
    parser.add_argument("--coverage", action="store_true", help="Collect coverage")
    parser.add_argument(
        "--auto-approve", action="store_true", help="Auto-approve scenarios"
    )
    parser.add_argument("--output-dir", type=Path, help="Output directory for tests")
    parser.add_argument("--model", type=str, help="Model to use")
    args = parser.parse_args()

    if not args.codebase_path.exists():
        print(f"Error: Path does not exist: {args.codebase_path}")
        sys.exit(1)

    pipeline = PythonTestingPipeline(model=args.model)
    # Determine run_tests behavior with support for both flags
    if args.run_tests:
        run_tests_flag = True
    elif getattr(args, "no_run_tests", False):
        run_tests_flag = False
    else:
        # Default behavior: run tests unless explicitly disabled
        run_tests_flag = True

    results = pipeline.run_pipeline(
        codebase_path=args.codebase_path,
        output_dir=args.output_dir,
        should_run_tests=run_tests_flag,
        coverage=args.coverage,
        auto_approve=args.auto_approve,
    )
    sys.exit(0 if results["status"] == "completed" else 1)


if __name__ == "__main__":
    main()
