"""Unit tests for main.py entry point."""


from unittest.mock import patch, MagicMock
from pathlib import Path


class TestMain:
    """Tests for main module."""

    def test_module_structure(self):
        """Module should have main() and import PipelineGUI."""
        from src.extension.GUI import main
        from src.extension.GUI.main import PipelineGUI
        
        assert callable(main.main)
        assert PipelineGUI is not None
        assert Path(main.__file__).name == "main.py"

    @patch("src.extension.GUI.main.PipelineGUI")
    def test_main_creates_and_runs_gui(self, mock_gui):
        """main() should create PipelineGUI and call mainloop."""
        mock_app = MagicMock()
        mock_gui.return_value = mock_app
        
        from src.extension.GUI.main import main
        main()
        
        mock_gui.assert_called_once()
        mock_app.mainloop.assert_called_once()
