"""Unit tests for PipelineGUI application."""

from unittest.mock import Mock, patch

import pytest


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

    def test_console_input_packed_before_log_textbox(self):
        """Input frame packed at bottom before log textbox."""
        import inspect

        from src.extension.GUI.app import PipelineGUI

        # Verify _build_console packs input_frame with side="bottom"
        source = inspect.getsource(PipelineGUI._build_console)

        # Find positions of key elements
        input_pack_pos = source.find('input_frame.pack(side="bottom"')
        log_pack_pos = source.find('self.log_text.pack(')
        input_creation_pos = source.find('input_frame = ctk.CTkFrame')
        log_creation_pos = source.find('self.log_text = ctk.CTkTextbox')

        # Input frame should be created before log_text
        assert input_creation_pos < log_creation_pos, (
            "input_frame should be created before log_text"
        )
        # Input frame should be packed before log_text
        assert input_pack_pos < log_pack_pos, (
            "input_frame should be packed before log_text"
        )
        # Input frame should be packed at bottom
        assert 'input_frame.pack(side="bottom"' in source, (
            "input_frame should be packed at bottom"
        )
        # pack_propagate should be called on input_frame
        assert "input_frame.pack_propagate(False)" in source, (
            "input_frame should have pack_propagate(False)"
        )

    def test_window_geometry_adequate_height(self):
        """Window should have adequate height for all elements."""
        import inspect

        from src.extension.GUI.app import PipelineGUI

        source = inspect.getsource(PipelineGUI._setup_window)
        # Extract geometry values
        import re
        match = re.search(r'geometry\("(\d+)x(\d+)"\)', source)
        assert match is not None, "geometry should be set in _setup_window"

        width, height = int(match.group(1)), int(match.group(2))
        assert width >= 1000, f"Window width {width} should be >= 1000"
        assert height >= 800, (
            f"Window height {height} should be >= 800 to fit input bar"
        )

    def test_window_minsize_set(self):
        """Window should have minimum size constraints."""
        import inspect

        from src.extension.GUI.app import PipelineGUI

        source = inspect.getsource(PipelineGUI._setup_window)
        assert "minsize(" in source, "minsize should be set for window"

    def test_tab_config_exists(self):
        """PipelineGUI should have TAB_CONFIG for reusable tab buttons."""
        from src.extension.GUI.app import PipelineGUI

        assert hasattr(PipelineGUI, "TAB_CONFIG"), "TAB_CONFIG should exist"
        assert len(PipelineGUI.TAB_CONFIG) >= 3, "Should have at least 3 tabs"

        for tab_id, label in PipelineGUI.TAB_CONFIG:
            assert isinstance(tab_id, str), "Tab ID should be string"
            assert isinstance(label, str), "Tab label should be string"

    def test_input_frame_has_fixed_height(self):
        """Input frame should have a fixed height to prevent squishing."""
        import inspect

        from src.extension.GUI.app import PipelineGUI

        source = inspect.getsource(PipelineGUI._build_console)
        # Check that input_frame is created with height parameter
        assert "height=50" in source or "height=36" in source, (
            "input_frame should have fixed height"
        )


class TestPipelineGUIModules:
    """Tests for module imports."""

    def test_all_modules_import(self):
        """All GUI modules should import correctly."""
        from src.extension.GUI import app, log_parser, pipeline_runner, theme
        from src.extension.GUI.widgets import PerformanceGraph, PhaseStep, StatsCard

        assert all(
            x is not None
            for x in [
                app.PipelineGUI,
                theme.COLORS,
                log_parser.LogParser,
                pipeline_runner.PipelineRunner,
                PhaseStep,
                StatsCard,
                PerformanceGraph,
            ]
        )


class TestPipelineGUIMethods:
    """Tests for PipelineGUI methods."""

    @pytest.fixture
    def mock_gui(self):
        """Create mocked PipelineGUI."""
        with patch("customtkinter.CTk.__init__", return_value=None):
            with patch("src.extension.GUI.app.PipelineGUI._setup_window"):
                with patch(
                    "src.extension.GUI.app.PipelineGUI._init_components"
                ):
                    with patch("src.extension.GUI.app.PipelineGUI._build_ui"):
                        from src.extension.GUI.app import PipelineGUI

                        gui = PipelineGUI()
                        gui.runner = Mock(is_running=False)
                        gui.parser = Mock()
                        gui.phases = {
                            "identify": Mock(),
                            "implement": Mock(),
                            "verify": Mock(),
                        }
                        gui.stats_cards = {
                            "coverage": Mock(),
                            "tests": Mock(),
                            "security": Mock(),
                        }
                        gui.log_text = Mock()
                        gui.path_entry = Mock()
                        gui.input_entry = Mock()
                        gui.run_btn = Mock()
                        gui.auto_approve = Mock()
                        gui.graph = Mock()
                        gui.agent_flow = Mock()
                        gui.latest_prompts_file = None
                        gui.latest_report_file = None
                        gui._graph_iteration = 0
                        gui._pipeline_start_time = 0
                        gui.after = Mock(side_effect=lambda t, f: f())
                        return gui

    def test_browse_path(self, mock_gui):
        """_browse_path should update entry on folder selection."""
        with patch(
            "src.extension.GUI.app.filedialog.askdirectory",
            return_value="/path"
        ):
            mock_gui._browse_path()
            mock_gui.path_entry.insert.assert_called_with(0, "/path")

        with patch(
            "src.extension.GUI.app.filedialog.askdirectory", return_value=""
        ):
            mock_gui.path_entry.reset_mock()
            mock_gui._browse_path()
            mock_gui.path_entry.delete.assert_not_called()

    def test_toggle_pipeline(self, mock_gui):
        """_toggle_pipeline should start/stop based on state."""
        with patch.object(mock_gui, "_start_pipeline") as mock_start:
            mock_gui._toggle_pipeline()
            mock_start.assert_called_once()

        mock_gui.runner.is_running = True
        with patch.object(mock_gui, "_log"), patch.object(
            mock_gui, "_on_complete"
        ):
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

        # Test agent activation and coverage update
        mock_gui.parser.parse.return_value = ParseResult(
            agent_activation=1, coverage="85.5"
        )
        mock_gui.update_idletasks = Mock()

        with patch.object(mock_gui, "_log"):
            mock_gui._process_line("Agent 1: Identifying")
            mock_gui.agent_flow.add_agent.assert_called_with(1)
            mock_gui.stats_cards["coverage"].update_stats.assert_called()
