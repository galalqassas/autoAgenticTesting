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
import importlib.metadata
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

# Import LLM configuration and client
from llm_config import create_llm_client

# ==================== Type Definitions ====================


@dataclass
class TestScenario:
    """Represents a single test scenario."""

    scenario_description: str
    priority: str  # "High", "Medium", or "Low"


@dataclass
class TestScenariosOutput:
    """Output from the Test Case Identification Agent."""

    test_scenarios: list[TestScenario]


@dataclass
class ExecutionSummary:
    """Summary of test execution."""

    total_tests: int
    passed: int
    failed: int


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
    actionable_recommendations: list[str]
    security_issues: list[SecurityIssue] = None
    has_severe_security_issues: bool = False

    def __post_init__(self):
        if self.security_issues is None:
            self.security_issues = []


# ==================== System Prompts ====================

IDENTIFICATION_SYSTEM_PROMPT = """### ROLE
You are a Senior Software Quality Assurance Engineer specializing in Python.

### OBJECTIVE
Your primary goal is to analyze the given Python codebase and identify a comprehensive list of test scenarios, including critical edge cases, for human approval.

### RULES & CONSTRAINTS
- Focus exclusively on identifying test scenarios; do not generate test code.
- Prioritize critical paths, common use cases, and edge cases (e.g., invalid inputs, empty values, concurrency issues).
- If the code is unclear or incomplete, identify the ambiguity as a test scenario.

### OUTPUT FORMAT
- Provide the response as a single JSON object.
- The JSON object should contain one key, "test_scenarios", which holds a list of test case objects.
- Each test case object must include:
    - "scenario_description": A concise string explaining the test case.
    - "priority": A string with a value of "High", "Medium", or "Low".

### EXAMPLE
```json
{
  "test_scenarios": [
    {
      "scenario_description": "Test user login with valid credentials.",
      "priority": "High"
    },
    {
      "scenario_description": "Test user login with an invalid password.",
      "priority": "High"
    },
    {
      "scenario_description": "Test user login with an empty username field.",
      "priority": "Medium"
    }
  ]
}
```"""

