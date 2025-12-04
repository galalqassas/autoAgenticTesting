#!/usr/bin/env python3
"""Entry point for the Pipeline GUI application."""

import sys
from pathlib import Path

# Support direct script execution by adding parent to path
if __name__ == "__main__":
    _root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(_root))
    from src.extension.GUI.app import PipelineGUI
else:
    from .app import PipelineGUI


def main():
    """Launch the Pipeline GUI."""
    app = PipelineGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
