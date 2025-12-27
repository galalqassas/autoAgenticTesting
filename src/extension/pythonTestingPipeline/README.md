# Python Automated Testing Pipeline

A three-agent system for automated Python testing, security analysis, and coverage improvement.

## Overview

This pipeline uses three specialized AI agents to ensure code quality:

1.  **Identification Agent**: Finds test scenarios (edge cases, security, critical paths).
2.  **Implementation Agent**: Generates PyTest scripts with security awareness.
3.  **Evaluation Agent**: Runs tests, checks coverage (target 90%), and analyzes security.

**Key Features:**

- **Auto-Improvement**: Iteratively generates tests until coverage goals are met.
- **Security Analysis**: Detects SQLi, XSS, secrets, and more.
- **Robustness**: Auto-fixes syntax errors, rotates API keys, and handles rate limits.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Python Testing Pipeline                              │
├─────────────────────────────────────────────────────────────────────────┤
│   ┌──────────────────┐    JSON     ┌──────────────────┐                │
│   │   Identification │ ─────────▶ │  Human Approval  │                 │
│   │      Agent       │            │     (Review)     │                 │
│   └──────────────────┘            └────────┬─────────┘                 │
│            │                               ▼                            │
│            │                      ┌──────────────────┐                 │
│            │                      │  Implementation  │                 │
│            │                      │      Agent       │                 │
│            │                      └────────┬─────────┘                 │
│            │                               ▼                            │
│            │                      ┌──────────────────┐                 │
│            │                      │    Evaluation    │◀────────────┐   │
│            │                      │   + Security     │             │   │
│            │                      └────────┬─────────┘             │   │
│            │                               │ Coverage < 90%?       │   │
│            │                               ▼         Yes           │   │
│            │                      ┌──────────────────┐             │   │
│            │                      │  Generate More   │─────────────┘   │
│            │                      │     Tests        │                 │
│            │                      └──────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## Usage

### VS Code Integration

Use the command in Copilot Chat:

```
@workspace /generatePythonTests ./my_project
```

### CLI Usage

Run the standalone script:

```bash
# Basic usage
python pythonTestingPipeline.py ./my_project

# Common options
python pythonTestingPipeline.py ./my_project --coverage       # Measure coverage
python pythonTestingPipeline.py ./my_project --auto-approve   # Skip manual review
python pythonTestingPipeline.py ./my_project --no-run-tests   # Generate only
```

## Configuration

**Requirements:**

- Python 3.10+
- `pip install pytest pytest-cov openai matplotlib`
- VS Code + GitHub Copilot (for extension usage)

**LLM Setup:**
Configure `scripts/llm_config.py` and `scripts/.env`.

- **Keys**: `GROQ_API_KEY`, `GROQ_API_KEY_1`, etc. (auto-rotates on 429 errors).
- **Models**: Defaults to `openai/gpt-oss-120b`, falls back to `groq/compound`, `llama`, etc.

## Agents & Communication

Agents communicate via JSON.

- **Identification**: Outputs `test_scenarios` (description, priority).
- **Implementation**: Receives scenarios, outputs raw PyTest code.
- **Evaluation**: Outputs `execution_summary`, `code_coverage_percentage`, and `security_issues`.

**Security Checks:**
The pipeline flags **Critical** to **Low** severity issues including:

- SQL/Command Injection & XSS
- Path Traversal & Data Exposure
- Weak Authentication & Hardcoded Secrets

## Contributing

1.  Follow existing patterns.
2.  Add unit tests (`npm run test:unit`).
3.  Ensure TypeScript compilation passes.
