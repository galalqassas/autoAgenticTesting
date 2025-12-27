# API Documentation

REST API for the Python Testing Pipeline. All endpoints are open (no authentication required).

## Base URL

```
http://localhost:8000
```

---

## Health & Info

### GET /health

Health check.

**Response:**

```json
{ "status": "healthy", "version": "1.0.0" }
```

### GET /info

API configuration.

**Response:**

```json
{
  "version": "1.0.0",
  "available_models": ["llama-3.3-70b-versatile"],
  "default_model": "llama-3.3-70b-versatile"
}
```

---

## Pipeline

### POST /pipeline/run

Run complete testing pipeline.

**Request:**

```json
{
  "codebase_path": "/absolute/path/to/code",
  "auto_approve": true,
  "run_tests": true,
  "coverage": false,
  "model": null
}
```

**Response:**

```json
{
  "success": true,
  "scenarios_count": 12,
  "test_file": "/path/to/tests/test_generated.py",
  "execution": { "total_tests": 12, "passed": 10, "failed": 2 },
  "coverage_percent": 75.5,
  "security_issues": [],
  "recommendations": ["Add edge case tests"],
  "prompts_file": "/path/to/prompts.json",
  "error": null
}
```

### POST /pipeline/run/stream

Same as above but with SSE streaming output.

---

## Agent 1: Identification

### POST /agents/identify

Identify test scenarios from codebase.

**Request:**

```json
{
  "codebase_path": "/absolute/path/to/code",
  "model": null
}
```

**Response:**

```json
{
  "success": true,
  "scenarios": {
    "scenarios": [
      { "scenario_description": "Test user login", "priority": "High" },
      { "scenario_description": "Test input validation", "priority": "Medium" }
    ],
    "total": 2,
    "by_priority": { "High": 1, "Medium": 1 }
  },
  "error": null
}
```

### POST /agents/identify/refine

Refine scenarios with feedback.

**Request:**

```json
{
  "scenarios": [{ "scenario_description": "Test login", "priority": "High" }],
  "feedback": "Add more edge cases for invalid inputs",
  "model": null
}
```

**Response:** Same format as `/agents/identify`

---

## Agent 2: Implementation

### POST /agents/implement

Generate test code from scenarios.

**Request:**

```json
{
  "scenarios": [{ "scenario_description": "Test login", "priority": "High" }],
  "codebase_path": "/path/to/code",
  "output_dir": "/path/to/tests",
  "model": null
}
```

**Response:**

```json
{
  "success": true,
  "test_file": "/path/to/tests/test_generated.py",
  "test_code": "import pytest\n\ndef test_login():\n    ...",
  "error": null
}
```

### POST /agents/implement/improve

Improve tests for better coverage.

**Request:**

```json
{
  "codebase_path": "/path/to/code",
  "existing_test_file": "/path/to/test.py",
  "coverage_percentage": 60.0,
  "uncovered_areas": "login.py lines 45-60",
  "syntax_errors": "",
  "security_issues": [],
  "model": null
}
```

**Response:**

```json
{
  "success": true,
  "test_code": "# Improved test code...",
  "error": null
}
```

### POST /agents/implement/fix-syntax

Fix syntax errors in test code.

**Request:**

```json
{
  "code": "def test():\n  return",
  "error_msg": "IndentationError: expected an indented block",
  "codebase_path": "/path/to/code",
  "model": null
}
```

**Response:**

```json
{
  "success": true,
  "fixed_code": "def test():\n    return",
  "error": null
}
```

---

## Agent 3: Evaluation

### POST /agents/evaluate

Evaluate test results and security.

**Request:**

```json
{
  "test_results": { "passed": 8, "failed": 2, "output": "..." },
  "scenarios": [{ "scenario_description": "Test login", "priority": "High" }],
  "codebase_path": "/path/to/code",
  "model": null
}
```

**Response:**

```json
{
  "success": true,
  "evaluation": {
    "execution_summary": { "total_tests": 10, "passed": 8, "failed": 2 },
    "code_coverage_percentage": 72.5,
    "actionable_recommendations": ["Add error handling tests"],
    "security_issues": [
      {
        "severity": "medium",
        "issue": "SQL injection vulnerability",
        "location": "db.py:45",
        "recommendation": "Use parameterized queries"
      }
    ],
    "has_severe_security_issues": false
  },
  "error": null
}
```

---

## Test Execution

### POST /tests/run

Run tests with coverage.

**Request:**

```json
{
  "test_file": "/path/to/test.py",
  "codebase_path": "/path/to/code"
}
```

**Response:**

```json
{
  "success": true,
  "total": 10,
  "passed": 8,
  "failed": 2,
  "coverage_percent": 75.0,
  "output": "===== 8 passed, 2 failed =====",
  "error": null
}
```

### POST /tests/parse-output

Parse pytest output to structured data.

**Request:**

```json
{ "output": "10 passed, 2 failed in 1.5s" }
```

**Response:**

```json
{ "total": 12, "passed": 10, "failed": 2 }
```

---

## Utilities

### POST /utils/extract-dependencies

Extract package dependencies from code.

**Request:**

```json
{ "test_code": "import pytest\nimport requests\n..." }
```

**Response:**

```json
{ "packages": ["pytest", "requests"] }
```

### POST /utils/install-dependencies

Install packages.

**Request:**

```json
{ "packages": ["pytest", "requests"], "cwd": "/path/to/project" }
```

**Response:**

```json
{ "success": true, "installed": ["pytest", "requests"], "failed": [] }
```

### POST /utils/parse-log

Parse pipeline log line for metrics.

**Request:**

```json
{ "line": "Agent 1: Identifying test scenarios" }
```

**Response:**

```json
{
  "phase_update": ["identify", "active"],
  "coverage": null,
  "tests": null,
  "scenarios": null,
  "security_issues": null,
  "agent_activation": 1
}
```

### GET /utils/models

List available LLM models.

**Response:**

```json
{
  "models": ["llama-3.3-70b-versatile"],
  "default": "llama-3.3-70b-versatile"
}
```

---

## Error Responses

All endpoints may return:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```
