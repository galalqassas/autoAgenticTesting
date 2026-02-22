"""Agent classes for the Python Testing Pipeline."""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import List, Tuple

from llm_config import create_llm_client
from pipeline.code_utils import detect_hallucinations, sanitize_code, validate_syntax
from pipeline.file_utils import (
    gather_python_files,
    read_file_contents_chunked,
    truncate_at_boundary,
)
from pipeline.governance import FailureReason, governance_log
from pipeline.models import (
    ExecutionSummary,
    SecurityIssue,
    TestEvaluationOutput,
    TestScenario,
    TestScenariosOutput,
)
from pipeline.prompts import (
    EVALUATION_SYSTEM_PROMPT,
    HALLUCINATION_FIX_PROMPT,
    IDENTIFICATION_SYSTEM_PROMPT,
    IMPLEMENTATION_SYSTEM_PROMPT,
)


class BaseAgent:
    def __init__(self, llm_client=None, prompt_history: List[dict] = None):
        self.llm_client = llm_client or create_llm_client(use_mock_on_failure=False)
        self.prompt_history = prompt_history if prompt_history is not None else []

    def call_llm(
        self, system_prompt: str, user_prompt: str, agent_name: str = "unknown"
    ) -> str:
        """Calls the LLM with the given prompts and records them."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Make the LLM call with automatic fallback
        response, is_mock = self.llm_client.call(system_prompt, user_prompt)

        # Governance: Log decision with transparency and explainability
        governance_log.log_decision(
            agent=agent_name,
            action="llm_call",
            rationale=f"Processing {agent_name} request via LLM",
            confidence=0.85 if not is_mock else 0.0,
            inputs_used={
                "system_prompt_len": len(system_prompt),
                "user_prompt_len": len(user_prompt),
                "model": self.llm_client.current_model,
            },
            risk_level="medium" if not is_mock else "low",
        )

        prompt_record = {
            "timestamp": timestamp,
            "agent": agent_name,
            "model": getattr(self.llm_client, "last_used_model", None) or self.llm_client.current_model,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "response": response,
            "is_mock": is_mock,
        }
        self.prompt_history.append(prompt_record)

        return response


class IdentificationAgent(BaseAgent):
    def run(self, codebase_path: Path) -> TestScenariosOutput:
        """Identifies test scenarios from the codebase using parallel processing."""
        print("\n🔍 Agent 1: Identifying test scenarios...")

        python_files = gather_python_files(codebase_path)
        if not python_files:
            raise ValueError(f"No Python files found in {codebase_path}")

        print(f"   Found {len(python_files)} Python files to analyze")

        # Use chunked reading
        code_chunks = read_file_contents_chunked(python_files)
        print(f"   Split into {len(code_chunks)} logical chunks")

        file_list = "\n".join(str(f) for f in python_files)
        all_scenarios = []

        # Process chunks in parallel using ThreadPoolExecutor
        max_workers = min(5, len(code_chunks))

        if len(code_chunks) > 1:
            # print(f"   Using {max_workers} parallel workers for faster processing")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all chunks for processing
                future_to_chunk = {
                    executor.submit(
                        self._process_chunk,
                        idx + 1,
                        chunk,
                        file_list,
                        len(code_chunks),
                    ): idx + 1
                    for idx, chunk in enumerate(code_chunks)
                }

                # Collect results as they complete
                for future in as_completed(future_to_chunk):
                    chunk_idx = future_to_chunk[future]
                    try:
                        scenarios = future.result()
                        all_scenarios.extend(scenarios)
                    except Exception as e:
                        print(f"   ⚠️  Error processing chunk {chunk_idx}: {e}")
        else:
            # Single chunk - no need for parallelization
            scenarios = self._process_chunk(1, code_chunks[0], file_list, 1)
            all_scenarios.extend(scenarios)

        # Deduplicate scenarios based on description similarity
        unique_scenarios = []
        seen_descriptions = set()

        for scenario in all_scenarios:
            # Normalize description for comparison
            normalized = scenario.scenario_description.lower().strip()
            if normalized not in seen_descriptions:
                seen_descriptions.add(normalized)
                unique_scenarios.append(scenario)

        print(
            f"   Identified {len(all_scenarios)} scenarios ({len(unique_scenarios)} unique)"
        )
        return TestScenariosOutput(test_scenarios=unique_scenarios)

    def _process_chunk(
        self, chunk_idx: int, code_chunk: str, file_list: str, total_chunks: int
    ) -> List[TestScenario]:
        """Process a single code chunk to identify test scenarios."""
        # Create a dedicated LLM client for this thread/worker
        llm_client = create_llm_client(use_mock_on_failure=False)

        # print(f"   Processing chunk {chunk_idx}/{total_chunks}...")

        user_prompt = f"""Analyze this Python codebase chunk and identify test scenarios.

