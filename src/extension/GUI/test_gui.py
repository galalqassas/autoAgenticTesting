#!/usr/bin/env python3
"""Test script to launch the Pipeline GUI with a pre-filled path."""

import sys
from pathlib import Path

# Add parent to path for relative imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.extension.GUI.app import PipelineGUI


def main():
    """Launch GUI with test path."""
    app = PipelineGUI()
    # Compute path dynamically from project root for portability
    project_root = Path(__file__).parent.parent.parent.parent.parent
    default_path = project_root / "apps" / "todo"
    app.path_entry.insert(0, str(default_path))
    print(f"GUI launched with pre-filled path: {default_path}")
    app.mainloop()


if __name__ == "__main__":
    main()