IMPLEMENTATION_SYSTEM_PROMPT = """### ROLE
You are a Senior Software Development Engineer in Test (SDET) specializing in Python and the PyTest framework.

### OBJECTIVE
Your goal is to generate executable PyTest test scripts based on an approved JSON list of test scenarios.

### CRITICAL RULES
- Return ONLY raw Python code - NO markdown formatting, NO code fences (``` or ```python)
- The output must be valid Python that can be saved directly to a .py file
- Use the PyTest framework for all generated tests
- Write clean, readable, and maintainable code following PEP 8 standards
- Ensure each test function is self-contained and starts with 'test_'
- Include all necessary imports at the top of the file

### CRITICAL: CODE COVERAGE REQUIREMENTS
- For coverage to be measured, you MUST import and use the source code DIRECTLY in the test process
- DO NOT run source files as subprocesses for testing - pytest-cov cannot measure subprocess coverage
- IMPORT the source module and test its functions, classes, and behavior directly
- Use mocking to isolate side effects (e.g., network, file I/O)
- Example for testing a server module:
  ```python
  import sys
  from pathlib import Path

  # Add project root to path for imports
  PROJECT_ROOT = Path(__file__).parent.parent
  sys.path.insert(0, str(PROJECT_ROOT))

  # Now import the source module directly
  import server  # This will be measured by coverage

  def test_handler_class():
      # Test the Handler class directly
      assert hasattr(server, 'Handler')
      assert issubclass(server.Handler, http.server.SimpleHTTPRequestHandler)
  ```

### CRITICAL: TESTING `if __name__ == "__main__":` BLOCKS
- Code inside `if __name__ == "__main__":` is NOT executed when importing the module
- To test this code, use `exec()` or `runpy.run_path()` with mocks
- IMPORTANT: When using runpy.run_path() to test server code, you MUST mock:
  1. `socketserver.TCPServer` to prevent real server startup
  2. The serve_forever() method to avoid blocking
  3. Have the mock raise KeyboardInterrupt to simulate shutdown
- Example pattern:
  ```python
  from unittest.mock import patch, MagicMock
  import runpy

  def test_main_block_starts_server():
      # MUST mock TCPServer to prevent real server from starting!
      mock_httpd = MagicMock()
      mock_httpd.serve_forever.side_effect = KeyboardInterrupt()  # Simulate Ctrl+C

      mock_context = MagicMock()
      mock_context.__enter__.return_value = mock_httpd
      mock_context.__exit__.return_value = None

      with patch('socketserver.TCPServer', return_value=mock_context):
          with patch('os.path.exists', return_value=True):
              runpy.run_path(str(SERVER_SCRIPT), run_name="__main__")

  def test_main_block_with_missing_directory():
      with patch('os.path.exists', return_value=False):
          with patch('builtins.exit') as mock_exit:
              with patch('builtins.print'):
                  try:
                      runpy.run_path(str(SERVER_SCRIPT), run_name="__main__")
                  except SystemExit:
                      pass
              mock_exit.assert_called_once_with(1)
  ```

### CRITICAL: TESTING http.server.SimpleHTTPRequestHandler SUBCLASSES
- These handlers require real socket connections to initialize
- NEVER call Handler(None, None, None) - it will fail
- Use mocking or test the class attributes instead:
  ```python
  def test_handler_inheritance():
      assert issubclass(server.Handler, http.server.SimpleHTTPRequestHandler)

  def test_handler_init_sets_directory():
      # Check __init__ method signature or use runpy to run server
      import inspect
      sig = inspect.signature(server.Handler.__init__)
      # Verify it accepts the expected parameters
  ```

### IMPORTANT: FILE PATH HANDLING
- The test file will be saved in a `tests/` subdirectory of the project
- Add the project root to sys.path to enable imports: `sys.path.insert(0, str(PROJECT_ROOT))`
- Then import source modules directly: `import mymodule`
- For file path references, use: `Path(__file__).parent.parent / "filename.py"`

### IMPORTANT: WINDOWS COMPATIBILITY
- NEVER use `signal.SIGINT` to stop processes - it is NOT supported on Windows
- To stop a subprocess, use `proc.terminate()` or `proc.kill()` instead
- For tests that need to simulate keyboard interrupt, mock the behavior instead of sending signals

### OUTPUT FORMAT
- Return raw Python code only - no explanations, no markdown
- The code must be syntactically correct and ready for execution
- Function names should clearly reflect the scenario (e.g., `test_login_with_invalid_password`)

### EXAMPLE OUTPUT (note: no code fences, just raw Python):
import pytest
import sys
import runpy
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
SERVER_SCRIPT = PROJECT_ROOT / "server.py"

# Import source module directly (for coverage measurement)
import server

def test_handler_class_exists():
    assert hasattr(server, 'Handler')

def test_port_constant():
    assert server.PORT == 8000

def test_directory_constant():
    assert server.DIRECTORY == 'dist'

def test_handler_inheritance():
    import http.server
    assert issubclass(server.Handler, http.server.SimpleHTTPRequestHandler)

def test_main_exits_when_directory_missing():
    with patch('os.path.exists', return_value=False):
        with patch('builtins.exit') as mock_exit:
            with patch('builtins.print'):
                try:
                    runpy.run_path(str(SERVER_SCRIPT), run_name="__main__")
                except SystemExit:
                    pass
            mock_exit.assert_called_once_with(1)"""

