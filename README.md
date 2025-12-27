# Agentic Testing Pipeline

**An AI-powered automated testing pipeline that autonomously identifies test scenarios, generates PyTest scripts, and evaluates code coverage and security.**

It features a multi-agent architecture (Identification, Implementation, Evaluation), interactive GUI, and comprehensive security analysis.

## 🚀 How to Run

Follow the **Prerequisites** first then choose one of the following:

### 1. GUI (Recommended)

The easiest way to use the pipeline.

```bash
python src/extension/GUI/main.py
```

### 2. API Service

Expose the pipeline as a REST service with 25+ endpoints.

```bash
# Run server (Recommended method)
python -m uvicorn src.extension.api.main:app --port 8000

# View Documentation
# Open http://localhost:8000/ (Redirects to /docs)
```

#### Example Request:

```bash
curl -X POST http://localhost:8000/agents/identify \
  -H "Content-Type: application/json" \
  -d '{"codebase_path": "/absolute/path/to/code"}'
```

### 3. CLI

Run directly from the command line.

```bash
python src/extension/pythonTestingPipeline/scripts/pythonTestingPipeline.py <path_to_target> [options]
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
git clone https://github.com/galalqassas/autoAgenticTesting.git
cd autoAgenticTesting

# Create virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Or install manually
pip install groq pytest pytest-cov fastapi uvicorn matplotlib customtkinter python-dotenv
```

### API Keys Setup

1. Copy `.env.example` to `.env`.
2. Add your API keys to the `.env` file.

```bash
cp .env.example .env
```

**Note**: The `.env` file **must** be present in `src/extension/pythonTestingPipeline/scripts/` for the Python pipeline to function correctly, as the configuration loader looks for it there. Placing it in the root is recommended for consistency and other tools.
