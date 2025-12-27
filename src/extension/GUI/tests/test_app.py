"""Unit tests for PipelineGUI application."""

import pytest
from unittest.mock import Mock, patch


class TestPipelineGUIConfig:
    """Tests for PipelineGUI configuration."""

    def test_class_attributes(self):
        """PipelineGUI should have PHASES and STATS configured."""
        from src.extension.GUI.app import PipelineGUI
        
        assert len(PipelineGUI.PHASES) == 3
        assert len(PipelineGUI.STATS) == 3
        
        for label, icon in PipelineGUI.PHASES:
            assert isinstance(label, str) and len(icon) > 0
        
        for name, value, subtext, color in PipelineGUI.STATS:
            assert isinstance(name, str) and color.startswith("#")


class TestPipelineGUIModules:
    """Tests for module imports."""

    def test_all_modules_import(self):
        """All GUI modules should import correctly."""
        from src.extension.GUI import app, theme, log_parser, pipeline_runner
        from src.extension.GUI.widgets import PhaseStep, StatsCard, PerformanceGraph
        
        assert all(x is not None for x in [
            app.PipelineGUI, theme.COLORS, log_parser.LogParser, 
            pipeline_runner.PipelineRunner, PhaseStep, StatsCard, PerformanceGraph
        ])


class TestPipelineGUIMethods:
    """Tests for PipelineGUI methods."""

    @pytest.fixture
    def mock_gui(self):
        """Create mocked PipelineGUI."""
        with patch("customtkinter.CTk.__init__", return_value=None):
            with patch("src.extension.GUI.app.PipelineGUI._setup_window"):
                with patch("src.extension.GUI.app.PipelineGUI._init_components"):
                    with patch("src.extension.GUI.app.PipelineGUI._build_ui"):
                        from src.extension.GUI.app import PipelineGUI
                        gui = PipelineGUI()
                        gui.runner = Mock(is_running=False)
                        gui.parser = Mock()
                        gui.phases = {"identify": Mock(), "implement": Mock(), "verify": Mock()}
                        gui.stats_cards = {"coverage": Mock(), "tests": Mock(), "security": Mock()}
                        gui.log_text = Mock()
                        gui.path_entry = Mock()
                        gui.input_entry = Mock()
                        gui.run_btn = Mock()
                        gui.auto_approve = Mock()
                        gui.graph = Mock()
                        gui.after = Mock(side_effect=lambda t, f: f())
                        return gui

    def test_browse_path(self, mock_gui):
        """_browse_path should update entry on folder selection."""
        with patch("src.extension.GUI.app.filedialog.askdirectory", return_value="/path"):
            mock_gui._browse_path()
            mock_gui.path_entry.insert.assert_called_with(0, "/path")
        
        with patch("src.extension.GUI.app.filedialog.askdirectory", return_value=""):
            mock_gui.path_entry.reset_mock()
            mock_gui._browse_path()
            mock_gui.path_entry.delete.assert_not_called()

    def test_toggle_pipeline(self, mock_gui):
        """_toggle_pipeline should start/stop based on state."""
        with patch.object(mock_gui, "_start_pipeline") as mock_start:
            mock_gui._toggle_pipeline()
            mock_start.assert_called_once()
        
        mock_gui.runner.is_running = True
        with patch.object(mock_gui, "_log"), patch.object(mock_gui, "_on_complete"):
            mock_gui._toggle_pipeline()
            mock_gui.runner.stop.assert_called_once()

    def test_start_pipeline_validation(self, mock_gui):
        """_start_pipeline should validate path and call runner."""
        mock_gui.path_entry.get.return_value = "   "
        with patch.object(mock_gui, "_log") as log:
            mock_gui._start_pipeline()
            assert "Error" in log.call_args[0][0]

    def test_send_input(self, mock_gui):
        """_send_input should forward non-empty input."""
        mock_gui.input_entry.get.return_value = "cmd"
        mock_gui.runner.send_input.return_value = True
        with patch.object(mock_gui, "_log"):
            mock_gui._send_input()
            mock_gui.runner.send_input.assert_called_with("cmd")
        
        mock_gui.input_entry.get.return_value = "   "
        mock_gui.runner.reset_mock()
        mock_gui._send_input()
        mock_gui.runner.send_input.assert_not_called()

    def test_process_line(self, mock_gui):
        """_process_line should update UI from parsed log."""
        from src.extension.GUI.log_parser import ParseResult
        
        # Use mock parser to control output
        mock_gui.parser.parse.return_value = ParseResult(
            phase_update=("identify", "active"),
            coverage="85.5"
        )
        mock_gui.update_idletasks = Mock()
        
        with patch.object(mock_gui, "_log"):
            mock_gui._process_line("Agent 1: Identifying")
            mock_gui.phases["identify"].set_state.assert_called_with("active")
            mock_gui.stats_cards["coverage"].update_stats.assert_called()

