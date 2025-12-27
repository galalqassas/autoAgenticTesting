"""Service layer - wraps pipeline components."""

import ast
import json
import sys
from pathlib import Path
from typing import Generator
from dataclasses import asdict

from .schemas import (
    InfoResponse,
    PipelineRequest,
    PipelineResponse,
    IdentifyRequest,
    IdentifyResponse,
    RefineRequest,
    ImplementRequest,
    ImplementResponse,
    ImproveRequest,
    ImproveResponse,
    FixSyntaxRequest,
    EvaluateRequest,
    EvaluateResponse,
    TestRunRequest,
    TestRunResponse,
    ParseOutputRequest,
    ParseOutputResponse,
    ExtractDepsRequest,
    ExtractDepsResponse,
    InstallDepsRequest,
    InstallDepsResponse,
    ParseLogRequest,
    ParseLogResponse,
    ModelsResponse,
    TestScenario,
    ScenariosOutput,
    SecurityIssue,
    ExecutionSummary,
    EvaluationOutput,
    SafetyValidateRequest,
    SafetyValidateResponse,
    CodebaseAnalyzeRequest,
    CodebaseAnalyzeResponse,
    FileInfo,
    ListFilesRequest,
    ListFilesResponse,
    PipelineStatus,
    PipelineStatusResponse,
    CoverageRequest,
    CoverageResponse,
    FileCoverage,
    PromptsHistoryResponse,
    PromptsRunInfo,
    PromptsRunResponse,
    PromptEntry,
    InterpretInputRequest,
    InterpretInputResponse,
    ValidateSyntaxRequest,
    ValidateSyntaxResponse,
    SyntaxError as SyntaxErrorSchema,
)

# Add pipeline to path
_SCRIPTS = Path(__file__).parent.parent / "pythonTestingPipeline" / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

# Lazy imports
_cache = {}


def _get(key, loader):
    if key not in _cache:
        _cache[key] = loader()
    return _cache[key]


def _pipeline():
    return _get(
        "pipeline", lambda: __import__("pythonTestingPipeline").PythonTestingPipeline
    )


def _agents():
    from pipeline.agents import (
        IdentificationAgent,
        ImplementationAgent,
        EvaluationAgent,
    )

    return _get(
        "agents", lambda: (IdentificationAgent, ImplementationAgent, EvaluationAgent)
    )


def _runner():
    from pipeline import test_runner

    return _get("runner", lambda: test_runner)


def _parser():
    from src.extension.GUI.log_parser import LogParser

    return _get("parser", lambda: LogParser())


def _to_internal(scenarios):
    from pipeline.models import TestScenario as TS, TestScenariosOutput as TSO

    return TSO(
        test_scenarios=[
            TS(scenario_description=s.scenario_description, priority=s.priority)
            for s in scenarios
        ]
    )


def _to_output(scenarios):
    items = [
        TestScenario(scenario_description=s.scenario_description, priority=s.priority)
        for s in scenarios
    ]
    by_priority = {}
    for s in items:
        by_priority[s.priority] = by_priority.get(s.priority, 0) + 1
    return ScenariosOutput(scenarios=items, total=len(items), by_priority=by_priority)


# Info
def get_info() -> InfoResponse:
    try:
        from llm_config import AVAILABLE_MODELS, DEFAULT_MODEL

        return InfoResponse(
            version="1.0.0",
            available_models=AVAILABLE_MODELS,
            default_model=DEFAULT_MODEL,
        )
    except ImportError:
        return InfoResponse(
            version="1.0.0",
            available_models=["llama-3.3-70b-versatile"],
            default_model="llama-3.3-70b-versatile",
        )


# Pipeline
def run_pipeline(req: PipelineRequest) -> PipelineResponse:
    try:
        result = _pipeline()(model=req.model).run_pipeline(
            codebase_path=Path(req.codebase_path),
            should_run_tests=req.run_tests,
            coverage=req.coverage,
            auto_approve=req.auto_approve,
        )
        ev = result.get("evaluation")
        return PipelineResponse(
            success=True,
            scenarios_count=len(result.get("scenarios", {}).get("test_scenarios", [])),
            test_file=str(result.get("test_file")) if result.get("test_file") else None,
            execution=ExecutionSummary(**ev.get("execution_summary", {}))
            if ev
            else None,
            coverage_percent=ev.get("code_coverage_percentage") if ev else None,
            security_issues=[SecurityIssue(**i) for i in ev.get("security_issues", [])]
            if ev
            else [],
            recommendations=ev.get("actionable_recommendations", []) if ev else [],
            prompts_file=result.get("prompts_file"),
        )
    except Exception as e:
        return PipelineResponse(success=False, error=str(e))