Files in project: {file_list}

Code chunk {chunk_idx} of {total_chunks}:
{code_chunk}

Respond with JSON containing test_scenarios."""

        response, is_mock = llm_client.call(IDENTIFICATION_SYSTEM_PROMPT, user_prompt)

        # Record this prompt in history
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        prompt_record = {
            "timestamp": timestamp,
            "agent": "identification_agent",
            "model": getattr(llm_client, "last_used_model", None) or llm_client.current_model,
            "system_prompt": IDENTIFICATION_SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "response": response,
            "is_mock": is_mock,
        }
        self.prompt_history.append(prompt_record)

        try:
            if "```" in response:
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
                if json_match:
                    response = json_match.group(1).strip()

            data = json.loads(response)
            chunk_scenarios = [TestScenario(**s) for s in data["test_scenarios"]]
            return chunk_scenarios
        except (json.JSONDecodeError, KeyError) as e:
            print(f"   ⚠️  Warning: Failed to parse response for chunk {chunk_idx}: {e}")
            return []


class ImplementationAgent(BaseAgent):
    def run(
        self, scenarios: TestScenariosOutput, codebase_path: Path, output_dir: Path
    ) -> Tuple[str, Path]:
        """Generates PyTest test code from approved scenarios."""
        print("\n🔧 Agent 2: Generating PyTest test code...")

        python_files = gather_python_files(codebase_path)

        # Use chunked reading and limit to reasonable amount
        code_chunks = read_file_contents_chunked(python_files)
        # Take first 10 chunks to provide enough context without exceeding tokens
        max_chunks = 10
        selected_chunks = code_chunks[:max_chunks]
        code_context = "\n\n".join(selected_chunks)

        chunk_info = (
            f"{len(selected_chunks)} of {len(code_chunks)} code chunks"
            if len(code_chunks) > max_chunks
            else f"{len(code_chunks)} code chunks"
        )
        print(f"   Using {chunk_info} for context")

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

Source code (showing {chunk_info}):
{code_context}

IMPORTANT RULES:
1. Return ONLY valid Python code - no markdown, no code fences
2. Include all necessary imports at the top
3. Each test function must start with 'test_'
4. IMPORT source modules directly for coverage (add project root to sys.path first)
5. Use mocking for side effects (network, file I/O)
6. Use proc.terminate() instead of signal.SIGINT for stopping processes

Generate a complete, executable PyTest file."""

        response = self.call_llm(
            IMPLEMENTATION_SYSTEM_PROMPT, user_prompt, agent_name="implementation_agent"
        )
        test_code = sanitize_code(response)

        # Validate syntax and fix if needed (up to 3 attempts)
        for attempt in range(3):
            is_valid, error_msg, error_details = validate_syntax(test_code)
            if is_valid:
                break
            test_code = self.fix_syntax_errors(
                test_code, error_msg, codebase_path, error_details
            )

        # Final validation
        is_valid, error_msg, error_details = validate_syntax(test_code)
        if not is_valid:
            print(f"   ⚠️ Warning: Generated code may have syntax errors: {error_msg}")
            governance_log.log_validation(
                "syntax_validator",
                "generated_test_code",
                False,
                f"Hallucination: Syntax error in LLM output - {error_msg}",
            )

        # Explicit hallucination detection
        hallucinations = detect_hallucinations(test_code, codebase_path)
        if hallucinations:
            print(
                f"   ⚠️ Hallucinations detected: {len(hallucinations)} invalid import(s)"
            )
            for h in hallucinations:
                governance_log.log_validation(
                    "hallucination_detector",
                    h["name"],
                    False,
                    f"Hallucination: {h['reason']}",
                )
            # Attempt to fix hallucinations
            test_code = self.fix_hallucinations(test_code, hallucinations, codebase_path)
            governance_log.log_failure(
                FailureReason.HALLUCINATION,
                f"{len(hallucinations)} hallucination(s) detected and corrected",
                0,
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        test_file = output_dir / f"test_generated_{int(time.time())}.py"

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)

        print(f"   Generated: {test_file}")
        return test_code, test_file

    def improve_tests(
        self,
        codebase_path: Path,
        existing_test_file: Path,
        coverage_percentage: float,
        uncovered_areas: str,
        syntax_errors: str = "",
        security_issues: List[SecurityIssue] = None,
    ) -> Tuple[str, Path]:
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

        python_files = gather_python_files(codebase_path)
        # Limit context size to prevent 413 errors - use chunked reading
        code_chunks = read_file_contents_chunked(python_files)
        # Use first 10 chunks and truncate at logical boundary
        raw_context = "\n\n".join(code_chunks[:10])
        code_context = truncate_at_boundary(raw_context, 15000)

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
{existing_tests[:1500]}

