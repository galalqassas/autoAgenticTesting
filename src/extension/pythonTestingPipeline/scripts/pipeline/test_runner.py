"""Test execution and dependency management for the Python Testing Pipeline."""

import importlib.metadata
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from llm_config import create_llm_client
from pipeline.prompts import (
    DEPENDENCY_ANALYSIS_SYSTEM_PROMPT,
    DEPENDENCY_FIX_SYSTEM_PROMPT,
)

__all__ = [
    "extract_dependencies",
    "install_dependencies",
    "run_tests",
    "parse_pytest_output",
    "parse_coverage_json",
]


def analyze_dependencies_with_llm(test_code: str) -> Optional[List[str]]:
    """
    Uses LLM to analyze test code and determine exact PyPI packages.
    Returns None if analysis fails, triggering fallback to regex.
    """
    print("   🤖 Asking LLM to identify dependencies...")
    try:
        llm_client = create_llm_client(use_mock_on_failure=True)

        # Truncate test code if it's too long to avoid token limits
        # 10k chars is usually enough to see imports and usage
        code_sample = test_code[:10000]
        if len(test_code) > 10000:
            code_sample += "\n... (truncated)"

        response, _ = llm_client.call(
            DEPENDENCY_ANALYSIS_SYSTEM_PROMPT,
            f"Identify PyPI packages for this code:\n\n{code_sample}",
        )

        # Parse JSON response
        if "```" in response:
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
            if json_match:
                response = json_match.group(1).strip()

        data = json.loads(response)
        packages = data.get("packages", [])

        # Basic validation
        if isinstance(packages, list) and all(isinstance(p, str) for p in packages):
            return packages

    except Exception as e:
        print(f"   ⚠️  LLM dependency analysis failed: {e}")

    return None


def extract_dependencies(test_code: str) -> List[str]:
    """Extracts required packages using LLM with regex fallback."""

    # 1. Try LLM first
    llm_packages = analyze_dependencies_with_llm(test_code)
    if llm_packages is not None:
        print(f"   ✨ LLM identified packages: {', '.join(llm_packages)}")
        return llm_packages

    # 2. Fallback to regex if LLM fails
    print("   ⚠️  Falling back to regex dependency extraction...")

    # Common import to package name mappings
    import_to_package = {
        "fastapi": "fastapi",
        "starlette": "starlette",
        "httpx": "httpx",
        "pytest": "pytest",
        "pytest_asyncio": "pytest-asyncio",
        "jinja2": "jinja2",
        "pydantic": "pydantic",
        "sqlalchemy": "sqlalchemy",
        "flask": "flask",
        "django": "django",
        "requests": "requests",
        "aiohttp": "aiohttp",
        "numpy": "numpy",
        "pandas": "pandas",
        "cv2": "opencv-python",
        "bs4": "beautifulsoup4",
        "yaml": "PyYAML",
        "PIL": "Pillow",
        "sklearn": "scikit-learn",
    }

    # Find all imports
    import_pattern = r"^(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
    imports = set()
    for line in test_code.split("\n"):
        match = re.match(import_pattern, line.strip())
        if match:
            module = match.group(1)
            if module in import_to_package:
                imports.add(import_to_package[module])

    # Always include pytest essentials
    imports.add("pytest")
    imports.add("pytest-cov")
    imports.add("pytest-timeout")

    return list(imports)


