"""Unit tests for GUI widgets."""

import pytest
from unittest.mock import Mock, patch


# Skip widget tests if customtkinter not available in headless mode
pytest.importorskip("customtkinter")


class TestTheme:
    """Tests for theme configuration."""

    def test_colors_dict_exists(self):
        """Should have COLORS dictionary."""
        from src.extension.GUI.theme import COLORS

        assert isinstance(COLORS, dict)

    def test_required_colors_present(self):
        """Should have all required color keys."""
        from src.extension.GUI.theme import COLORS

        required = [
            "bg_dark",
            "bg_card",
            "bg_header",
            "bg_console",
            "text_primary",
            "text_secondary",
            "text_muted",
            "accent_green",
            "accent_blue",
            "accent_red",
            "button_primary",
            "button_hover",
        ]
        for key in required:
            assert key in COLORS, f"Missing color: {key}"

    def test_colors_are_hex(self):
        """All colors should be valid hex codes."""
        from src.extension.GUI.theme import COLORS

        for key, value in COLORS.items():
            assert value.startswith("#"), f"{key} should be hex: {value}"
            assert len(value) == 7, f"{key} should be #RRGGBB: {value}"

    def test_matplotlib_available_flag(self):
        """Should have MATPLOTLIB_AVAILABLE flag."""
        from src.extension.GUI.widgets.perf_graph import MATPLOTLIB_AVAILABLE

        assert isinstance(MATPLOTLIB_AVAILABLE, bool)


class TestPhaseStep:
    """Tests for PhaseStep widget."""

    @pytest.fixture
    def mock_ctk(self):
        """Mock customtkinter for headless testing."""
        with patch("src.extension.GUI.widgets.phase_step.ctk") as mock:
            mock.CTkFrame = Mock(return_value=Mock())
            mock.CTkLabel = Mock(return_value=Mock())
            mock.CTkFont = Mock(return_value=Mock())
            yield mock

    def test_states_dict_defined(self):
        """Should have STATES dictionary."""
        from src.extension.GUI.widgets.phase_step import PhaseStep

        assert hasattr(PhaseStep, "STATES")
        assert "pending" in PhaseStep.STATES
        assert "active" in PhaseStep.STATES
        assert "completed" in PhaseStep.STATES

    def test_state_has_required_keys(self):
        """Each state should have required styling keys."""
        from src.extension.GUI.widgets.phase_step import PhaseStep

        required_keys = ["fg_color", "border_color", "text_color", "show_check"]
        for state, config in PhaseStep.STATES.items():
            for key in required_keys:
                assert key in config, f"State {state} missing {key}"


class TestStatsCard:
    """Tests for StatsCard widget."""

    def test_import_succeeds(self):
        """Should import without error."""
        from src.extension.GUI.widgets.stats_card import StatsCard

        assert StatsCard is not None


class TestPerformanceGraph:
    """Tests for PerformanceGraph widget."""

    def test_lines_config_defined(self):
        """Should have LINES configuration."""
        from src.extension.GUI.widgets.perf_graph import PerformanceGraph

        assert hasattr(PerformanceGraph, "LINES")
        assert len(PerformanceGraph.LINES) == 3

    def test_lines_have_required_format(self):
        """Each line config should have (attr, color, label)."""
        from src.extension.GUI.widgets.perf_graph import PerformanceGraph

        for line in PerformanceGraph.LINES:
            assert len(line) == 3
            attr, color, label = line
            assert isinstance(attr, str)
            assert color.startswith("#")
            assert isinstance(label, str)
