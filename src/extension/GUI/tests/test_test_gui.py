"""Unit tests for test_gui.py launcher script."""

import pytest
from pathlib import Path


class TestTestGuiScript:
    """Tests for test_gui.py launcher."""

    def test_script_exists_and_valid(self):
        """Script should exist with required components."""
        script_path = Path(__file__).parent.parent / "test_gui.py"
        content = script_path.read_text()
        
        assert script_path.exists()
        assert "def main():" in content
        assert "PipelineGUI" in content
        assert 'if __name__ ==' in content
