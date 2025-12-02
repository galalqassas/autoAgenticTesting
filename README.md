# Agentic Testing Pipeline

An AI-powered automated testing pipeline that autonomously identifies test scenarios, generates PyTest scripts, and evaluates code coverage and security.

## 🚀 Features

- **🤖 Multi-Agent Architecture**:
  - **Identification Agent**: Analyzes code to find critical paths, edge cases, and security risks.
  - **Implementation Agent**: Generates executable, high-quality PyTest scripts.
  - **Evaluation Agent**: Runs tests, measures coverage, and performs security analysis.
- **📊 Interactive Dashboard**: Visualize pipeline metrics, code coverage, and agent conversations.
- **🛡️ Security Analysis**: Identifies vulnerabilities like SQL injection, XSS, and more.
- **📈 Automated Reporting**: Generates detailed JSON reports and visualization data.

## 🛠️ Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18.0.0 or higher (for VS Code extension)
- **API Keys**: OpenAI or Groq API key

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd autoAgenticTesting
    ```

2.  **Install Python Dependencies**:
    ```bash
    pip install openai pytest pytest-cov fastapi uvicorn streamlit pandas plotly
    ```

3.  **Set up Environment Variables**:
    Create a `.env` file in `src/extension/pythonTestingPipeline/scripts/` (or root) with your API keys:
    ```ini
    OPENAI_API_KEY=your_openai_key_here
    # or
    GROQ_API_KEY=your_groq_key_here
    ```

## 🏃 Usage

### 1. Running the Testing Pipeline

Run the standalone Python script to test a target codebase:

```bash
python src/extension/pythonTestingPipeline/scripts/pythonTestingPipeline.py <path_to_target_codebase> [options]
```

**Options:**
- `--coverage`: Enable code coverage measurement.
- `--auto-approve`: Automatically proceed without user confirmation.
- `--no-run-tests`: Generate tests but do not execute them.

**Example:**
```bash
python src/extension/pythonTestingPipeline/scripts/pythonTestingPipeline.py apps/web_timer --coverage --auto-approve
```

### 2. Launching the Dashboard

Visualize the results, coverage, and agent history:

```bash
cd dashboard
pip install -r requirements.txt  # Ensure dashboard deps are installed
python -m streamlit run app.py
```

The dashboard will open at `http://localhost:8501`.

### 3. VS Code Extension

1.  Install dependencies: `npm install`
2.  Compile: `npm run compile`
3.  Run: Open in VS Code and press `F5` to launch the extension host.
4.  Command: `Agentic Testing: Generate Tests`

## 📂 Project Structure

- **`apps/`**: Example applications used for testing (e.g., `web_timer`).
- **`dashboard/`**: Streamlit application for visualizing results.
- **`src/extension/pythonTestingPipeline/scripts/`**: Core Python scripts for the agentic pipeline.
- **`src/`**: TypeScript source code for the VS Code extension.

For more information, please refer to the [Mini Paper](https://docs.google.com/document/d/1ri4d37M5Gi8h9ROnLbFPA4R8Abg7bfyj_fnCvEmfjX4/edit?tab=t.0).