def install_dependencies_with_retry(packages: List[str], cwd: Path) -> Tuple[str, int]:
    """Installs packages with LLM-guided retry logic on failure."""

    attempt = 0
    max_retries = 3
    current_packages = packages.copy()
    last_output = ""
    last_return_code = 0

    while attempt <= max_retries:
        if not current_packages:
            return "No packages to install", 0

        # Check what's missing
        missing_packages = []
        installed_dists = set()
        for d in importlib.metadata.distributions():
            name = d.metadata.get("Name")
            if name:
                installed_dists.add(name.lower().replace("_", "-"))

        for package in current_packages:
            # Normalize package name
            pkg_name = (
                package.split("==")[0]
                .split(">=")[0]
                .split("<=")[0]
                .split(">")[0]
                .split("<")[0]
                .strip()
                .lower()
                .replace("_", "-")
            )

            if pkg_name not in installed_dists:
                missing_packages.append(package)

        if not missing_packages:
            print(
                f"\n✅ All dependencies already installed: {', '.join(current_packages)}"
            )
            return "All dependencies already installed", 0

        print(
            f"\n📦 Installing dependencies (Attempt {attempt + 1}/{max_retries + 1}): {', '.join(missing_packages)}"
        )

        cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + missing_packages

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120, cwd=cwd
            )
            last_output = result.stdout + "\n" + result.stderr
            last_return_code = result.returncode

            if result.returncode == 0:
                print("   ✅ Dependencies installed successfully")
                return last_output, 0

            # Installation failed
            print(f"   ❌ Installation failed: {result.stderr.strip()}")

            if attempt < max_retries:
                print("   🤔 Asking LLM for a fix...")
                llm_client = create_llm_client(use_mock_on_failure=True)

                user_prompt = f"""Dependency installation failed.

                Packages attempted: {missing_packages}

                Error message:
                {result.stderr}

                Suggest a fix."""

                response, _ = llm_client.call(DEPENDENCY_FIX_SYSTEM_PROMPT, user_prompt)

                # Parse fix
                if "```" in response:
                    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
                    if json_match:
                        response = json_match.group(1).strip()

                try:
                    data = json.loads(response)
                    new_packages = data.get("packages", [])
                    reason = data.get("reason", "No reason provided")

                    if new_packages:
                        print(f"   💡 LLM Suggestion: {reason}")
                        print(f"   🔄 Retrying with: {', '.join(new_packages)}")
                        # Replace failed packages with suggested ones in our list
                        # For simplicity, we just use the new list for the next attempt
                        current_packages = new_packages
                    else:
                        print("   ⚠️  LLM could not suggest a fix.")
                        break
                except json.JSONDecodeError:
                    print("   ⚠️  Failed to parse LLM suggestion.")
                    break

            attempt += 1

        except subprocess.TimeoutExpired:
            return "Dependency installation timed out", 1
        except Exception as e:
            return f"Error installing dependencies: {e}", 1

    return last_output, last_return_code


def install_dependencies(packages: List[str], cwd: Path) -> Tuple[str, int]:
    """Wrapper for install_dependencies_with_retry."""
    return install_dependencies_with_retry(packages, cwd)


def parse_pytest_output(output: str) -> Dict[str, int]:
    """Parses pytest output to extract test counts."""
    total = passed = failed = 0

    # Match patterns like "5 passed", "3 failed", "10 passed, 2 failed"
    passed_match = re.search(r"(\d+) passed", output)
    failed_match = re.search(r"(\d+) failed", output)
    error_match = re.search(r"(\d+) error", output)

    if passed_match:
        passed = int(passed_match.group(1))
    if failed_match:
        failed = int(failed_match.group(1))
    if error_match:
        failed += int(error_match.group(1))

    total = passed + failed
    return {"total": total, "passed": passed, "failed": failed}


def parse_coverage_json(coverage_json_path: Path, source_root: Path) -> dict:
    """
    Parses coverage.json to extract detailed coverage information.

    Returns a dict with:
      - percentage: overall coverage percentage
      - uncovered_areas_text: formatted string for LLM
      - detailed_reports: dict of FileCoverageReport (as dicts)
    """
    try:
        from dataclasses import asdict

        from pipeline.coverage import (
            analyze_coverage,
            format_uncovered_areas,
            get_overall_percentage,
        )

        if coverage_json_path.exists():
            reports = analyze_coverage(coverage_json_path, source_root)
            return {
                "percentage": get_overall_percentage(reports),
                "uncovered_areas_text": format_uncovered_areas(reports),
                "detailed_reports": {
                    fp: asdict(r) for fp, r in reports.items()
                },
            }
    except Exception as e:
        print(f"   ⚠️ Could not parse coverage.json: {e}")
    return {"percentage": 0.0, "uncovered_areas_text": "", "detailed_reports": {}}


