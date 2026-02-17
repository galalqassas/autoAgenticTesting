"""Python Testing Pipeline API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse

from . import services
from .schemas import (
    CodebaseAnalyzeRequest,
    CodebaseAnalyzeResponse,
    CoverageRequest,
    CoverageResponse,
    EvaluateRequest,
    EvaluateResponse,
    ExtractDepsRequest,
    ExtractDepsResponse,
    FixSyntaxRequest,
    HealthResponse,
    IdentifyRequest,
    IdentifyResponse,
    ImplementRequest,
    ImplementResponse,
    ImproveRequest,
    ImproveResponse,
    InfoResponse,
    InstallDepsRequest,
    InstallDepsResponse,
    InterpretInputRequest,
    InterpretInputResponse,
    ListFilesRequest,
    ListFilesResponse,
    ModelsResponse,
    ParseLogRequest,
    ParseLogResponse,
    ParseOutputRequest,
    ParseOutputResponse,
    PipelineRequest,
    PipelineResponse,
    PipelineStatusResponse,
    PromptsHistoryResponse,
    PromptsRunResponse,
    RefineRequest,
    SafetyValidateRequest,
    SafetyValidateResponse,
    TestRunRequest,
    TestRunResponse,
    ValidateSyntaxRequest,
    ValidateSyntaxResponse,
)

app = FastAPI(
    title="Python Testing Pipeline API",
    description="REST API for automated test generation",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


# Root redirect to docs
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


# Health
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/info", response_model=InfoResponse, tags=["Health"])
async def info():
    return services.get_info()


# Pipeline
@app.post("/pipeline/run", response_model=PipelineResponse, tags=["Pipeline"])
async def pipeline_run(req: PipelineRequest):
    return services.run_pipeline(req)


@app.post("/pipeline/run/stream", tags=["Pipeline"])
async def pipeline_run_stream(req: PipelineRequest):
    return StreamingResponse(
        services.run_pipeline_stream(req), media_type="text/event-stream"
    )


# Identification
@app.post("/agents/identify", response_model=IdentifyResponse, tags=["Agents"])
async def identify(req: IdentifyRequest):
    return services.identify_scenarios(req)


@app.post("/agents/identify/refine", response_model=IdentifyResponse, tags=["Agents"])
async def refine(req: RefineRequest):
    return services.refine_scenarios(req)


# Implementation
@app.post("/agents/implement", response_model=ImplementResponse, tags=["Agents"])
async def implement(req: ImplementRequest):
    return services.implement_tests(req)


@app.post("/agents/implement/improve", response_model=ImproveResponse, tags=["Agents"])
async def improve(req: ImproveRequest):
    return services.improve_tests(req)


@app.post(
    "/agents/implement/fix-syntax", response_model=ImproveResponse, tags=["Agents"]
)
async def fix_syntax(req: FixSyntaxRequest):
    return services.fix_syntax(req)


# Evaluation
@app.post("/agents/evaluate", response_model=EvaluateResponse, tags=["Agents"])
async def evaluate(req: EvaluateRequest):
    return services.evaluate_results(req)


# Tests
@app.post("/tests/run", response_model=TestRunResponse, tags=["Tests"])
async def tests_run(req: TestRunRequest):
    return services.run_tests(req)


@app.post("/tests/parse-output", response_model=ParseOutputResponse, tags=["Tests"])
async def parse_test_output(req: ParseOutputRequest):
    return services.parse_output(req)


# Utilities
@app.post(
    "/utils/extract-dependencies",
    response_model=ExtractDepsResponse,
    tags=["Utilities"],
)
async def extract_deps(req: ExtractDepsRequest):
    return services.extract_dependencies(req)


@app.post(
    "/utils/install-dependencies",
    response_model=InstallDepsResponse,
    tags=["Utilities"],
)
async def install_deps(req: InstallDepsRequest):
    return services.install_dependencies(req)


@app.post("/utils/parse-log", response_model=ParseLogResponse, tags=["Utilities"])
async def parse_log(req: ParseLogRequest):
    return services.parse_log(req)


@app.get("/utils/models", response_model=ModelsResponse, tags=["Utilities"])
async def get_models():
    return services.get_models()


# Safety Validation (High Priority)
@app.post(
    "/agents/safety/validate", response_model=SafetyValidateResponse, tags=["Agents"]
)
async def validate_safety(req: SafetyValidateRequest):
    """Validate prompt safety using Llama Guard models."""
    return services.validate_safety(req)


# Codebase Analysis (High Priority)
@app.post(
    "/codebase/analyze", response_model=CodebaseAnalyzeResponse, tags=["Codebase"]
)
async def analyze_codebase(req: CodebaseAnalyzeRequest):
    """Analyze codebase structure including file counts and line counts."""
    return services.analyze_codebase(req)


@app.post("/codebase/files", response_model=ListFilesResponse, tags=["Codebase"])
async def list_files(req: ListFilesRequest):
    """List code files in a directory with optional extension filtering."""
    return services.list_codebase_files(req)


# Pipeline Status (High Priority)
@app.get(
    "/pipeline/status/{run_id}",
    response_model=PipelineStatusResponse,
    tags=["Pipeline"],
)
async def pipeline_status(run_id: str):
    """Get the status of a pipeline run by ID."""
    return services.get_pipeline_status(run_id)


# Coverage Report (High Priority)
@app.post("/tests/coverage", response_model=CoverageResponse, tags=["Tests"])
async def get_coverage(req: CoverageRequest):
    """Get coverage report from coverage.json file."""
    return services.get_coverage_report(req)


# Prompts History (Medium Priority)
@app.get("/prompts/history", response_model=PromptsHistoryResponse, tags=["Prompts"])
async def prompts_history():
    """Get list of saved prompt history runs."""
    return services.get_prompts_history()


@app.get("/prompts/{run_id}", response_model=PromptsRunResponse, tags=["Prompts"])
async def prompts_by_run(run_id: str):
    """Get prompts for a specific pipeline run."""
    return services.get_prompts_by_run(run_id)


# Input Interpretation (Medium Priority)
@app.post(
    "/agents/interpret-input", response_model=InterpretInputResponse, tags=["Agents"]
)
async def interpret_input(req: InterpretInputRequest):
    """Interpret natural language user input for scenario management."""
    return services.interpret_input(req)


# Syntax Validation (Medium Priority)
@app.post(
    "/tests/validate-syntax", response_model=ValidateSyntaxResponse, tags=["Tests"]
)
async def validate_syntax(req: ValidateSyntaxRequest):
    """Validate Python code syntax without executing."""
    return services.validate_syntax(req)
