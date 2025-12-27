"""Unit tests for GUI widgets."""

import pytest
from unittest.mock import Mock, patch

pytest.importorskip("customtkinter")


class TestPhaseStep:
    """Tests for PhaseStep widget."""

    def test_states_configuration(self):
        """PhaseStep should have valid state configurations."""
        from src.extension.GUI.widgets.phase_step import PhaseStep
        
        for state in ["pending", "active", "completed"]:
            assert state in PhaseStep.STATES
            config = PhaseStep.STATES[state]
            assert all(k in config for k in ["fg_color", "border_color", "text_color", "show_check"])
        
        assert PhaseStep.STATES["pending"]["show_check"] is False
        assert PhaseStep.STATES["completed"]["show_check"] is True


class TestStatsCard:
    """Tests for StatsCard widget."""

    def test_class_structure(self):
        """StatsCard should have required methods and inherit from CTkFrame."""
        from src.extension.GUI.widgets.stats_card import StatsCard
        import customtkinter as ctk
        
        assert issubclass(StatsCard, ctk.CTkFrame)
        assert callable(getattr(StatsCard, "update_stats"))
        assert callable(getattr(StatsCard, "_build_ui"))


class TestPerformanceGraph:
    """Tests for PerformanceGraph widget."""

    def test_lines_configuration(self):
        """PerformanceGraph should have valid LINES config."""
        from src.extension.GUI.widgets.perf_graph import PerformanceGraph
        
        assert len(PerformanceGraph.LINES) == 3
        expected = {"coverage_data", "security_data", "time_data"}
        assert {line[0] for line in PerformanceGraph.LINES} == expected

    def test_clamp_function(self):
        """_clamp should handle various input types."""
        from src.extension.GUI.widgets.perf_graph import PerformanceGraph
        
        # Valid inputs
        assert PerformanceGraph._clamp(50, int, 0, 100) == 50
        assert PerformanceGraph._clamp(150, float, 0, 100) == 100
        assert PerformanceGraph._clamp(-10, int, 0) == 0
        # Invalid/None inputs return type defaults
        assert PerformanceGraph._clamp(None, int) == 0
        assert PerformanceGraph._clamp("invalid", float) == 0.0
        # String conversion
        assert PerformanceGraph._clamp("5", int) == 5

    def test_has_required_methods(self):
        """PerformanceGraph should have required methods."""
        from src.extension.GUI.widgets.perf_graph import PerformanceGraph
        
        for method in ["add_data_point", "reset", "_init_data", "_refresh"]:
            assert hasattr(PerformanceGraph, method)