Uncovered code areas from coverage report:
{uncovered_areas[:2000]}

Source code to test (truncated to fit limits):
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

        response = self.call_llm(
            IMPLEMENTATION_SYSTEM_PROMPT,
            user_prompt,
            agent_name="implementation_agent_improvement",
        )
        test_code = sanitize_code(response)

        # Validate syntax and fix if needed
        for attempt in range(3):
            is_valid, error_msg, error_details = validate_syntax(test_code)
            if is_valid:
                break
            test_code = self.fix_syntax_errors(
                test_code, error_msg, codebase_path, error_details
            )

        # Final validation
        is_valid, error_msg, error_details = validate_syntax(test_code)
        if not is_valid:
            print(f"   ⚠️ Warning: Code may still have syntax errors: {error_msg}")

        # Overwrite existing file
        with open(existing_test_file, "w", encoding="utf-8") as f:
            f.write(test_code)

        print(f"   Updated: {existing_test_file}")
        return test_code, existing_test_file

    def fix_hallucinations(
        self, code: str, hallucinations: List[dict], codebase_path: Path
    ) -> str:
        """Uses LLM to fix hallucinated imports and symbols in generated code."""
        print(f"   🔧 Fixing {len(hallucinations)} hallucination(s)...")

        # Get list of actual modules and symbols from codebase
        python_files = gather_python_files(codebase_path)
        actual_modules = [f.stem for f in python_files]

        # Extract actual function/class names from codebase for reference
        actual_symbols = []
        for file_path in python_files[:5]:  # Limit to first 5 files for performance
            try:
                from pipeline.code_utils import extract_code_definitions

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                definitions = extract_code_definitions(content, recursive=False)
                actual_symbols.extend([d.name for d in definitions])
            except Exception:
                pass

        # Format hallucinations for the prompt
        hallucination_list = "\n".join(
            f"- {h['name']}: {h['reason']}" for h in hallucinations
        )

        user_prompt = f"""Fix the following test code by replacing invalid imports and symbols.

HALLUCINATIONS DETECTED:
{hallucination_list}

AVAILABLE MODULES IN CODEBASE:
{', '.join(actual_modules)}

AVAILABLE FUNCTIONS/CLASSES IN CODEBASE:
{', '.join(set(actual_symbols)) if actual_symbols else 'None extracted'}

CODE TO FIX:
{truncate_at_boundary(code, 12000)}

Return ONLY the corrected Python code."""

        response = self.call_llm(
            HALLUCINATION_FIX_PROMPT, user_prompt, agent_name="hallucination_fixer"
        )
        fixed_code = sanitize_code(response)

        # Validate the fix didn't introduce syntax errors
        is_valid, _, _ = validate_syntax(fixed_code)
        if is_valid:
            print("   ✓ Hallucinations fixed successfully")
            return fixed_code
        else:
            print("   ⚠️ Fix introduced syntax errors, keeping original")
            return code

    def fix_syntax_errors(
        self, code: str, error_msg: str, codebase_path: Path, error_details: dict = None
    ) -> str:
        """Asks LLM to fix syntax errors in generated code with enhanced context."""
        print(f"   ⚠️ Syntax error detected: {error_msg}")
        print("   🔧 Attempting to fix...")

        # Extract context window around the error
        code_lines = code.splitlines()
        context_window = ""

        if error_details and error_details.get("lineno"):
            error_line = error_details["lineno"]
            error_col = error_details.get("offset", 0)

            # Show ±5 lines around the error
            start_line = max(1, error_line - 5)
            end_line = min(len(code_lines), error_line + 5)

            context_lines = []
            for i in range(start_line, end_line + 1):
                line_num = i
                line_content = code_lines[i - 1] if i <= len(code_lines) else ""

                # Mark the error line with >>>
                if i == error_line:
                    marker = ">>> "
                    # Add column marker if available
                    if error_col > 0:
                        context_lines.append(f"{marker}{line_num:3d}: {line_content}")
                        context_lines.append(
                            f"         {' ' * (error_col - 1)}^ ERROR HERE"
                        )
                    else:
                        context_lines.append(
                            f"{marker}{line_num:3d}: {line_content}  # <-- ERROR HERE"
                        )
                else:
                    context_lines.append(f"    {line_num:3d}: {line_content}")

            context_window = "\n".join(context_lines)
        else:
            # Fallback: show first 20 lines with line numbers
            context_lines = [
                f"    {i + 1:3d}: {line}" for i, line in enumerate(code_lines[:20])
            ]
            context_window = "\n".join(context_lines)
            if len(code_lines) > 20:
                context_window += f"\n    ... ({len(code_lines) - 20} more lines)"

        # Use chunked reading for source context
        python_files = gather_python_files(codebase_path)
        source_chunks = read_file_contents_chunked(python_files)
        source_context = "\n\n".join(source_chunks[:2])  # First 2 chunks

        fix_prompt = f"""SYNTAX ERROR DETECTED IN GENERATED TEST CODE

ERROR DETAILS:
  Type: SyntaxError
  Message: {error_msg}
  {f"Line: {error_details['lineno']}, Column: {error_details['offset']}" if error_details else ""}

PROBLEMATIC CODE SECTION:
{context_window}

FULL GENERATED CODE:
{code}

SOURCE CODE BEING TESTED (for reference):
{source_context[:1500]}

INSTRUCTIONS:
Your task is to fix the syntax error in the test code above.
1. Identify the exact syntax issue based on the error location and message
2. Fix ONLY the syntax error (maintain all test logic)
3. Return ONLY valid Python code with NO markdown formatting
4. Do NOT include code fences (``` or ```python)
5. Return the complete, corrected test file

Return the fixed code now:"""

        response = self.call_llm(
            IMPLEMENTATION_SYSTEM_PROMPT, fix_prompt, agent_name="syntax_fixer"
        )
        return sanitize_code(response)