def run_tests(
    test_file: Path,
    codebase_path: Path,
    run_mutation_tests: bool = False,
) -> dict:
    """Runs the generated PyTest suite with coverage measurement.

    Args:
        test_file: Path to the pytest test file.
        codebase_path: Root path of the source code being tested.
        run_mutation_tests: If True, run mutation testing after the
            pytest suite completes.

    Returns:
        Dict containing test results, coverage data, and optionally
        mutation testing results.
    """
    print("\nRunning tests with coverage...")

    # Get source directory to measure coverage
    source_dir = str(codebase_path)

    # Create a .coveragerc file to exclude test files from coverage measurement.
    # This prevents the AI from trying to generate tests for test files.
    coveragerc_path = codebase_path / ".coveragerc"
    coveragerc_content = """[run]
omit =
    */tests/*
    */test/*
    **/test_*.py
    **/*_test.py
    **/conftest.py

[report]
omit =
    */tests/*
    */test/*
    **/test_*.py
    **/*_test.py
    **/conftest.py
"""
    try:
        with open(coveragerc_path, "w", encoding="utf-8") as f:
            f.write(coveragerc_content)
    except Exception as e:
        print(f"   ⚠️ Could not create .coveragerc: {e}")

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        "-v",
        "--tb=short",
        "--timeout=30",  # Per-test timeout of 30 seconds
        f"--cov={source_dir}",
        "--cov-branch",
        "--cov-report=term-missing",
        "--cov-report=json",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2-minute overall timeout
            cwd=test_file.parent.parent,
        )
        output = result.stdout + "\n" + result.stderr

        # Parse test results from output
        test_results = parse_pytest_output(output)

        # Parse coverage from JSON report
        coverage_json_path = test_file.parent.parent / "coverage.json"
        coverage_data = parse_coverage_json(coverage_json_path, codebase_path)

        # Run mutation testing if enabled
        mutation_score = 0.0
        mutation_report = None
        mutation_feedback = ""

        if run_mutation_tests:
            try:
                from pipeline.mutation_testing import (
                    format_mutation_feedback,
                    run_mutation_testing,
                )

                mutation_report = run_mutation_testing(
                    codebase_path=codebase_path,
                    test_file=test_file,
                    min_file_coverage=95.0,
                    timeout=600,
                )
                mutation_score = mutation_report.mutation_score
                mutation_feedback = format_mutation_feedback(mutation_report)
            except Exception as exc:
                print(f"   Mutation testing failed: {exc}")

        return {
            "output": output,
            "exit_code": result.returncode,
            "total_tests": test_results["total"],
            "passed": test_results["passed"],
            "failed": test_results["failed"],
            "coverage_percentage": coverage_data["percentage"],
            "uncovered_areas_text": coverage_data["uncovered_areas_text"],
            "coverage_details": coverage_data["detailed_reports"],
            "mutation_score": mutation_score,
            "mutation_report": mutation_report,
            "mutation_feedback": mutation_feedback,
        }
    except subprocess.TimeoutExpired:
        return {
            "output": "Test execution timed out",
            "exit_code": 1,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "coverage_percentage": 0.0,
            "uncovered_areas_text": "",
            "coverage_details": {},
            "mutation_score": 0.0,
            "mutation_report": None,
            "mutation_feedback": "",
        }
    except Exception as e:
        return {
            "output": f"Error running tests: {e}",
            "exit_code": 1,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "coverage_percentage": 0.0,
            "uncovered_areas_text": "",
            "coverage_details": {},
            "mutation_score": 0.0,
            "mutation_report": None,
            "mutation_feedback": "",
        }
