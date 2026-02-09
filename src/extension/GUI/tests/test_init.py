"""Unit tests for GUI package initialization."""


class TestPackageExports:
    """Tests for package exports."""

    def test_gui_package_exports(self):
        """GUI package should export PipelineGUI."""
        from src.extension.GUI import PipelineGUI
        import src.extension.GUI as gui

        assert PipelineGUI is not None
        assert gui.__all__ == ["PipelineGUI"]

    def test_widgets_package_exports(self):
        """Widgets package should export all widgets."""
        from src.extension.GUI.widgets import (
            PhaseStep,
            StatsCard,
            PerformanceGraph,
            AgentFlow,
            PromptCard,
            ConversationViewer,
            ReportViewer,
            CoverageViewer,
        )
        import src.extension.GUI.widgets as widgets

        assert all(
            isinstance(w, type)
            for w in [
                PhaseStep,
                StatsCard,
                PerformanceGraph,
                AgentFlow,
                PromptCard,
                ConversationViewer,
                ReportViewer,
                CoverageViewer,
            ]
        )
        assert set(widgets.__all__) == {
            "PhaseStep",
            "StatsCard",
            "PerformanceGraph",
            "AgentFlow",
            "PromptCard",
            "ConversationViewer",
            "ReportViewer",
            "CoverageViewer",
        }
