"""Tests for the API endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from src.extension.api.main import app

    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health and info endpoints."""

    def test_health(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_info(self, client):
        """Info endpoint should return version and models."""
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "available_models" in data
        assert "default_model" in data


class TestUtilityEndpoints:
    """Tests for utility endpoints."""

    def test_parse_output(self, client):
        """Parse output should extract test counts."""
        response = client.post(
            "/tests/parse-output", json={"output": "5 passed, 2 failed in 1.23s"}
        )
        assert response.status_code == 200

    def test_models(self, client):
        """Models endpoint should return available models."""
        response = client.get("/utils/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "default" in data

    def test_parse_log(self, client):
        """Parse log should extract metrics."""
        response = client.post(
            "/utils/parse-log", json={"line": "Agent 1: Identifying test scenarios"}
        )
        assert response.status_code == 200


class TestOpenAPIDocs:
    """Tests for API documentation."""

    def test_docs_available(self, client):
        """OpenAPI docs should be available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json(self, client):
        """OpenAPI JSON schema should be available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        # Verify all endpoint categories exist
        paths = list(data["paths"].keys())
        assert "/health" in paths
        assert "/pipeline/run" in paths
        assert "/agents/identify" in paths
        assert "/agents/implement" in paths
        assert "/agents/evaluate" in paths
        assert "/tests/run" in paths
        # Verify new endpoints exist
        assert "/agents/safety/validate" in paths
        assert "/codebase/analyze" in paths
        assert "/codebase/files" in paths
        assert "/pipeline/status/{run_id}" in paths
        assert "/tests/coverage" in paths
        assert "/prompts/history" in paths
        assert "/prompts/{run_id}" in paths
        assert "/agents/interpret-input" in paths
        assert "/tests/validate-syntax" in paths


class TestSafetyEndpoints:
    """Tests for safety validation endpoints."""

    def test_validate_safety_safe_prompt(self, client):
        """Safety validation should accept safe prompts."""
        response = client.post(
            "/agents/safety/validate",
            json={"prompt": "Write a test for the add function"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "is_safe" in data
        assert "reason" in data

    def test_validate_safety_with_model(self, client):
        """Safety validation should accept model parameter."""
        response = client.post(
            "/agents/safety/validate",
            json={
                "prompt": "Generate unit tests",
                "model": "meta-llama/llama-guard-4-12b",
            },
        )
        assert response.status_code == 200


class TestCodebaseEndpoints:
    """Tests for codebase analysis endpoints."""

    def test_analyze_codebase_invalid_path(self, client):
        """Analyze should handle invalid paths gracefully."""
        response = client.post(
            "/codebase/analyze", json={"codebase_path": "/nonexistent/path"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_list_files_invalid_path(self, client):
        """List files should handle invalid paths gracefully."""
        response = client.post("/codebase/files", json={"path": "/nonexistent/path"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_list_files_with_extensions(self, client):
        """List files should accept extension filter."""
        response = client.post(
            "/codebase/files",
            json={
                "path": "/nonexistent/path",
                "extensions": [".py", ".js"],
                "recursive": True,
            },
        )
        assert response.status_code == 200


class TestPipelineStatusEndpoints:
    """Tests for pipeline status endpoints."""

    def test_pipeline_status_unknown_id(self, client):
        """Pipeline status should handle unknown run IDs."""
        response = client.get("/pipeline/status/unknown-run-id")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["run_id"] == "unknown-run-id"
        assert "error" in data


class TestCoverageEndpoints:
    """Tests for coverage report endpoints."""

    def test_coverage_missing_file(self, client):
        """Coverage should handle missing coverage.json."""
        response = client.post(
            "/tests/coverage", json={"codebase_path": "/nonexistent/path"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_coverage_with_custom_path(self, client):
        """Coverage should accept custom coverage file path."""
        response = client.post(
            "/tests/coverage",
            json={
                "codebase_path": "/some/path",
                "coverage_json_path": "/custom/coverage.json",
            },
        )
        assert response.status_code == 200


class TestPromptsEndpoints:
    """Tests for prompts history endpoints."""

    def test_prompts_history(self, client):
        """Prompts history should return a list of runs."""
        response = client.get("/prompts/history")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "runs" in data
        assert "total" in data

    def test_prompts_by_run_unknown(self, client):
        """Prompts by run should handle unknown run IDs."""
        response = client.get("/prompts/unknown-run-id")
        assert response.status_code == 200
        data = response.json()
        # Either success with empty prompts or failure with error
        assert "success" in data


class TestInterpretInputEndpoints:
    """Tests for input interpretation endpoints."""

    def test_interpret_input_basic(self, client):
        """Interpret input should process user input."""
        response = client.post(
            "/agents/interpret-input",
            json={
                "user_input": "Add more tests for error handling",
                "scenarios": [
                    {"scenario_description": "Test login", "priority": "High"}
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data


class TestSyntaxValidationEndpoints:
    """Tests for syntax validation endpoints."""

    def test_validate_syntax_valid_code(self, client):
        """Syntax validation should accept valid Python code."""
        response = client.post(
            "/tests/validate-syntax", json={"code": "def hello():\n    return 'world'"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["is_valid"] is True
        assert data["errors"] == []

    def test_validate_syntax_invalid_code(self, client):
        """Syntax validation should detect invalid Python code."""
        response = client.post(
            "/tests/validate-syntax", json={"code": "def hello(\n    return 'world'"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0
        assert "line" in data["errors"][0]
        assert "message" in data["errors"][0]

    def test_validate_syntax_empty_code(self, client):
        """Syntax validation should handle empty code."""
        response = client.post("/tests/validate-syntax", json={"code": ""})
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