EVALUATION_SYSTEM_PROMPT = """### ROLE
You are a Principal Software Development Engineer in Test (SDET) with expertise in test automation analysis, code quality metrics, and security testing.

### OBJECTIVE
Your primary goal is to:
1. Evaluate the results of a PyTest test suite execution
2. Analyze test outcomes and measure code coverage
3. Perform security analysis on the source code and test code
4. Provide actionable recommendations to enhance testing quality and security

### RULES & CONSTRAINTS
- You will receive the PyTest execution report (pass/fail status), code coverage report, and source code.
- Your analysis must identify security vulnerabilities in the code.
- Recommendations must be specific, actionable, and aimed at improving test coverage, robustness, AND security.
- Security issues should be classified by severity: "critical", "high", "medium", "low".
- Critical/High severity issues MUST be addressed before the pipeline can complete.

### SECURITY ANALYSIS FOCUS AREAS
- SQL Injection vulnerabilities
- Cross-Site Scripting (XSS)
- Command Injection
- Path Traversal attacks
- Insecure deserialization
- Hardcoded secrets/credentials
- Insecure cryptographic practices
- Missing input validation
- Improper error handling that leaks sensitive info
- Insecure dependencies

### OUTPUT FORMAT
- Provide the response as a single JSON object.
- The JSON object must contain these keys:
    - "execution_summary": An object containing integer values for "total_tests", "passed", and "failed".
    - "code_coverage_percentage": A float value representing the total coverage (e.g., 92.5).
    - "security_issues": A list of objects with "severity" (critical/high/medium/low), "issue", "location", and "recommendation".
    - "has_severe_security_issues": Boolean - true if any critical or high severity issues exist.
    - "actionable_recommendations": A list of concise strings for improving coverage and fixing issues.

### EXAMPLE
```json
{
  "execution_summary": {
    "total_tests": 50,
    "passed": 48,
    "failed": 2
  },
  "code_coverage_percentage": 85.0,
  "security_issues": [
    {
      "severity": "high",
      "issue": "SQL Injection vulnerability",
      "location": "database.py:45 - execute_query()",
      "recommendation": "Use parameterized queries instead of string concatenation"
    },
    {
      "severity": "medium",
      "issue": "Missing input validation",
      "location": "api.py:23 - get_user()",
      "recommendation": "Validate and sanitize user_id parameter before use"
    }
  ],
  "has_severe_security_issues": true,
  "actionable_recommendations": [
    "Fix the SQL injection vulnerability in database.py before deployment.",
    "Add input validation tests for all API endpoints.",
    "Increase test coverage for the 'user_profile_utils.py' module."
  ]
}
```"""


# ==================== Pipeline Implementation ====================