def run_pipeline_stream(req: PipelineRequest) -> Generator[str, None, None]:
    yield f"data: Starting pipeline for {req.codebase_path}\n\n"
    try:
        yield f"data: {run_pipeline(req).model_dump_json()}\n\n"
    except Exception as e:
        yield f"data: Error: {e}\n\n"


# Identification
def identify_scenarios(req: IdentifyRequest) -> IdentifyResponse:
    try:
        result = _agents()[0]().run(Path(req.codebase_path))
        return IdentifyResponse(
            success=True, scenarios=_to_output(result.test_scenarios)
        )
    except Exception as e:
        return IdentifyResponse(success=False, error=str(e))


def refine_scenarios(req: RefineRequest) -> IdentifyResponse:
    try:
        result = _pipeline()(model=req.model).refine_scenarios(
            _to_internal(req.scenarios), req.feedback
        )
        return IdentifyResponse(
            success=True, scenarios=_to_output(result.test_scenarios)
        )
    except Exception as e:
        return IdentifyResponse(success=False, error=str(e))


# Implementation
def implement_tests(req: ImplementRequest) -> ImplementResponse:
    try:
        output_dir = (
            Path(req.output_dir)
            if req.output_dir
            else Path(req.codebase_path) / "tests"
        )
        test_file = _agents()[1]().run(
            _to_internal(req.scenarios), Path(req.codebase_path), output_dir
        )
        return ImplementResponse(
            success=True,
            test_file=str(test_file),
            test_code=test_file.read_text() if test_file.exists() else None,
        )
    except Exception as e:
        return ImplementResponse(success=False, error=str(e))


def improve_tests(req: ImproveRequest) -> ImproveResponse:
    try:
        security = [
            asdict(SecurityIssue(**s.model_dump())) for s in req.security_issues
        ]
        code = _agents()[1]().improve_tests(
            codebase_path=Path(req.codebase_path),
            existing_test_file=Path(req.existing_test_file),
            coverage_percentage=req.coverage_percentage,
            uncovered_areas=req.uncovered_areas,
            syntax_errors=req.syntax_errors,
            security_issues=security or None,
        )
        return ImproveResponse(success=True, test_code=code)
    except Exception as e:
        return ImproveResponse(success=False, error=str(e))


def fix_syntax(req: FixSyntaxRequest) -> ImproveResponse:
    try:
        fixed = _agents()[1]().fix_syntax_errors(
            req.code, req.error_msg, Path(req.codebase_path)
        )
        return ImproveResponse(success=True, test_code=fixed)
    except Exception as e:
        return ImproveResponse(success=False, error=str(e))


# Evaluation
def evaluate_results(req: EvaluateRequest) -> EvaluateResponse:
    try:
        result = _agents()[2]().run(
            req.test_results, _to_internal(req.scenarios), Path(req.codebase_path)
        )
        return EvaluateResponse(
            success=True,
            evaluation=EvaluationOutput(
                execution_summary=ExecutionSummary(**asdict(result.execution_summary)),
                code_coverage_percentage=result.code_coverage_percentage,
                actionable_recommendations=result.actionable_recommendations,
                security_issues=[
                    SecurityIssue(**asdict(i)) for i in result.security_issues
                ],
                has_severe_security_issues=result.has_severe_security_issues,
            ),
        )
    except Exception as e:
        return EvaluateResponse(success=False, error=str(e))


# Tests
def run_tests(req: TestRunRequest) -> TestRunResponse:
    try:
        result = _runner().run_tests(Path(req.test_file), Path(req.codebase_path))
        parsed = _runner().parse_pytest_output(result.get("output", ""))
        return TestRunResponse(
            success=parsed.get("failed", 0) == 0,
            total=parsed.get("total", 0),
            passed=parsed.get("passed", 0),
            failed=parsed.get("failed", 0),
            coverage_percent=result.get("coverage"),
            output=result.get("output", ""),
        )
    except Exception as e:
        return TestRunResponse(success=False, error=str(e))


def parse_output(req: ParseOutputRequest) -> ParseOutputResponse:
    parsed = _runner().parse_pytest_output(req.output)
    return ParseOutputResponse(
        total=parsed.get("total", 0),
        passed=parsed.get("passed", 0),
        failed=parsed.get("failed", 0),
    )


# Utilities
def extract_dependencies(req: ExtractDepsRequest) -> ExtractDepsResponse:
    return ExtractDepsResponse(packages=_runner().extract_dependencies(req.test_code))