class EvaluationAgent(BaseAgent):
    def run(
        self, test_results: dict, scenarios: TestScenariosOutput, codebase_path: Path
    ) -> TestEvaluationOutput:
        """Evaluates test results, coverage, and security."""
        print("\nAgent 3: Evaluating test results and security...")

        # Use actual measured values
        actual_coverage = test_results.get("coverage_percentage", 0.0)
        actual_mutation_score = test_results.get("mutation_score", 0.0)
        mutation_feedback = test_results.get("mutation_feedback", "")
        total_tests = test_results.get("total_tests", 0)
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)

        print(f"   Actual coverage measured: {actual_coverage:.1f}%")
        if actual_mutation_score > 0:
            print(f"   Mutation score: {actual_mutation_score:.1f}%")

        # Gather source code for security analysis - limit size to prevent 413
        python_files = gather_python_files(codebase_path)
        code_chunks = read_file_contents_chunked(python_files)
        source_code = "\n\n".join(code_chunks[:10])[:15000]  # Max 15000 chars

        # Build mutation section for the prompt
        mutation_section = ""
        if mutation_feedback:
            mutation_section = f"""\n\nMutation Coverage:
{mutation_feedback}

Mutation coverage shows test effectiveness. Survived mutants indicate
gaps where tests pass even when bugs are introduced.
Target: Aim for >80% mutation score for robust test suites."""

        scenarios_json = json.dumps(asdict(scenarios), indent=2)[
            :2000
        ]  # Limit scenarios too
        user_prompt = f"""Evaluate these PyTest results AND perform security analysis:

Scenarios (summary): {scenarios_json}

Test Results:
- Total tests: {total_tests}
- Passed: {passed}
- Failed: {failed}
- Code Coverage: {actual_coverage:.1f}%
- Mutation Score: {actual_mutation_score:.1f}%{mutation_section}

PyTest Output:
{test_results.get("output", "")[:2000]}

Source Code (analyze for security issues):
{source_code}

Provide:
1. Actionable recommendations to improve test coverage and fix failures
2. Security analysis identifying vulnerabilities (SQL injection, XSS, command injection, path traversal, hardcoded secrets, etc.)
3. Mark has_severe_security_issues as true if any critical or high severity issues exist

Respond with JSON containing execution_summary, code_coverage_percentage, security_issues, has_severe_security_issues, and actionable_recommendations."""

        response = self.call_llm(
            EVALUATION_SYSTEM_PROMPT, user_prompt, agent_name="evaluation_agent"
        )

        try:
            if "```" in response:
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
                if json_match:
                    response = json_match.group(1).strip()

            data = json.loads(response)

            # Fix: Handle case where LLM returns a list [ { ... } ] instead of a dict { ... }
            if isinstance(data, list):
                if data and isinstance(data[0], dict):
                    data = data[0]
                else:
                    # If it's a list but not containing a dict, validation will fail gracefully below
                    # when looking for keys in an empty dict or by letting it proceed if it was just []
                    data = {}

            # Parse security issues
            security_issues = []
            for issue_data in data.get("security_issues", []):
                # Fix: Ensure issue_data is a dictionary before calling .get()
                if not isinstance(issue_data, dict):
                    continue

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
                print(f"   Security issues found: {len(security_issues)}")
                severe_count = sum(
                    1 for si in security_issues if si.severity in ("critical", "high")
                )
                if severe_count > 0:
                    print(f"   Severe issues (critical/high): {severe_count}")

            # Override with actual measured values
            return TestEvaluationOutput(
                execution_summary=ExecutionSummary(
                    total_tests=total_tests, passed=passed, failed=failed
                ),
                code_coverage_percentage=actual_coverage,
                actionable_recommendations=data.get("actionable_recommendations", []),
                security_issues=security_issues,
                has_severe_security_issues=has_severe,
                mutation_score=actual_mutation_score,
                mutation_report=test_results.get("mutation_report"),
            )
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            # Return actual values even if LLM parsing fails
            return TestEvaluationOutput(
                execution_summary=ExecutionSummary(
                    total_tests=total_tests, passed=passed, failed=failed
                ),
                code_coverage_percentage=actual_coverage,
                actionable_recommendations=[f"Evaluation parsing failed: {e}"],
                security_issues=[],
                has_severe_security_issues=False,
                mutation_score=actual_mutation_score,
                mutation_report=test_results.get("mutation_report"),
            )
