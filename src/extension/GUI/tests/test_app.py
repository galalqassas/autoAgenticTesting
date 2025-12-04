"""End-to-end tests for the Pipeline GUI application."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestPipelineGUIImports:
    """Tests for GUI imports and initialization."""

    def test_app_module_imports(self):
        """Should import app module without error."""
        from src.extension.GUI import app

        assert hasattr(app, "PipelineGUI")

    def test_all_modules_import(self):
        """Should import all required modules."""
        from src.extension.GUI import theme, log_parser, pipeline_runner
        from src.extension.GUI.widgets import PhaseStep, StatsCard, PerformanceGraph

        assert theme.COLORS is not None
        assert log_parser.LogParser is not None
        assert pipeline_runner.PipelineRunner is not None


class TestPipelineGUIConfiguration:
    """Tests for GUI configuration."""

    def test_phases_defined(self):
        """Should have PHASES class attribute."""
        from src.extension.GUI.app import PipelineGUI

        assert hasattr(PipelineGUI, "PHASES")
        assert len(PipelineGUI.PHASES) == 3

    def test_stats_defined(self):
        """Should have STATS class attribute."""
        from src.extension.GUI.app import PipelineGUI

        assert hasattr(PipelineGUI, "STATS")
        assert len(PipelineGUI.STATS) == 3

    def test_phases_have_labels_and_icons(self):
        """Each phase should have label and icon."""
        from src.extension.GUI.app import PipelineGUI

        for phase in PipelineGUI.PHASES:
            assert len(phase) == 2
            label, icon = phase
            assert isinstance(label, str)
            assert len(icon) > 0

    def test_stats_have_required_fields(self):
        """Each stat should have name, value, subtext, color."""
        from src.extension.GUI.app import PipelineGUI

        for stat in PipelineGUI.STATS:
            assert len(stat) == 4
            name, value, subtext, color = stat
            assert isinstance(name, str)
            assert color.startswith("#")


class TestPipelineGUIIntegration:
    """Integration tests for GUI behavior."""

    @pytest.fixture
    def mock_tk_root(self):
        """Mock Tk root for headless testing."""
        with patch("customtkinter.CTk.__init__", return_value=None):
            with patch("customtkinter.CTk.title"):
                with patch("customtkinter.CTk.geometry"):
                    with patch("customtkinter.CTk.minsize"):
                        with patch("customtkinter.CTk.configure"):
                            yield

    def test_log_parser_integration(self):
        """LogParser should work with real pipeline output."""
        from src.extension.GUI.log_parser import LogParser

        parser = LogParser()

        # Simulate real pipeline output
        lines = [
            "🔍 Agent 1: Identifying test scenarios...",
            "   Found 5 Python files to analyze",
            "   Identified 45 scenarios (45 unique)",
            "🔧 Agent 2: Generating PyTest test code...",
            "--- Iteration 1 ---",
            "   Coverage: 95.2%",
            "   🔒 Security issues found: 3",
            "   Severe security issues: None",
            "✅ Pipeline Complete!",
        ]

        results = [parser.parse(line) for line in lines]

        # Check key extractions happened
        phases = [r.phase_update for r in results if r.phase_update]
        assert len(phases) > 0

        coverages = [r.coverage for r in results if r.coverage]
        assert "95.2" in coverages

        scenarios = [r.scenarios for r in results if r.scenarios]
        assert "45" in scenarios


class TestGUIWorkflow:
    """Tests for complete GUI workflow."""

    def test_parse_result_workflow(self):
        """Should handle complete parsing workflow."""
        from src.extension.GUI.log_parser import LogParser, ParseResult

        parser = LogParser()

        # Test the complete workflow
        result = parser.parse("Coverage: 85.5% - Tests passed")
        assert result.coverage == "85.5"

        # Multiple parses should be independent
        result2 = parser.parse("Something else")
        assert result2.coverage is None

    def test_runner_callback_pattern(self):
        """Should use callback pattern correctly."""
        from src.extension.GUI.pipeline_runner import PipelineRunner
        from pathlib import Path
        import tempfile

        outputs = []
        completed = [False]

        def on_output(line):
            outputs.append(line)

        def on_complete():
            completed[0] = True

        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "test.py"
            script.write_text("print('hello')")

            runner = PipelineRunner(script, on_output, on_complete)

            # Verify callbacks are stored
            assert runner.on_output == on_output
            assert runner.on_complete == on_complete