def install_dependencies(req: InstallDepsRequest) -> InstallDepsResponse:
    try:
        _runner().install_dependencies(req.packages, Path(req.cwd))
        return InstallDepsResponse(success=True, installed=req.packages)
    except Exception:
        return InstallDepsResponse(success=False, failed=req.packages)


def parse_log(req: ParseLogRequest) -> ParseLogResponse:
    r = _parser().parse(req.line)
    return ParseLogResponse(
        phase_update=r.phase_update,
        coverage=r.coverage,
        tests=r.tests,
        scenarios=r.scenarios,
        security_issues=r.security_issues,
        agent_activation=r.agent_activation,
    )


def get_models() -> ModelsResponse:
    try:
        from llm_config import AVAILABLE_MODELS, DEFAULT_MODEL

        return ModelsResponse(models=AVAILABLE_MODELS, default=DEFAULT_MODEL)
    except ImportError:
        return ModelsResponse(
            models=["llama-3.3-70b-versatile"], default="llama-3.3-70b-versatile"
        )


# Pipeline status tracking (in-memory store)
_pipeline_runs: dict[str, dict] = {}


# Safety Validation
def validate_safety(req: SafetyValidateRequest) -> SafetyValidateResponse:
    try:
        from prompt_safety import PromptSafetyChecker

        checker = (
            PromptSafetyChecker(model=req.model) if req.model else PromptSafetyChecker()
        )
        is_safe, reason = checker.check(req.prompt)
        return SafetyValidateResponse(success=True, is_safe=is_safe, reason=reason)
    except Exception as e:
        return SafetyValidateResponse(
            success=False, is_safe=True, reason="error", error=str(e)
        )


# Codebase Analysis
def analyze_codebase(req: CodebaseAnalyzeRequest) -> CodebaseAnalyzeResponse:
    try:
        codebase = Path(req.codebase_path)
        if not codebase.exists():
            return CodebaseAnalyzeResponse(success=False, error="Path does not exist")

        files = []
        by_extension: dict[str, int] = {}
        total_lines = 0

        for f in codebase.rglob("*"):
            if f.is_file():
                # Skip hidden files unless requested
                if not req.include_hidden and any(p.startswith(".") for p in f.parts):
                    continue
                # Skip common non-code directories
                if any(
                    d in f.parts
                    for d in ["__pycache__", "node_modules", ".git", "venv", ".venv"]
                ):
                    continue

                ext = f.suffix.lower()
                by_extension[ext] = by_extension.get(ext, 0) + 1

                lines = 0
                try:
                    lines = len(
                        f.read_text(encoding="utf-8", errors="ignore").splitlines()
                    )
                except Exception:
                    pass

                total_lines += lines
                files.append(
                    FileInfo(
                        path=str(f.relative_to(codebase)),
                        size=f.stat().st_size,
                        lines=lines,
                    )
                )

        return CodebaseAnalyzeResponse(
            success=True,
            files=files,
            total_files=len(files),
            total_lines=total_lines,
            by_extension=by_extension,
        )
    except Exception as e:
        return CodebaseAnalyzeResponse(success=False, error=str(e))


def list_codebase_files(req: ListFilesRequest) -> ListFilesResponse:
    try:
        path = Path(req.path)
        if not path.exists():
            return ListFilesResponse(success=False, error="Path does not exist")

        files = []
        pattern = "**/*" if req.recursive else "*"

        for f in path.glob(pattern):
            if f.is_file() and f.suffix.lower() in req.extensions:
                # Skip common non-code directories
                if any(
                    d in f.parts
                    for d in ["__pycache__", "node_modules", ".git", "venv", ".venv"]
                ):
                    continue
                files.append(str(f.relative_to(path)))

        return ListFilesResponse(success=True, files=sorted(files), total=len(files))
    except Exception as e:
        return ListFilesResponse(success=False, error=str(e))


# Pipeline Status
def get_pipeline_status(run_id: str) -> PipelineStatusResponse:
    if run_id not in _pipeline_runs:
        return PipelineStatusResponse(
            success=False,
            run_id=run_id,
            status=PipelineStatus.pending,
            error="Run ID not found",
        )

    run = _pipeline_runs[run_id]
    return PipelineStatusResponse(
        success=True,
        run_id=run_id,
        status=run.get("status", PipelineStatus.pending),
        progress=run.get("progress", 0),
        result=run.get("result"),
    )


def update_pipeline_status(
    run_id: str,
    status: PipelineStatus,
    progress: int = 0,
    result: PipelineResponse = None,
):
    """Internal function to update pipeline status."""
    _pipeline_runs[run_id] = {"status": status, "progress": progress, "result": result}


