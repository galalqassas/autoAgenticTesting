"""
Pipeline GUI - Main Application
A modern, minimalistic GUI for the Python Testing Pipeline.
"""

import logging
from contextlib import contextmanager
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from .theme import COLORS
from .widgets import PhaseStep, StatsCard, PerformanceGraph
from .log_parser import LogParser
from .pipeline_runner import PipelineRunner

logger = logging.getLogger(__name__)


class PipelineGUI(ctk.CTk):
    """Main Pipeline GUI Application."""

    PHASES = [("Identify", "🔍"), ("Implement", "⚙️"), ("Verify", "✓")]
    STATS = [
        ("Coverage", "--", "Waiting...", COLORS["accent_green"]),
        ("Tests", "--", "Waiting...", COLORS["accent_blue"]),
        ("Security", "0", "No issues", COLORS["accent_red"]),
    ]

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._init_components()
        self._build_ui()

    def _setup_window(self):
        """Configure window properties."""
        self.title("AutoTest - Python Testing Pipeline")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=COLORS["bg_dark"])

    def _init_components(self):
        """Initialize non-UI components."""
        script_path = (
            Path(__file__).parent.parent
            / "pythonTestingPipeline"
            / "scripts"
            / "pythonTestingPipeline.py"
        )
        self.runner = PipelineRunner(script_path, self._on_output, self._on_complete)
        self.parser = LogParser()
        self.phases = {}
        self.stats_cards = {}

    def _build_ui(self):
        """Build the complete UI."""
        self._build_header()
        self._build_main_content()

    # ==================== Header ====================
    def _build_header(self):
        """Build the header bar."""
        header = ctk.CTkFrame(
            self, fg_color=COLORS["bg_header"], height=70, corner_radius=0
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        # Title
        ctk.CTkLabel(
            header,
            text="🧪 AutoTest",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(side="left", padx=24)

        # Path input
        path_frame = ctk.CTkFrame(header, fg_color="transparent")
        path_frame.pack(side="left", expand=True, fill="x", padx=20)

        ctk.CTkLabel(
            path_frame,
            text="Target Path:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 8))

        self.path_entry = ctk.CTkEntry(
            path_frame,
            placeholder_text="Select target codebase...",
            width=400,
            height=36,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
        )
        self.path_entry.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            path_frame,
            text="📁",
            width=36,
            height=36,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            command=self._browse_path,
        ).pack(side="left")

        # Controls
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right", padx=24)

        self.auto_approve = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            controls,
            text="Auto-approve",
            variable=self.auto_approve,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            progress_color=COLORS["accent_green"],
        ).pack(side="left", padx=(0, 16))

        self.run_btn = ctk.CTkButton(
            controls,
            text="▶  Run Pipeline",
            width=140,
            height=40,
            fg_color=COLORS["button_primary"],
            hover_color=COLORS["button_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._toggle_pipeline,
        )
        self.run_btn.pack(side="left")

    # ==================== Main Content ====================
    def _build_main_content(self):
        """Build the main content area."""
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=24, pady=24)

        self._build_stepper(main)
        self._build_stats_row(main)
        self._build_console(main)

    def _build_stepper(self, parent):
        """Build the phase stepper."""
        frame = ctk.CTkFrame(parent, fg_color="transparent", height=100)
        frame.pack(fill="x", pady=(0, 24))

        container = ctk.CTkFrame(frame, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")

        for i, (label, icon) in enumerate(self.PHASES):
            if i > 0:
                ctk.CTkFrame(
                    container, width=60, height=2, fg_color=COLORS["border"]
                ).pack(side="left", pady=(0, 20))
            phase = PhaseStep(container, label, icon)
            phase.pack(side="left", padx=16)
            self.phases[label.lower()] = phase

    def _build_stats_row(self, parent):
        """Build the stats cards and graph row."""
        frame = ctk.CTkFrame(parent, fg_color="transparent", height=180)
        frame.pack(fill="x", pady=(0, 24))
        frame.pack_propagate(False)
        frame.grid_columnconfigure((0, 1), weight=1, uniform="stats")
        frame.grid_rowconfigure(0, weight=1)

        # Cards
        cards_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cards_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        cards_inner = ctk.CTkFrame(cards_frame, fg_color="transparent")
        cards_inner.pack(expand=True, fill="both")

        for name, value, subtext, color in self.STATS:
            card = StatsCard(cards_inner, name, value, subtext, color)
            card.pack(side="left", padx=(0, 8), fill="both", expand=True)
            self.stats_cards[name.lower()] = card

        # Graph
        self.graph = PerformanceGraph(frame)
        self.graph.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

    def _build_console(self, parent):
        """Build the log console."""
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12)
        frame.pack(fill="both", expand=True)

        header = ctk.CTkFrame(frame, fg_color="transparent", height=40)
        header.pack(fill="x", padx=16, pady=(8, 0))

        ctk.CTkLabel(
            header,
            text="📋 Output Log",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Clear",
            width=60,
            height=28,
            fg_color=COLORS["bg_dark"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(size=11),
            command=self._clear_log,
        ).pack(side="right")

        self.log_text = ctk.CTkTextbox(
            frame,
            fg_color=COLORS["bg_console"],
            text_color=COLORS["accent_green"],
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=8,
        )
        self.log_text.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        self.log_text.configure(state="disabled")

    # ==================== Actions ====================
    def _browse_path(self):
        """Open folder browser."""
        if folder := filedialog.askdirectory(title="Select Target Codebase"):
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)

    def _toggle_pipeline(self):
        """Start or stop the pipeline."""
        if self.runner.is_running:
            self.runner.stop()
            self._log("\n⚠️ Pipeline stopped by user.\n")
            self._on_complete()
        else:
            self._start_pipeline()

    def _start_pipeline(self):
        """Start pipeline execution."""
        target = self.path_entry.get().strip()
        if not target:
            self._log("❌ Error: Please select a target codebase path.\n")
            return

        self._reset_ui()
        cmd = f"🚀 Starting pipeline: python {self.runner.script_path} {target}"
        if self.auto_approve.get():
            cmd += " --auto-approve"
        self._log(f"{cmd}\n{'-' * 60}\n")

        if not self.runner.start(target, self.auto_approve.get()):
            self._log("❌ Error: Failed to start pipeline.\n")
            return

        self.run_btn.configure(
            text="⬛ Stop",
            fg_color=COLORS["accent_red"],
            hover_color=COLORS["button_stop"],
        )

    # ==================== Callbacks ====================
    def _on_output(self, line: str):
        """Handle pipeline output line."""
        self.after(0, lambda: self._process_line(line))

    def _process_line(self, line: str):
        """Process a log line and update UI."""
        self._log(line)
        result = self.parser.parse(line)

        if result.phase_update:
            phase, state = result.phase_update
            if phase in self.phases:
                self.phases[phase].set_state(state)
                self.update_idletasks()

        if result.coverage:
            self.stats_cards["coverage"].update_stats(
                f"{result.coverage}%", "Lines covered"
            )

        if result.tests:
            passed, total, failed = result.tests
            self.stats_cards["tests"].update_stats(
                f"{passed}/{total}", f"{failed} Failed"
            )
        elif result.scenarios:
            self.stats_cards["tests"].update_stats(
                result.scenarios, "Scenarios identified"
            )

        if result.security_issues:
            self.stats_cards["security"].update_stats(
                result.security_issues, "Issues found"
            )
        elif result.security_severity:
            label = (
                "No severe issues"
                if result.security_severity == "none"
                else "Low/Medium severity"
            )
            self.stats_cards["security"].update_stats(
                "0" if result.security_severity == "none" else result.security_severity,
                label,
            )

    def _on_complete(self):
        """Handle pipeline completion."""
        self.after(0, self._finalize)

    def _finalize(self):
        """Finalize UI after pipeline ends."""
        self.run_btn.configure(
            text="▶  Run Pipeline",
            fg_color=COLORS["button_primary"],
            hover_color=COLORS["button_hover"],
        )
        self._log(f"\n{'=' * 60}\nPipeline execution finished.\n")

    # ==================== Helpers ====================
    def _reset_ui(self):
        """Reset UI to initial state."""
        for phase in self.phases.values():
            phase.set_state("pending")
        for name, value, subtext, _ in self.STATS:
            self.stats_cards[name.lower()].update_stats(value, subtext)
        self.graph.reset()
        self._clear_log()

    @contextmanager
    def _log_editable(self):
        """Context manager for safe log text editing."""
        try:
            self.log_text.configure(state="normal")
            yield self.log_text
            self.log_text.configure(state="disabled")
        except Exception as e:
            logger.warning(f"Log operation failed: {e}")

    def _log(self, msg: str):
        """Append message to log console."""
        with self._log_editable():
            self.log_text.insert("end", msg)
            self.log_text.see("end")
        self.update_idletasks()

    def _clear_log(self):
        """Clear the log console."""
        with self._log_editable():
            self.log_text.delete("1.0", "end")