class PythonTestingPipeline:
    """Orchestrates the three-agent testing pipeline."""

    def __init__(self, model: Optional[str] = None):
        # Use the LLM client from llm_config for automatic API key rotation and model fallback
        self.llm_client = create_llm_client(use_mock_on_failure=True)
        self.prompt_history = []  # Track all prompts for later analysis

        # Print current configuration
        if self.llm_client.current_api_key:
            print(f"Using model: {self.llm_client.current_model}")

    @property
    def model(self) -> str:
        """Get current model from LLM client."""
        return self.llm_client.current_model

    def _call_llm(
        self, system_prompt: str, user_prompt: str, agent_name: str = "unknown"
    ) -> str:
        """Calls the LLM with the given prompts and records them."""
        import time as time_module

        timestamp = time_module.strftime("%Y-%m-%d %H:%M:%S")

        # Make the LLM call with automatic fallback
        response, is_mock = self.llm_client.call(system_prompt, user_prompt)

        # Record the prompt after the call
        prompt_record = {
            "timestamp": timestamp,
            "agent": agent_name,
            "model": self.llm_client.current_model,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "response": response,
            "is_mock": is_mock,
        }
        self.prompt_history.append(prompt_record)

        return response

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

    def _sanitize_code(self, code: str) -> str:
        """Removes markdown formatting and ensures valid Python code."""
        # Remove markdown code fences
        code = code.strip()

        # Handle ```python ... ``` blocks
        if code.startswith("```"):
            # Find the end of the first line (language specifier)
            first_newline = code.find("\n")
            if first_newline != -1:
                code = code[first_newline + 1 :]

        # Remove trailing ``` if present
        if code.endswith("```"):
            code = code[:-3].rstrip()

        # Also try regex extraction as fallback
        if "```" in code:
            match = re.search(r"```(?:python)?\s*([\s\S]*?)```", code)
            if match:
                code = match.group(1).strip()

        # Remove any remaining backticks at start/end
        code = code.strip("`").strip()

        return code

    def _validate_syntax(self, code: str) -> tuple[bool, str]:
        """Validates Python syntax. Returns (is_valid, error_message)."""
        try:
            import ast

            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"

    def _fix_syntax_errors(self, code: str, error_msg: str, codebase_path: Path) -> str:
        """Asks LLM to fix syntax errors in generated code."""
        print(f"   ⚠️ Syntax error detected: {error_msg}")
        print("   🔧 Attempting to fix...")

        python_files = self.gather_python_files(codebase_path)
        source_context = self.read_file_contents(python_files[:5])

        fix_prompt = f"""The following Python test code has a syntax error:

Error: {error_msg}

Problematic code:
{code[:2000]}...

Source code being tested:
{source_context[:2000]}

Fix the syntax error and return ONLY valid Python code. Do NOT include markdown code fences (``` or ```python). Return raw Python code only."""

        response = self._call_llm(
            IMPLEMENTATION_SYSTEM_PROMPT, fix_prompt, agent_name="syntax_fixer"
        )
        return self._sanitize_code(response)

    def gather_python_files(self, codebase_path: Path) -> list[Path]:
        """Gathers all Python files from the codebase."""
        python_files = []
        excluded_dirs = {
            ".git",
            "__pycache__",
            "venv",
            ".venv",
            "node_modules",
            ".pytest_cache",
            "tests",
            "test",
            "__tests__",
        }

        for root, dirs, files in os.walk(codebase_path):
            # Filter out excluded directories (test directories, hidden dirs, etc.)
            dirs[:] = [
                d for d in dirs if d not in excluded_dirs and not d.startswith(".")
            ]

            for file in files:
                # Exclude test files: test_*.py, *_test.py, conftest.py
                if file.endswith(".py"):
                    is_test_file = (
                        file.startswith("test_")
                        or file.endswith("_test.py")
                        or file == "conftest.py"
                    )
                    if not is_test_file:
                        python_files.append(Path(root) / file)

        return python_files

    def read_file_contents(self, files: list[Path]) -> str:
        """Reads and combines content from multiple files."""
        contents = []
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    contents.append(f"# File: {file_path}\n{f.read()}")
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")
        return "\n\n".join(contents)

    def identify_test_scenarios(self, codebase_path: Path) -> TestScenariosOutput:
        """Agent 1: Identifies test scenarios from the codebase."""
        print("\n🔍 Agent 1: Identifying test scenarios...")

        python_files = self.gather_python_files(codebase_path)
        if not python_files:
            raise ValueError(f"No Python files found in {codebase_path}")

        print(f"   Found {len(python_files)} Python files to analyze")

        code_content = self.read_file_contents(python_files)
        file_list = "\n".join(str(f) for f in python_files)

        user_prompt = f"""Analyze this Python codebase and identify test scenarios.

Files: {file_list}

Code:
{code_content}

Respond with JSON containing test_scenarios."""

        response = self._call_llm(
            IDENTIFICATION_SYSTEM_PROMPT, user_prompt, agent_name="identification_agent"
        )

        try:
            if "```" in response:
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
                if json_match:
                    response = json_match.group(1).strip()

            data = json.loads(response)
            scenarios = [TestScenario(**s) for s in data["test_scenarios"]]
            return TestScenariosOutput(test_scenarios=scenarios)
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse response: {e}")

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
        print("\n🔧 Agent 2: Generating PyTest test code...")

        python_files = self.gather_python_files(codebase_path)
        code_context = self.read_file_contents(python_files[:10])
        scenarios_json = json.dumps(asdict(scenarios), indent=2)

        # Build file list for the AI to understand the project structure
        file_list = "\n".join(f"  - {f.name}" for f in python_files)

        user_prompt = f"""Generate PyTest tests for these scenarios:

{scenarios_json}

PROJECT STRUCTURE:
- Tests will be saved to: tests/test_generated_*.py
- Source files are in the project root:
{file_list}

CRITICAL: CODE COVERAGE - IMPORT SOURCE FILES DIRECTLY:
- Add project root to sys.path: `sys.path.insert(0, str(PROJECT_ROOT))`
- Import source modules directly: `import server` (NOT as subprocess)
- Test functions, classes, and constants directly to measure coverage
- DO NOT run source files as subprocesses - coverage won't be measured!

WINDOWS COMPATIBILITY:
- NEVER use `signal.SIGINT` to stop processes (not supported on Windows)
- Use `proc.terminate()` or `proc.kill()` to stop subprocesses
- For keyboard interrupt tests, mock the behavior instead of sending real signals

Source code:
{code_context}

IMPORTANT RULES:
1. Return ONLY valid Python code - no markdown, no code fences
2. Include all necessary imports at the top
3. Each test function must start with 'test_'
4. IMPORT source modules directly for coverage (add project root to sys.path first)
5. Use mocking for side effects (network, file I/O)
6. Use proc.terminate() instead of signal.SIGINT for stopping processes

Generate a complete, executable PyTest file."""

        response = self._call_llm(
            IMPLEMENTATION_SYSTEM_PROMPT, user_prompt, agent_name="implementation_agent"
        )
        test_code = self._sanitize_code(response)

        # Validate syntax and fix if needed (up to 3 attempts)
        for attempt in range(3):
            is_valid, error_msg = self._validate_syntax(test_code)
            if is_valid:
                break
            test_code = self._fix_syntax_errors(test_code, error_msg, codebase_path)

        # Final validation
        is_valid, error_msg = self._validate_syntax(test_code)
        if not is_valid:
            print(f"   ⚠️ Warning: Generated code may have syntax errors: {error_msg}")

        output_dir.mkdir(parents=True, exist_ok=True)
        test_file = output_dir / f"test_generated_{int(__import__('time').time())}.py"

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)

        print(f"   Generated: {test_file}")
        return test_code, test_file

    def extract_dependencies(self, test_code: str) -> list[str]:
        """Extracts required packages from generated test code imports."""
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

    def install_dependencies(self, packages: list[str], cwd: Path) -> tuple[str, int]:
        """Installs required packages using pip, skipping those already installed."""
        if not packages:
            return "No packages to install", 0

        # Check which packages are already installed
        missing_packages = []
        # Get all installed packages, normalized to lowercase and hyphens
        installed_dists = set()
        for d in importlib.metadata.distributions():
            name = d.metadata.get("Name")
            if name:
                installed_dists.add(name.lower().replace("_", "-"))

        for package in packages:
            # Extract package name from version specifiers (e.g., "pytest>=7.0" -> "pytest")
            # Simple normalization for comparison
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
            print(f"\n✅ All dependencies already installed: {', '.join(packages)}")
            return "All dependencies already installed", 0

        print(f"\n📦 Installing dependencies: {', '.join(missing_packages)}")

        cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + missing_packages

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120, cwd=cwd
            )
            output = result.stdout + "\n" + result.stderr
            if result.returncode == 0:
                print("   ✅ Dependencies installed successfully")
            else:
                print(f"   ⚠️ Some packages may have failed: {result.stderr}")
            return output, result.returncode
        except subprocess.TimeoutExpired:
            return "Dependency installation timed out", 1
        except Exception as e:
            return f"Error installing dependencies: {e}", 1

    def run_tests(self, test_file: Path, codebase_path: Path) -> dict:
        """Runs the generated PyTest suite with coverage measurement."""
        print("\n🧪 Running tests with coverage...")

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
            print(output)

            # Parse test results from output
            test_results = self._parse_pytest_output(output)

            # Parse coverage from JSON report
            coverage_json_path = test_file.parent.parent / "coverage.json"
            coverage_pct = self._parse_coverage_json(coverage_json_path)

            return {
                "output": output,
                "exit_code": result.returncode,
                "total_tests": test_results["total"],
                "passed": test_results["passed"],
                "failed": test_results["failed"],
                "coverage_percentage": coverage_pct,
            }
        except subprocess.TimeoutExpired:
            return {
                "output": "Test execution timed out",
                "exit_code": 1,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "coverage_percentage": 0.0,
            }
        except Exception as e:
            return {
                "output": f"Error running tests: {e}",
                "exit_code": 1,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "coverage_percentage": 0.0,
            }

    def _parse_pytest_output(self, output: str) -> dict:
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

    def _parse_coverage_json(self, coverage_json_path: Path) -> float:
        """Parses coverage.json to extract total coverage percentage."""
        try:
            if coverage_json_path.exists():
                with open(coverage_json_path, "r") as f:
                    data = json.load(f)
                    return data.get("totals", {}).get("percent_covered", 0.0)
        except Exception as e:
            print(f"   ⚠️ Could not parse coverage.json: {e}")
        return 0.0

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
        print("\n📊 Agent 3: Evaluating test results and security...")

        # Use actual measured values
        actual_coverage = test_results.get("coverage_percentage", 0.0)
        total_tests = test_results.get("total_tests", 0)
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)

        print(f"   Actual coverage measured: {actual_coverage:.1f}%")

        # Gather source code for security analysis
        python_files = self.gather_python_files(codebase_path)
        source_code = self.read_file_contents(python_files[:10])

        scenarios_json = json.dumps(asdict(scenarios), indent=2)
        user_prompt = f"""Evaluate these PyTest results AND perform security analysis:

Scenarios: {scenarios_json}

Test Results:
- Total tests: {total_tests}
- Passed: {passed}
- Failed: {failed}
- Code Coverage: {actual_coverage:.1f}%

PyTest Output:
{test_results.get("output", "")[:3000]}

Source Code (analyze for security issues):
{source_code[:5000]}

Provide:
1. Actionable recommendations to improve test coverage and fix failures
2. Security analysis identifying vulnerabilities (SQL injection, XSS, command injection, path traversal, hardcoded secrets, etc.)
3. Mark has_severe_security_issues as true if any critical or high severity issues exist

Respond with JSON containing execution_summary, code_coverage_percentage, security_issues, has_severe_security_issues, and actionable_recommendations."""

        response = self._call_llm(
            EVALUATION_SYSTEM_PROMPT, user_prompt, agent_name="evaluation_agent"
        )

        try:
            if "```" in response:
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
                if json_match:
                    response = json_match.group(1).strip()

            data = json.loads(response)

            # Parse security issues
            security_issues = []
            for issue_data in data.get("security_issues", []):
                security_issues.append(
                    SecurityIssue(
                        severity=issue_data.get("severity", "low"),
                        issue=issue_data.get("issue", ""),
                        location=issue_data.get("location", ""),
                        recommendation=issue_data.get("recommendation", ""),
                    )
                )

            has_severe = data.get("has_severe_security_issues", False)
            # Also check if any security issues are critical/high
            if not has_severe and security_issues:
                has_severe = any(
                    si.severity in ("critical", "high") for si in security_issues
                )

            if security_issues:
                print(f"   🔒 Security issues found: {len(security_issues)}")
                severe_count = sum(
                    1 for si in security_issues if si.severity in ("critical", "high")
                )
                if severe_count > 0:
                    print(f"   ⚠️  Severe issues (critical/high): {severe_count}")

            # Override with actual measured values
            return TestEvaluationOutput(
                execution_summary=ExecutionSummary(
                    total_tests=total_tests, passed=passed, failed=failed
                ),
                code_coverage_percentage=actual_coverage,
                actionable_recommendations=data.get("actionable_recommendations", []),
                security_issues=security_issues,
                has_severe_security_issues=has_severe,
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Return actual values even if LLM parsing fails
            return TestEvaluationOutput(
                execution_summary=ExecutionSummary(
                    total_tests=total_tests, passed=passed, failed=failed
                ),
                code_coverage_percentage=actual_coverage,
                actionable_recommendations=[f"Evaluation parsing failed: {e}"],
                security_issues=[],
                has_severe_security_issues=False,
            )

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
        reasons = []
        if coverage_percentage < 90.0:
            reasons.append(f"coverage ({coverage_percentage:.1f}%) below 90%")
        if security_issues:
            severe = [
                si for si in security_issues if si.severity in ("critical", "high")
            ]
            if severe:
                reasons.append(f"{len(severe)} severe security issue(s)")

        print(f"\n🔄 Generating additional tests: {', '.join(reasons)}...")

        python_files = self.gather_python_files(codebase_path)
        code_context = self.read_file_contents(python_files[:10])

        # Build file list for the AI to understand the project structure
        file_list = "\n".join(f"  - {f.name}" for f in python_files)

        # Read existing tests
        existing_tests = ""
        try:
            with open(existing_test_file, "r", encoding="utf-8") as f:
                existing_tests = f.read()
        except Exception:
            pass

        # Build error context if there were syntax errors
        error_context = ""
        if syntax_errors:
            error_context = f"""\n\nCRITICAL: The previous test file had syntax errors that must be fixed:
{syntax_errors}

Common issues to avoid:
- Do NOT include markdown code fences (``` or ```python)
- Ensure all strings are properly closed
- Ensure all parentheses, brackets, and braces are balanced
- Make sure indentation is consistent (use 4 spaces)
"""

        # Build security context if there are security issues
        security_context = ""
        if security_issues:
            security_feedback = []
            for si in security_issues:
                security_feedback.append(
                    f"- [{si.severity.upper()}] {si.issue} at {si.location}\n"
                    f"  Recommendation: {si.recommendation}"
                )
            security_context = f"""\n\nSECURITY ISSUES TO ADDRESS:
The following security vulnerabilities were identified. Add tests that:
1. Verify these vulnerabilities are handled properly
2. Test boundary conditions and malicious inputs
3. Ensure proper input validation and sanitization

{chr(10).join(security_feedback)}

For each security issue, add at least one test that:
- Tests the vulnerable code path with malicious input
- Verifies proper error handling or input rejection
- Checks that sensitive data is not exposed in errors
"""

        user_prompt = f"""The current test suite needs improvements:
- Code coverage: {coverage_percentage:.1f}% (target: 90%+)
- Security issues: {len(security_issues) if security_issues else 0} found

PROJECT STRUCTURE:
- Tests are saved in: tests/test_generated_*.py
- Source files are in the project root:
{file_list}

CRITICAL: CODE COVERAGE - IMPORT SOURCE FILES DIRECTLY:
- Add project root to sys.path: `sys.path.insert(0, str(PROJECT_ROOT))`
- Import source modules directly: `import server` (NOT as subprocess)
- Test functions, classes, and constants directly to measure coverage
- DO NOT run source files as subprocesses - coverage won't be measured!

WINDOWS COMPATIBILITY:
- NEVER use `signal.SIGINT` to stop processes (not supported on Windows)
- Use `proc.terminate()` or `proc.kill()` to stop subprocesses
- For keyboard interrupt tests, mock the behavior instead of sending real signals
{error_context}{security_context}
Existing tests (may have errors - fix them):
{existing_tests[:3000]}

Uncovered code areas from coverage report:
{uncovered_areas}

Source code to test:
{code_context}

IMPORTANT RULES:
1. Return ONLY valid Python code - NO markdown code fences (``` or ```python)
2. Fix any syntax errors from the existing tests
3. IMPORT source modules directly for coverage (add project root to sys.path first)
4. Each test function must start with 'test_'
5. Use mocking for side effects (network, file I/O)
6. Use proc.terminate() instead of signal.SIGINT for stopping processes

Generate a complete, executable PyTest file that:
1. Fixes any existing syntax errors
2. IMPORTS source modules directly (not subprocess) for coverage
3. Tests uncovered lines by calling functions/classes directly
4. Aims for 90%+ code coverage"""

        response = self._call_llm(
            IMPLEMENTATION_SYSTEM_PROMPT,
            user_prompt,
            agent_name="implementation_agent_improvement",
        )
        test_code = self._sanitize_code(response)

        # Validate syntax and fix if needed
        for attempt in range(3):
            is_valid, error_msg = self._validate_syntax(test_code)
            if is_valid:
                break
            test_code = self._fix_syntax_errors(test_code, error_msg, codebase_path)

        # Final validation
        is_valid, error_msg = self._validate_syntax(test_code)
        if not is_valid:
            print(f"   ⚠️ Warning: Code may still have syntax errors: {error_msg}")

        # Overwrite existing test file with improved version
        with open(existing_test_file, "w", encoding="utf-8") as f:
            f.write(test_code)

        print(f"   Updated: {existing_test_file}")
        return test_code, existing_test_file

    def run_pipeline(
        self,
        codebase_path: Path,
        output_dir: Optional[Path] = None,
        run_tests: bool = True,
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
            if run_tests:
                deps = self.extract_dependencies(test_code)
                if deps:
                    dep_output, dep_exit = self.install_dependencies(
                        deps, codebase_path
                    )
                    results["dependencies_installed"] = deps
                    results["dependency_output"] = dep_output

            # Step 5: Run tests with coverage and improvement loop
            if run_tests:
                target_coverage = 90.0
                max_iterations = 15  # Safety limit to prevent infinite loops
                current_test_file = test_file
                current_test_code = test_code
                iteration = 0

                # Track progress to prevent getting stuck
                best_coverage = 0.0
                best_severe_count = float("inf")
                consecutive_no_progress = 0

                while iteration < max_iterations:
                    iteration += 1
                    print(f"\n--- Iteration {iteration} ---")

                    # Run tests with coverage
                    test_results = self.run_tests(current_test_file, codebase_path)
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
                    new_deps = self.extract_dependencies(current_test_code)
                    if new_deps:
                        self.install_dependencies(new_deps, codebase_path)

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
                results["prompts_file"] = str(prompts_file)
            except Exception:
                pass

        return results


# ==================== CLI Entry Point ====================


def main():
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
        run_tests=run_tests_flag,
        coverage=args.coverage,
        auto_approve=args.auto_approve,
    )
    sys.exit(0 if results["status"] == "completed" else 1)


if __name__ == "__main__":
    main()