# Coverage Report
def get_coverage_report(req: CoverageRequest) -> CoverageResponse:
    try:
        codebase = Path(req.codebase_path)
        coverage_path = (
            Path(req.coverage_json_path)
            if req.coverage_json_path
            else codebase / "coverage.json"
        )

        if not coverage_path.exists():
            return CoverageResponse(success=False, error="Coverage file not found")

        data = json.loads(coverage_path.read_text())
        files = []
        total_covered = 0
        total_statements = 0

        for file_path, file_data in data.get("files", {}).items():
            summary = file_data.get("summary", {})
            covered = summary.get("covered_lines", 0)
            total = summary.get("num_statements", 0)
            percent = (covered / total * 100) if total > 0 else 0

            total_covered += covered
            total_statements += total

            files.append(
                FileCoverage(
                    path=file_path,
                    covered_lines=covered,
                    total_lines=total,
                    percent=round(percent, 2),
                )
            )

        total_percent = (
            (total_covered / total_statements * 100) if total_statements > 0 else 0
        )
        # Fallback to totals if available
        if "totals" in data:
            total_percent = data["totals"].get("percent_covered", total_percent)

        return CoverageResponse(
            success=True, total_percent=round(total_percent, 2), files=files
        )
    except Exception as e:
        return CoverageResponse(success=False, error=str(e))


# Prompts History
def get_prompts_history() -> PromptsHistoryResponse:
    try:
        # Look for prompts files in common output locations
        runs = []
        search_paths = [
            _SCRIPTS / "output",
            _SCRIPTS.parent / "output",
            Path.cwd() / "output",
        ]

        for search_path in search_paths:
            if search_path.exists():
                for f in search_path.glob("**/prompts*.json"):
                    try:
                        stat = f.stat()
                        run_id = f.stem.replace("prompts_", "")
                        runs.append(
                            PromptsRunInfo(
                                run_id=run_id,
                                timestamp=str(stat.st_mtime),
                                file_path=str(f),
                            )
                        )
                    except Exception:
                        continue

        # Sort by timestamp descending
        runs.sort(key=lambda x: x.timestamp, reverse=True)
        return PromptsHistoryResponse(success=True, runs=runs, total=len(runs))
    except Exception as e:
        return PromptsHistoryResponse(success=False, error=str(e))


def get_prompts_by_run(run_id: str) -> PromptsRunResponse:
    try:
        # Search for the prompts file
        history = get_prompts_history()
        if not history.success:
            return PromptsRunResponse(success=False, error=history.error)

        # Find matching run
        matching = [
            r for r in history.runs if r.run_id == run_id or run_id in r.file_path
        ]
        if not matching:
            return PromptsRunResponse(
                success=False, run_id=run_id, error="Run not found"
            )

        prompts_file = Path(matching[0].file_path)
        data = json.loads(prompts_file.read_text())

        prompts = []
        for entry in data if isinstance(data, list) else data.get("prompts", []):
            prompts.append(
                PromptEntry(
                    agent=entry.get("agent", "unknown"),
                    system_prompt=entry.get("system_prompt", ""),
                    user_prompt=entry.get("user_prompt", ""),
                    response=entry.get("response", ""),
                    timestamp=entry.get("timestamp"),
                )
            )

        return PromptsRunResponse(success=True, run_id=run_id, prompts=prompts)
    except Exception as e:
        return PromptsRunResponse(success=False, run_id=run_id, error=str(e))


# Input Interpretation
def interpret_input(req: InterpretInputRequest) -> InterpretInputResponse:
    try:
        result = _pipeline()(model=req.model).interpret_user_input(
            req.user_input, _to_internal(req.scenarios)
        )
        return InterpretInputResponse(
            success=True,
            action=result.get("action", "unknown"),
            feedback=result.get("feedback"),
        )
    except Exception as e:
        return InterpretInputResponse(success=False, error=str(e))


# Syntax Validation
def validate_syntax(req: ValidateSyntaxRequest) -> ValidateSyntaxResponse:
    try:
        ast.parse(req.code)
        return ValidateSyntaxResponse(success=True, is_valid=True, errors=[])
    except SyntaxError as e:
        return ValidateSyntaxResponse(
            success=True,
            is_valid=False,
            errors=[
                SyntaxErrorSchema(
                    line=e.lineno or 0,
                    column=e.offset or 0,
                    message=str(e.msg) if hasattr(e, "msg") else str(e),
                )
            ],
        )
    except Exception as e:
        return ValidateSyntaxResponse(success=False, is_valid=False, errors=[])
