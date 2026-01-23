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
                {"severity": "critical", "issue": "SQL injection", "location": "db.py:10", "recommendation": "Fix it"}
            ],
            "has_severe_security_issues": False  # LLM says false, but we detect critical
        })
        mock_client.call.return_value = (response, False)
        mock_client.current_model = "test-model"
        
        from pipeline.agents import EvaluationAgent
        agent = EvaluationAgent(llm_client=mock_client)
        
        test_results = {"coverage_percentage": 80.0, "total_tests": 5, "passed": 5, "failed": 0}
        
        with patch("pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]):
            with patch("pipeline.agents.read_file_contents_chunked", return_value=["pass"]):
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
        
        test_results = {"coverage_percentage": 95.0, "total_tests": 5, "passed": 5, "failed": 0}
        
        with patch("pipeline.agents.gather_python_files", return_value=[codebase / "main.py"]):
            with patch("pipeline.agents.read_file_contents_chunked", return_value=["pass"]):
                result = agent.run(test_results, sample_scenarios, codebase)
        
        assert result.code_coverage_percentage == 95.0
