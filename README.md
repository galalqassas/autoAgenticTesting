# Agentic Testing Pipeline

AI-powered automated Python testing pipeline.

**Input**: A Python codebase path (e.g., `./my_project`).
**Output**: A comprehensive, executable PyTest suite (aiming for 90%+ coverage) and a security analysis report.

## Overview

Three specialized AI agents work in sequence:

1.  **Identification Agent**: Finds test scenarios (edge cases, security, critical paths).
2.  **Implementation Agent**: Generates PyTest scripts.
3.  **Evaluation Agent**: Runs tests, checks coverage, and analyzes security.

## Usage

### CLI

Run the standalone Python script:

```bash
python src/extension/pythonTestingPipeline/scripts/pythonTestingPipeline.py <path_to_codebase>
```

Options: `--coverage`, `--auto-approve`, `--no-run-tests`

### VS Code Extension

Run the command **"Agentic Testing: Generate Tests"** from the Command Palette.

### Development

```bash
npm install
npm run compile
# Open in VS Code, then press F5 to run the extension

```

## Configuration

Set API keys in `.env` (supports OpenAI, Groq).

## Getting Started

```bash
# Clone or initialize the repository
git clone <repository_url>
# or
git init

# Install dependencies
npm install

# Set up API keys
cp .env.example .env  # Create .env from example
# Edit .env and add your API keys
```
