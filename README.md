# Agentic Testing Pipeline

**An AI-powered automated testing pipeline that autonomously identifies test scenarios, generates PyTest scripts, and evaluates code coverage and security.**

It features a multi-agent architecture (Identification, Implementation, Evaluation), interactive GUI, and comprehensive security analysis.

## 🚀 How to Run

## Follow the prerequisits first then the follwing 3 steps

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

### 3. VS Code Extension

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

#creat virtual enviroment
python -m venv venv

#Activate the virtual enviroment
.\venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Or install manually
pip install openai groq pytest pytest-cov fastapi uvicorn streamlit pandas plotly matplotlib customtkinter python-dotenv
```

### API Keys Setup

Create a `.env` file in the project root and in `src/extension/pythonTestingPipeline/scripts/`:

```env
# Primary API key
GROQ_API_KEY=your_groq_key_here

# Or use OpenAI
OPENAI_API_KEY=your_openai_key_here

# Additional API keys (optional, for fallback)
GROQ_API_KEY_1=your_second_key
GROQ_API_KEY_2=your_third_key
```
