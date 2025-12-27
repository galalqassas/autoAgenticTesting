"""Unit tests for GUI widgets."""

import pytest

pytest.importorskip("customtkinter")


class TestPhaseStep:
    """Tests for PhaseStep widget."""

    def test_states_configuration(self):
        """PhaseStep should have valid state configurations."""
        from src.extension.GUI.widgets.phase_step import PhaseStep

        for state in ["pending", "active", "completed"]:
            assert state in PhaseStep.STATES
            config = PhaseStep.STATES[state]
            assert all(
                k in config
                for k in ["fg_color", "border_color", "text_color", "show_check"]
            )

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


class TestAgentFlow:
    """Tests for AgentFlow widget."""

    def test_agents_configuration(self):
        """AgentFlow should have valid AGENTS config."""
        from src.extension.GUI.widgets.agent_flow import AgentFlow

        assert len(AgentFlow.AGENTS) == 3
        for agent_num, (label, icon) in AgentFlow.AGENTS.items():
            assert isinstance(agent_num, int)
            assert isinstance(label, str) and len(label) > 0
            assert isinstance(icon, str) and len(icon) > 0

    def test_class_structure(self):
        """AgentFlow should inherit from CTkFrame and have required methods."""
        from src.extension.GUI.widgets.agent_flow import AgentFlow
        import customtkinter as ctk

        assert issubclass(AgentFlow, ctk.CTkFrame)
        for method in [
            "add_agent",
            "show_end",
            "reset",
            "_build_ui",
            "_create_node",
            "_set_node_state",
        ]:
            assert hasattr(AgentFlow, method)


class TestPromptCard:
    """Tests for PromptCard widget."""

    def test_class_structure(self):
        """PromptCard should inherit from CTkFrame and have required methods."""
        from src.extension.GUI.widgets.prompt_card import PromptCard
        import customtkinter as ctk

        assert issubclass(PromptCard, ctk.CTkFrame)
        assert callable(getattr(PromptCard, "expand_all"))
        assert callable(getattr(PromptCard, "collapse_all"))

    def test_constants_defined(self):
        """PromptCard module should have ICONS and AGENT_COLORS."""
        from src.extension.GUI.widgets import prompt_card

        assert hasattr(prompt_card, "ICONS")
        assert hasattr(prompt_card, "AGENT_COLORS")
        assert "System Prompt" in prompt_card.ICONS
        assert "User Prompt" in prompt_card.ICONS
        assert "Response" in prompt_card.ICONS
        assert "identification_agent" in prompt_card.AGENT_COLORS
        assert "implementation_agent" in prompt_card.AGENT_COLORS
        assert "evaluation_agent" in prompt_card.AGENT_COLORS


class TestCollapsibleSection:
    """Tests for CollapsibleSection widget."""

    def test_class_structure(self):
        """CollapsibleSection should inherit from CTkFrame and have required methods."""
        from src.extension.GUI.widgets.prompt_card import CollapsibleSection
        import customtkinter as ctk

        assert issubclass(CollapsibleSection, ctk.CTkFrame)
        for method in ["expand", "collapse", "_toggle", "_copy"]:
            assert callable(getattr(CollapsibleSection, method))


class TestBlendFunction:
    """Tests for blend helper function."""

    def test_blend_colors(self):
        """blend should correctly mix two hex colors."""
        from src.extension.GUI.widgets.prompt_card import blend

        # No blend (amt=0) returns base
        assert blend("#000000", "#ffffff", 0).lower() == "#000000"
        # Full blend (amt=1) returns tint
        assert blend("#000000", "#ffffff", 1).lower() == "#ffffff"
        # 50% blend
        result = blend("#000000", "#ffffff", 0.5).lower()
        assert result in ("#7f7f7f", "#808080")  # Allow for rounding

    def test_blend_handles_short_hex(self):
        """blend should handle 3-char hex colors."""
        from src.extension.GUI.widgets.prompt_card import blend

        # #fff expands to #ffffff
        result = blend("#000", "#fff", 1).lower()
        assert result == "#ffffff"


class TestConversationViewer:
    """Tests for ConversationViewer widget."""

    def test_class_structure(self):
        """ConversationViewer should inherit from CTkFrame and have required methods."""
        from src.extension.GUI.widgets.conversation_viewer import ConversationViewer
        import customtkinter as ctk

        assert issubclass(ConversationViewer, ctk.CTkFrame)
        for method in [
            "load_file",
            "reset",
            "_browse",
            "_render",
            "_expand_all",
            "_collapse_all",
        ]:
            assert callable(getattr(ConversationViewer, method))

    def test_agent_types_defined(self):
        """AGENT_TYPES should be defined with expected values."""
        from src.extension.GUI.widgets.conversation_viewer import AGENT_TYPES

        assert isinstance(AGENT_TYPES, list)
        assert len(AGENT_TYPES) >= 4
        # First item should be "All Agents"
        assert "All Agents" in AGENT_TYPES[0]


class TestWidgetsPackage:
    """Tests for widgets package exports."""

    def test_all_exports(self):
        """Widgets __init__ should export all expected classes."""
        from src.extension.GUI.widgets import (
            PhaseStep,
            StatsCard,
            PerformanceGraph,
            AgentFlow,
            PromptCard,
            ConversationViewer,
        )

        assert all(
            cls is not None
            for cls in [
                PhaseStep,
                StatsCard,
                PerformanceGraph,
                AgentFlow,
                PromptCard,
                ConversationViewer,
            ]
        )

    def test_all_list_matches_exports(self):
        """__all__ should list all exported widgets."""
        from src.extension.GUI import widgets

        expected = {
            "PhaseStep",
            "StatsCard",
            "PerformanceGraph",
            "AgentFlow",
            "PromptCard",
            "ConversationViewer",
        }
        assert set(widgets.__all__) == expected
