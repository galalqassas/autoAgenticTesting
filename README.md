# Agentic Testing Pipeline

**An AI-powered automated testing pipeline that autonomously identifies test scenarios, generates PyTest scripts, and evaluates code coverage and security.**

It features a multi-agent architecture (Identification, Implementation, Evaluation), interactive dashboards, and comprehensive security analysis.

## 🚀 How to Run

### 1. GUI (Recommended)

The easiest way to use the pipeline.

```bash
python src/extension/GUI/main.py
```

### 2. CLI

Run the pipeline directly from the command line.

```bash
python src/extension/pythonTestingPipeline/scripts/pythonTestingPipeline.py <path_to_target> [options]
```

**Options:** `--auto-approve`, `--no-run-tests`

### 3. Dashboard

Visualize results, coverage, and agent conversations.

```bash
cd dashboard
pip install -r requirements.txt
python -m streamlit run app.py
```

### 4. VS Code Extension

1. `npm install` then `npm run compile`
2. Press `F5` to launch.
3. Command: `Agentic Testing: Generate Tests`

## 🛠️ Prerequisites

- **Python**: 3.10+
- **Node.js**: 18.0.0+ (for VS Code extension)
- **API Keys**: Add `OPENAI_API_KEY` or `GROQ_API_KEY` to `.env`.

## 📦 Installation

```bash
git clone <repository_url>
cd autoAgenticTesting
pip install openai pytest pytest-cov fastapi uvicorn streamlit pandas plotly
```