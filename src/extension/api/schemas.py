"""API schemas."""

from pydantic import BaseModel
from typing import Optional
from enum import Enum


class Priority(str, Enum):
    high = "High"
    medium = "Medium"
    low = "Low"


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


# Common
class HealthResponse(BaseModel):
    status: str
    version: str


class InfoResponse(BaseModel):
    version: str
    available_models: list[str]
    default_model: str


class TestScenario(BaseModel):
    scenario_description: str
    priority: Priority


class ScenariosOutput(BaseModel):
    scenarios: list[TestScenario]
    total: int
    by_priority: dict[str, int] = {}


class SecurityIssue(BaseModel):
    severity: Severity
    issue: str
    location: str
    recommendation: str


class ExecutionSummary(BaseModel):
    total_tests: int
    passed: int
    failed: int


class EvaluationOutput(BaseModel):
    execution_summary: ExecutionSummary
    code_coverage_percentage: float
    actionable_recommendations: list[str] = []
    security_issues: list[SecurityIssue] = []
    has_severe_security_issues: bool = False


# Pipeline
class PipelineRequest(BaseModel):
    codebase_path: str
    auto_approve: bool = True
    run_tests: bool = True
    coverage: bool = False
    model: Optional[str] = None


class PipelineResponse(BaseModel):
    success: bool
    scenarios_count: int = 0
    test_file: Optional[str] = None
    execution: Optional[ExecutionSummary] = None
    coverage_percent: Optional[float] = None
    security_issues: list[SecurityIssue] = []
    recommendations: list[str] = []
    prompts_file: Optional[str] = None
    error: Optional[str] = None


# Identification
class IdentifyRequest(BaseModel):
    codebase_path: str
    model: Optional[str] = None


class IdentifyResponse(BaseModel):
    success: bool
    scenarios: Optional[ScenariosOutput] = None
    error: Optional[str] = None


class RefineRequest(BaseModel):
    scenarios: list[TestScenario]
    feedback: str
    model: Optional[str] = None


RefineResponse = IdentifyResponse  # Same structure


# Implementation
class ImplementRequest(BaseModel):
    scenarios: list[TestScenario]
    codebase_path: str
    output_dir: Optional[str] = None
    model: Optional[str] = None


class ImplementResponse(BaseModel):
    success: bool
    test_file: Optional[str] = None
    test_code: Optional[str] = None
    error: Optional[str] = None


class ImproveRequest(BaseModel):
    codebase_path: str
    existing_test_file: str
    coverage_percentage: float
    uncovered_areas: str
    syntax_errors: str = ""
    security_issues: list[SecurityIssue] = []
    model: Optional[str] = None


class ImproveResponse(BaseModel):
    success: bool
    test_code: Optional[str] = None
    error: Optional[str] = None


class FixSyntaxRequest(BaseModel):
    code: str
    error_msg: str
    codebase_path: str
    model: Optional[str] = None


FixSyntaxResponse = ImproveResponse  # Same structure


# Evaluation
class EvaluateRequest(BaseModel):
    test_results: dict
    scenarios: list[TestScenario]
    codebase_path: str
    model: Optional[str] = None


class EvaluateResponse(BaseModel):
    success: bool
    evaluation: Optional[EvaluationOutput] = None
    error: Optional[str] = None


# Tests
class TestRunRequest(BaseModel):
    test_file: str
    codebase_path: str


class TestRunResponse(BaseModel):
    success: bool
    total: int = 0
    passed: int = 0
    failed: int = 0
    coverage_percent: Optional[float] = None
    output: str = ""
    error: Optional[str] = None


class ParseOutputRequest(BaseModel):
    output: str


class ParseOutputResponse(BaseModel):
    total: int
    passed: int
    failed: int


# Utilities
class ExtractDepsRequest(BaseModel):
    test_code: str


class ExtractDepsResponse(BaseModel):
    packages: list[str]


class InstallDepsRequest(BaseModel):
    packages: list[str]
    cwd: str


class InstallDepsResponse(BaseModel):
    success: bool
    installed: list[str] = []
    failed: list[str] = []


class ParseLogRequest(BaseModel):
    line: str


class ParseLogResponse(BaseModel):
    phase_update: Optional[tuple[str, str]] = None
    coverage: Optional[str] = None
    tests: Optional[tuple[str, str, int]] = None
    scenarios: Optional[str] = None
    security_issues: Optional[str] = None
    agent_activation: Optional[int] = None


class ModelsResponse(BaseModel):
    models: list[str]
    default: str


# Safety Validation
class SafetyValidateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None


class SafetyValidateResponse(BaseModel):
    success: bool
    is_safe: bool = True
    reason: str = ""
    error: Optional[str] = None


# Codebase Analysis
class CodebaseAnalyzeRequest(BaseModel):
    codebase_path: str
    include_hidden: bool = False


class FileInfo(BaseModel):
    path: str
    size: int
    lines: int = 0


class CodebaseAnalyzeResponse(BaseModel):
    success: bool
    files: list[FileInfo] = []
    total_files: int = 0
    total_lines: int = 0
    by_extension: dict[str, int] = {}
    error: Optional[str] = None


class ListFilesRequest(BaseModel):
    path: str
    extensions: list[str] = [".py"]
    recursive: bool = True


class ListFilesResponse(BaseModel):
    success: bool
    files: list[str] = []
    total: int = 0
    error: Optional[str] = None


# Pipeline Status
class PipelineStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class PipelineStatusResponse(BaseModel):
    success: bool
    run_id: str
    status: PipelineStatus = PipelineStatus.pending
    progress: int = 0
    result: Optional[PipelineResponse] = None
    error: Optional[str] = None


# Coverage Report
class CoverageRequest(BaseModel):
    codebase_path: str
    coverage_json_path: Optional[str] = None


class FileCoverage(BaseModel):
    path: str
    covered_lines: int
    total_lines: int
    percent: float


class CoverageResponse(BaseModel):
    success: bool
    total_percent: float = 0.0
    files: list[FileCoverage] = []
    error: Optional[str] = None


# Prompts History
class PromptEntry(BaseModel):
    agent: str
    system_prompt: str
    user_prompt: str
    response: str
    timestamp: Optional[str] = None


class PromptsRunInfo(BaseModel):
    run_id: str
    timestamp: str
    file_path: str


class PromptsHistoryResponse(BaseModel):
    success: bool
    runs: list[PromptsRunInfo] = []
    total: int = 0
    error: Optional[str] = None


class PromptsRunResponse(BaseModel):
    success: bool
    run_id: str = ""
    prompts: list[PromptEntry] = []
    error: Optional[str] = None


# Input Interpretation
class InterpretInputRequest(BaseModel):
    user_input: str
    scenarios: list[TestScenario]
    model: Optional[str] = None


class InterpretInputResponse(BaseModel):
    success: bool
    action: str = ""
    feedback: Optional[str] = None
    error: Optional[str] = None


# Syntax Validation
class ValidateSyntaxRequest(BaseModel):
    code: str


class SyntaxError(BaseModel):
    line: int
    column: int
    message: str


class ValidateSyntaxResponse(BaseModel):
    success: bool
    is_valid: bool = True
    errors: list[SyntaxError] = []
