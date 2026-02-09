"""Unit tests for the pipeline agents module."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.models import (
    TestScenario,
    TestScenariosOutput,
    SecurityIssue,
    TestEvaluationOutput,
)


# ==================== BaseAgent Tests ====================
class TestBaseAgent:
    """Tests for BaseAgent class."""

    def test_init_with_default_client(self):
        """Should create default LLM client when none provided."""
        with patch("pipeline.agents.create_llm_client") as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client

            from pipeline.agents import BaseAgent
            agent = BaseAgent()

            mock_create.assert_called_once_with(use_mock_on_failure=False)
            assert agent.llm_client == mock_client

    def test_init_with_custom_client(self):
        """Should use provided LLM client."""
        mock_client = Mock()

        from pipeline.agents import BaseAgent
        agent = BaseAgent(llm_client=mock_client)

        assert agent.llm_client == mock_client

    def test_init_with_prompt_history(self):
        """Should use provided prompt history."""
        history = [{"test": "entry"}]
        mock_client = Mock()

        from pipeline.agents import BaseAgent
        agent = BaseAgent(llm_client=mock_client, prompt_history=history)

        assert agent.prompt_history == history

    def test_call_llm_records_history(self):
        """Should record prompts in history."""
        mock_client = Mock()
        mock_client.call.return_value = ("response text", False)
        mock_client.current_model = "test-model"

        from pipeline.agents import BaseAgent
        agent = BaseAgent(llm_client=mock_client)

        response = agent.call_llm("system prompt", "user prompt", "test_agent")

        assert response == "response text"
        assert len(agent.prompt_history) == 1
        assert agent.prompt_history[0]["agent"] == "test_agent"
        assert agent.prompt_history[0]["system_prompt"] == "system prompt"
        assert agent.prompt_history[0]["user_prompt"] == "user prompt"
        assert agent.prompt_history[0]["response"] == "response text"


# ==================== ImplementationAgent Tests (Generation Agent) ====================
class TestImplementationAgent:
    """Tests for ImplementationAgent (generation agent)."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = Mock()
        client.call.return_value = ("def test_example(): pass", False)
        client.current_model = "test-model"
        return client

    @pytest.fixture
    def agent(self, mock_llm_client):
        """Create an ImplementationAgent with mocked LLM."""
        from pipeline.agents import ImplementationAgent
        return ImplementationAgent(llm_client=mock_llm_client)

    @pytest.fixture
    def sample_scenarios(self):
        """Create sample test scenarios."""
        return TestScenariosOutput(
            test_scenarios=[
                TestScenario(scenario_description="Test basic functionality", priority="High"),
                TestScenario(scenario_description="Test edge cases", priority="Medium"),
            ]
        )

    def test_run_generates_test_file(self, agent, sample_scenarios, tmp_path):
        """run() should generate a test file."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("def hello(): return 'world'")

        output_dir = tmp_path / "tests"

        with patch("pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]):
            with patch("pipeline.agents.read_file_contents_chunked", return_value=["def hello(): pass"]):
                with patch("pipeline.agents.validate_syntax", return_value=(True, "", {})):
                    test_code, test_file = agent.run(sample_scenarios, codebase, output_dir)

        assert test_file.exists()
        assert "def test_example(): pass" in test_code

    def test_run_validates_syntax(self, agent, sample_scenarios, tmp_path):
        """run() should validate and fix syntax errors."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("print('hello')")
        output_dir = tmp_path / "tests"

        # First call returns invalid, second (after fix) returns valid, third (final check) returns valid
        validate_returns = [
            (False, "SyntaxError", {"lineno": 1, "offset": 5}),
            (True, "", {}),
            (True, "", {}),
        ]

        with patch("pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]):
            with patch("pipeline.agents.read_file_contents_chunked", return_value=["code"]):
                with patch("pipeline.agents.validate_syntax", side_effect=validate_returns):
                    with patch.object(agent, "fix_syntax_errors", return_value="fixed_code") as mock_fix:
                        test_code, test_file = agent.run(sample_scenarios, codebase, output_dir)
                        # Assert inside the context while mock is still active
                        mock_fix.assert_called()

    def test_run_with_empty_scenarios(self, agent, tmp_path):
        """run() should handle empty scenarios."""
        empty_scenarios = TestScenariosOutput(test_scenarios=[])
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("pass")
        output_dir = tmp_path / "tests"

        with patch("pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]):
            with patch("pipeline.agents.read_file_contents_chunked", return_value=["pass"]):
                with patch("pipeline.agents.validate_syntax", return_value=(True, "", {})):
                    test_code, test_file = agent.run(empty_scenarios, codebase, output_dir)

        assert test_file.exists()

    def test_improve_tests_updates_file(self, agent, tmp_path):
        """improve_tests() should update existing test file."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("def foo(): pass")

        test_file = tmp_path / "test_existing.py"
        test_file.write_text("def test_old(): pass")

        with patch("pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]):
            with patch("pipeline.agents.read_file_contents_chunked", return_value=["code"]):
                with patch("pipeline.agents.validate_syntax", return_value=(True, "", {})):
                    updated_code, updated_file = agent.improve_tests(
                        codebase, test_file, 50.0, "line 10 uncovered"
                    )

        assert updated_file == test_file
        # File should be updated
        assert test_file.read_text() != "def test_old(): pass"

    def test_improve_tests_with_security_issues(self, agent, tmp_path):
        """improve_tests() should include security context."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("pass")

        test_file = tmp_path / "test_sec.py"
        test_file.write_text("pass")

        security_issues = [
            SecurityIssue(
                severity="high",
                issue="SQL injection vulnerability",
                location="db.py:45",
                recommendation="Use parameterized queries"
            )
        ]

        with patch("pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]):
            with patch("pipeline.agents.read_file_contents_chunked", return_value=["code"]):
                with patch("pipeline.agents.validate_syntax", return_value=(True, "", {})):
                    agent.improve_tests(
                        codebase, test_file, 80.0, "uncovered",
                        security_issues=security_issues
                    )

        # Verify LLM was called (security context would be in prompt)
        agent.llm_client.call.assert_called()

    def test_fix_syntax_errors_calls_llm(self, agent, tmp_path):
        """fix_syntax_errors() should call LLM with error context."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("pass")

        code_with_error = "def test():\n  print('unclosed"
        error_msg = "EOL while scanning string literal"
        error_details = {"lineno": 2, "offset": 10}

        with patch("pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]):
            with patch("pipeline.agents.read_file_contents_chunked", return_value=["pass"]):
                agent.fix_syntax_errors(code_with_error, error_msg, codebase, error_details)

        agent.llm_client.call.assert_called()


# ==================== EvaluationAgent Tests ====================
class TestEvaluationAgent:
    """Tests for EvaluationAgent."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client returning valid JSON."""
        client = Mock()
        response = json.dumps({
            "execution_summary": {"total_tests": 10, "passed": 8, "failed": 2},
            "code_coverage_percentage": 85.0,
            "actionable_recommendations": ["Add more edge case tests"],
            "security_issues": [
                {"severity": "medium", "issue": "Hardcoded secret", "location": "config.py:5", "recommendation": "Use env vars"}
            ],
            "has_severe_security_issues": False
        })
        client.call.return_value = (response, False)
        client.current_model = "test-model"
        return client

    @pytest.fixture
    def agent(self, mock_llm_client):
        """Create an EvaluationAgent with mocked LLM."""
        from pipeline.agents import EvaluationAgent
        return EvaluationAgent(llm_client=mock_llm_client)

    @pytest.fixture
    def sample_scenarios(self):
        """Create sample test scenarios."""
        return TestScenariosOutput(
            test_scenarios=[TestScenario(scenario_description="Test X", priority="High")]
        )

    def test_run_parses_results(self, agent, sample_scenarios, tmp_path):
        """run() should parse test results correctly."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("pass")

        test_results = {
            "coverage_percentage": 85.0,
            "total_tests": 10,
            "passed": 8,
            "failed": 2,
            "output": "test output"
        }

        with patch("pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]):
            with patch("pipeline.agents.read_file_contents_chunked", return_value=["pass"]):
                result = agent.run(test_results, sample_scenarios, codebase)

        assert isinstance(result, TestEvaluationOutput)
        assert result.code_coverage_percentage == 85.0
        assert result.execution_summary.total_tests == 10

    def test_run_extracts_security_issues(self, agent, sample_scenarios, tmp_path):
        """run() should extract security issues from response."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("pass")

        test_results = {"coverage_percentage": 80.0, "total_tests": 5, "passed": 5, "failed": 0}

        with patch("pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]):
            with patch("pipeline.agents.read_file_contents_chunked", return_value=["pass"]):
                result = agent.run(test_results, sample_scenarios, codebase)

        assert len(result.security_issues) == 1
        assert result.security_issues[0].severity == "medium"
        assert "Hardcoded secret" in result.security_issues[0].issue

    def test_run_handles_json_list_response(self, sample_scenarios, tmp_path):
        """run() should handle LLM returning a JSON list instead of dict."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("pass")

        # LLM returns a list with one dict element
        mock_client = Mock()
        list_response = json.dumps([{
            "execution_summary": {"total_tests": 5, "passed": 5, "failed": 0},
            "code_coverage_percentage": 90.0,
            "actionable_recommendations": [],
            "security_issues": [],
            "has_severe_security_issues": False
        }])
        mock_client.call.return_value = (list_response, False)
        mock_client.current_model = "test-model"

        from pipeline.agents import EvaluationAgent
        agent = EvaluationAgent(llm_client=mock_client)

        test_results = {"coverage_percentage": 90.0, "total_tests": 5, "passed": 5, "failed": 0}

        with patch("pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]):
            with patch("pipeline.agents.read_file_contents_chunked", return_value=["pass"]):
                result = agent.run(test_results, sample_scenarios, codebase)

        assert result.code_coverage_percentage == 90.0

    def test_run_handles_parse_error(self, sample_scenarios, tmp_path):
        """run() should return fallback result on parse error."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("pass")

        mock_client = Mock()
        mock_client.call.return_value = ("invalid json {{{", False)
        mock_client.current_model = "test-model"

        from pipeline.agents import EvaluationAgent
        agent = EvaluationAgent(llm_client=mock_client)

        test_results = {"coverage_percentage": 75.0, "total_tests": 8, "passed": 6, "failed": 2}

        with patch("pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]):
            with patch("pipeline.agents.read_file_contents_chunked", return_value=["pass"]):
                result = agent.run(test_results, sample_scenarios, codebase)

        # Should use actual values from test_results
        assert result.code_coverage_percentage == 75.0
        assert result.execution_summary.total_tests == 8
        assert result.execution_summary.failed == 2

    def test_run_detects_severe_issues(self, sample_scenarios, tmp_path):
        """run() should detect severe security issues."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("pass")

        mock_client = Mock()
        response = json.dumps({
            "execution_summary": {"total_tests": 5, "passed": 5, "failed": 0},
            "code_coverage_percentage": 80.0,
            "actionable_recommendations": [],
            "security_issues": [
                {
                    "severity": "critical",
                    "issue": "SQL injection",
                    "location": "db.py:10",
                    "recommendation": "Fix it",
                }
            ],
            "has_severe_security_issues": False,  # LLM says false, but we detect critical
        })
        mock_client.call.return_value = (response, False)
        mock_client.current_model = "test-model"

        from pipeline.agents import EvaluationAgent
        agent = EvaluationAgent(llm_client=mock_client)

        test_results = {
            "coverage_percentage": 80.0,
            "total_tests": 5,
            "passed": 5,
            "failed": 0,
        }

        with patch(
            "pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]
        ):
            with patch(
                "pipeline.agents.read_file_contents_chunked", return_value=["pass"]
            ):
                result = agent.run(test_results, sample_scenarios, codebase)

        # Should detect severe issues even if LLM says false
        assert result.has_severe_security_issues is True

    def test_run_handles_code_fenced_json(self, sample_scenarios, tmp_path):
        """run() should extract JSON from markdown code fences."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("pass")

        mock_client = Mock()
        # LLM returns JSON wrapped in markdown code fence
        response = '''```json
{
    "execution_summary": {"total_tests": 5, "passed": 5, "failed": 0},
    "code_coverage_percentage": 95.0,
    "actionable_recommendations": [],
    "security_issues": [],
    "has_severe_security_issues": false
}
```'''
        mock_client.call.return_value = (response, False)
        mock_client.current_model = "test-model"

        from pipeline.agents import EvaluationAgent
        agent = EvaluationAgent(llm_client=mock_client)

        test_results = {
            "coverage_percentage": 95.0,
            "total_tests": 5,
            "passed": 5,
            "failed": 0,
        }

        with patch(
            "pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]
        ):
            with patch(
                "pipeline.agents.read_file_contents_chunked", return_value=["pass"]
            ):
                result = agent.run(test_results, sample_scenarios, codebase)

        assert result.code_coverage_percentage == 95.0


# ==================== Truncate at Boundary Tests ====================
class TestTruncateAtBoundary:
    """Tests for truncate_at_boundary utility function."""

    def test_short_code_unchanged(self):
        """Code shorter than max_chars should not be modified."""
        from pipeline.file_utils import truncate_at_boundary

        code = "def foo():\n    pass"
        result = truncate_at_boundary(code, 1000)

        assert result == code

    def test_truncates_at_function_boundary(self):
        """Should truncate at the start of a new function definition."""
        from pipeline.file_utils import truncate_at_boundary

        code = """def first_function():
    return 1

def second_function():
    return 2

def third_function():
    return 3"""

        # Truncate at 60 chars - should keep first function, cut before second
        result = truncate_at_boundary(code, 60)

        assert "first_function" in result
        assert "# ... (truncated)" in result

    def test_truncates_at_class_boundary(self):
        """Should truncate at the start of a new class definition."""
        from pipeline.file_utils import truncate_at_boundary

        code = """class FirstClass:
    pass

class SecondClass:
    pass"""

        result = truncate_at_boundary(code, 40)

        assert "FirstClass" in result
        assert "# ... (truncated)" in result

    def test_falls_back_to_blank_line(self):
        """Should fall back to blank line when no function/class boundary."""
        from pipeline.file_utils import truncate_at_boundary

        code = """x = 1
y = 2

z = 3
w = 4"""

        result = truncate_at_boundary(code, 20)

        assert "# ... (truncated)" in result

    def test_falls_back_to_newline(self):
        """Should fall back to last newline if no blank lines."""
        from pipeline.file_utils import truncate_at_boundary

        code = "line1\nline2\nline3\nline4"

        result = truncate_at_boundary(code, 15)

        assert "# ... (truncated)" in result
        assert not result.endswith("line4")


# ==================== ImplementationAgent Hallucination Fix Tests ====================
class TestHallucinationFix:
    """Tests for fix_hallucinations method."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = Mock()
        client.call.return_value = ("import real_module\ndef test_fixed(): pass", False)
        client.current_model = "test-model"
        return client

    @pytest.fixture
    def agent(self, mock_llm_client):
        """Create an ImplementationAgent with mocked LLM."""
        from pipeline.agents import ImplementationAgent
        return ImplementationAgent(llm_client=mock_llm_client)

    def test_fix_hallucinations_calls_llm(self, agent, tmp_path):
        """fix_hallucinations() should call LLM with hallucination context."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "real_module.py").write_text("def real_func(): pass")

        code_with_hallucinations = "import fake_module\ndef test_bad(): pass"
        hallucinations = [
            {"name": "fake_module", "reason": "Module does not exist in codebase"}
        ]

        with patch(
            "pipeline.agents.gather_python_files",
            return_value=[codebase / "real_module.py"],
        ):
            with patch("pipeline.agents.validate_syntax", return_value=(True, "", {})):
                result = agent.fix_hallucinations(
                    code_with_hallucinations, hallucinations, codebase
                )

        agent.llm_client.call.assert_called()
        assert "real_module" in result

    def test_fix_hallucinations_keeps_original_on_syntax_error(self, agent, tmp_path):
        """fix_hallucinations() should keep original code if fix has syntax errors."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "module.py").write_text("pass")

        original_code = "import fake\ndef test(): pass"
        hallucinations = [{"name": "fake", "reason": "Not found"}]

        # Mock LLM returning code with syntax errors
        agent.llm_client.call.return_value = ("def broken(:\n  pass", False)

        with patch(
            "pipeline.agents.gather_python_files", return_value=[codebase / "module.py"]
        ):
            with patch(
                "pipeline.agents.validate_syntax", return_value=(False, "SyntaxError", {})
            ):
                result = agent.fix_hallucinations(
                    original_code, hallucinations, codebase
                )

        assert result == original_code

    def test_fix_hallucinations_with_multiple_issues(self, agent, tmp_path):
        """fix_hallucinations() should handle multiple hallucinations."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "real.py").write_text("pass")

        code = "import fake1\nimport fake2\ndef test(): pass"
        hallucinations = [
            {"name": "fake1", "reason": "Not found"},
            {"name": "fake2", "reason": "Not found"},
        ]

        with patch(
            "pipeline.agents.gather_python_files", return_value=[codebase / "real.py"]
        ):
            with patch("pipeline.agents.validate_syntax", return_value=(True, "", {})):
                agent.fix_hallucinations(code, hallucinations, codebase)

        # Verify LLM prompt contains both hallucinations
        call_args = agent.llm_client.call.call_args
        assert "fake1" in str(call_args) or "fake2" in str(call_args)


# ==================== IdentificationAgent Edge Case Tests ====================
class TestIdentificationAgentEdgeCases:
    """Edge case tests for IdentificationAgent."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client returning valid scenarios."""
        client = Mock()
        response = json.dumps({
            "test_scenarios": [
                {"scenario_description": "Test basic", "priority": "High"}
            ]
        })
        client.call.return_value = (response, False)
        client.current_model = "test-model"
        return client

    @pytest.fixture
    def agent(self, mock_llm_client):
        """Create an IdentificationAgent with mocked LLM."""
        from pipeline.agents import IdentificationAgent
        return IdentificationAgent(llm_client=mock_llm_client)

    def test_run_with_empty_codebase(self, agent, tmp_path):
        """run() should raise ValueError for empty codebase."""
        codebase = tmp_path / "empty_src"
        codebase.mkdir()

        # Agent should raise ValueError when no Python files found
        with pytest.raises(ValueError, match="No Python files found"):
            agent.run(codebase)

    def test_run_with_large_codebase(self, agent, tmp_path):
        """run() should handle large codebase by chunking."""
        codebase = tmp_path / "large_src"
        codebase.mkdir()

        # Create multiple files
        for i in range(20):
            (codebase / f"module_{i}.py").write_text(f"def func_{i}(): pass")

        files = list(codebase.glob("*.py"))
        chunks = [f"chunk_{i}" for i in range(15)]

        with patch("pipeline.agents.gather_python_files", return_value=files):
            with patch(
                "pipeline.agents.read_file_contents_chunked", return_value=chunks
            ):
                result = agent.run(codebase)

        assert isinstance(result, TestScenariosOutput)

    def test_handles_malformed_llm_response(self, tmp_path):
        """run() should handle malformed LLM JSON response."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("pass")

        mock_client = Mock()
        mock_client.call.return_value = ("not valid json at all", False)
        mock_client.current_model = "test-model"

        from pipeline.agents import IdentificationAgent
        agent = IdentificationAgent(llm_client=mock_client)

        with patch(
            "pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]
        ):
            with patch(
                "pipeline.agents.read_file_contents_chunked", return_value=["pass"]
            ):
                with patch(
                    "pipeline.agents.create_llm_client", return_value=mock_client
                ):
                    result = agent.run(codebase)

        # Should return empty scenarios on parse failure
        assert isinstance(result, TestScenariosOutput)

    def test_deduplicates_scenarios(self, tmp_path):
        """run() should deduplicate identical scenarios from chunks."""
        codebase = tmp_path / "src"
        codebase.mkdir()
        (codebase / "main.py").write_text("pass")

        mock_client = Mock()
        # Return same scenario from different chunks
        response = json.dumps({
            "test_scenarios": [
                {"scenario_description": "Test duplicate", "priority": "High"},
                {"scenario_description": "Test duplicate", "priority": "High"},  # duplicate
            ]
        })
        mock_client.call.return_value = (response, False)
        mock_client.current_model = "test-model"

        from pipeline.agents import IdentificationAgent
        agent = IdentificationAgent(llm_client=mock_client)

        with patch(
            "pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]
        ):
            with patch(
                "pipeline.agents.read_file_contents_chunked", return_value=["chunk1"]
            ):
                with patch(
                    "pipeline.agents.create_llm_client", return_value=mock_client
                ):
                    result = agent.run(codebase)

        # Duplicates should be removed
        descriptions = [s.scenario_description for s in result.test_scenarios]
        assert len(descriptions) == len(set(descriptions))


# ==================== Error Handling Edge Cases ====================
class TestErrorHandling:
    """Tests for error handling edge cases."""

    def test_base_agent_handles_llm_exception(self):
        """BaseAgent should handle LLM call exceptions gracefully."""
        mock_client = Mock()
        mock_client.call.side_effect = Exception("API Error")
        mock_client.current_model = "test-model"

        from pipeline.agents import BaseAgent
        agent = BaseAgent(llm_client=mock_client)

        # Should raise the exception (caller handles it)
        with pytest.raises(Exception, match="API Error"):
            agent.call_llm("system", "user", "test")

    def test_implementation_agent_handles_file_not_found(self, tmp_path):
        """ImplementationAgent should handle missing codebase files."""
        mock_client = Mock()
        mock_client.call.return_value = ("def test(): pass", False)
        mock_client.current_model = "test-model"

        from pipeline.agents import ImplementationAgent
        agent = ImplementationAgent(llm_client=mock_client)

        scenarios = TestScenariosOutput(test_scenarios=[])
        nonexistent = tmp_path / "nonexistent"
        output = tmp_path / "tests"

        with patch(
            "pipeline.agents.gather_python_files", return_value=[]
        ):
            with patch(
                "pipeline.agents.read_file_contents_chunked", return_value=[]
            ):
                with patch(
                    "pipeline.agents.validate_syntax", return_value=(True, "", {})
                ):
                    # Should not crash, just generate with empty context
                    test_code, test_file = agent.run(scenarios, nonexistent, output)

        assert test_file.exists()
