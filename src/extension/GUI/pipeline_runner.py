"""Pipeline process runner with threading support."""

import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable, Optional


class PipelineRunner:
    """Manages pipeline subprocess execution."""

    def __init__(
        self,
        script_path: Path,
        on_output: Callable[[str], None],
        on_complete: Callable[[], None],
    ):
        self.script_path = script_path
        self.on_output = on_output
        self.on_complete = on_complete
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    def start(self, target_path: str, auto_approve: bool = True) -> bool:
        """Start the pipeline process. Returns False if already running or invalid path."""
        if self.is_running:
            return False
        if not Path(target_path).exists() or not self.script_path.exists():
            return False

        self.is_running = True
        cmd = [sys.executable, str(self.script_path), target_path]
        if auto_approve:
            cmd.append("--auto-approve")

        self._thread = threading.Thread(target=self._run, args=(cmd,), daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Stop the running pipeline."""
        self.is_running = False
        if self.process:
            self.process.terminate()

    def send_input(self, text: str) -> bool:
        """Send input to subprocess stdin. Returns False if not running."""
        if not self.is_running or not self.process or not self.process.stdin:
            return False
        try:
            self.process.stdin.write(text + "\n")
            self.process.stdin.flush()
            return True
        except (BrokenPipeError, OSError):
            return False

    def _run(self, cmd: list):
        """Execute the pipeline and stream output."""
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUNBUFFERED"] = "1"

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=str(self.script_path.parent),
                env=env,
                encoding="utf-8",
                errors="replace",
            )

            for line in iter(self.process.stdout.readline, ""):
                if not self.is_running:
                    break
                self.on_output(line)

            self.process.wait()
        except Exception as e:
            self.on_output(f"\n❌ Error: {e}\n")
        finally:
            self.is_running = False
            self.on_complete()
