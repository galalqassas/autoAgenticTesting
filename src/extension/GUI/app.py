"""
Pipeline GUI - Main Application
A modern, minimalistic GUI for the Python Testing Pipeline.
"""

import logging
import time
from contextlib import contextmanager
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from .theme import COLORS
from .widgets import (
    StatsCard,
    PerformanceGraph,
    AgentFlow,
    ConversationViewer,
    ReportViewer,
)
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
        self.bind("<Control-Return>", lambda e: self._toggle_pipeline())
        self.bind("<Control-o>", lambda e: self._browse_path())

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
        self.stats_cards = {}
        self.latest_prompts_file = None  # Track prompts file from pipeline
        self.latest_report_file = None  # Track report file from pipeline
        self._graph_iteration = 0  # Track iterations for graph

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
        """Build the main content area with tabbed interface."""
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=24, pady=(12, 24))

        # Tab bar
        self._build_tab_bar(self.main_container)

        # Content frames container
        self.content_container = ctk.CTkFrame(
            self.main_container, fg_color="transparent"
        )
        self.content_container.pack(fill="both", expand=True, pady=(16, 0))

        # Pipeline tab content
        self.pipeline_frame = ctk.CTkFrame(
            self.content_container, fg_color="transparent"
        )
        self._build_stepper(self.pipeline_frame)
        self._build_stats_row(self.pipeline_frame)
        self._build_console(self.pipeline_frame)

        # Prompts tab content
        self.prompts_frame = ConversationViewer(self.content_container)

        # Report tab content
        self.report_frame = ReportViewer(self.content_container)

        # Show pipeline tab by default
        self.current_tab = "pipeline"
        self._show_tab("pipeline")

    def _build_tab_bar(self, parent):
        """Build the tab navigation bar."""
        tab_bar = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_card"], corner_radius=10, height=44
        )
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)

        tab_inner = ctk.CTkFrame(tab_bar, fg_color="transparent")
        tab_inner.pack(side="left", padx=8, pady=6)

        self.tab_buttons = {}

        # Pipeline tab button
        self.tab_buttons["pipeline"] = ctk.CTkButton(
            tab_inner,
            text="🔧 Pipeline",
            width=120,
            height=32,
            fg_color=COLORS["button_primary"],
            hover_color=COLORS["button_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            command=lambda: self._show_tab("pipeline"),
        )
        self.tab_buttons["pipeline"].pack(side="left", padx=(0, 4))

        # Prompts tab button
        self.tab_buttons["prompts"] = ctk.CTkButton(
            tab_inner,
            text="💬 Prompts",
            width=120,
            height=32,
            fg_color=COLORS["bg_dark"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(size=13),
            corner_radius=8,
            command=lambda: self._show_tab("prompts"),
        )
        self.tab_buttons["prompts"].pack(side="left", padx=(0, 4))

        # Report tab button
        self.tab_buttons["report"] = ctk.CTkButton(
            tab_inner,
            text="📊 Report",
            width=120,
            height=32,
            fg_color=COLORS["bg_dark"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(size=13),
            corner_radius=8,
            command=lambda: self._show_tab("report"),
        )
        self.tab_buttons["report"].pack(side="left", padx=(0, 4))

    def _show_tab(self, tab_name: str):
        """Switch to the specified tab."""
        self.current_tab = tab_name

        # Hide all frames
        self.pipeline_frame.pack_forget()
        self.prompts_frame.pack_forget()
        self.report_frame.pack_forget()

        # Update button styles
        for name, btn in self.tab_buttons.items():
            if name == tab_name:
                btn.configure(
                    fg_color=COLORS["button_primary"],
                    font=ctk.CTkFont(size=13, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color=COLORS["bg_dark"],
                    font=ctk.CTkFont(size=13),
                )

        # Show selected frame
        if tab_name == "pipeline":
            self.pipeline_frame.pack(fill="both", expand=True)
        elif tab_name == "prompts":
            self.prompts_frame.pack(fill="both", expand=True)
        elif tab_name == "report":
            self.report_frame.pack(fill="both", expand=True)

    def _build_stepper(self, parent):
        """Build the agent flow stepper."""
        self.agent_flow = AgentFlow(parent)
        self.agent_flow.pack(fill="x", pady=(0, 24))

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
        self.log_text.pack(fill="both", expand=True, padx=16, pady=(8, 8))
        self.log_text.configure(state="disabled")

        # Input area for sending commands to pipeline
        input_frame = ctk.CTkFrame(frame, fg_color="transparent", height=36)
        input_frame.pack(fill="x", padx=16, pady=(0, 12))

        self.input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type input and press Enter or Send...",
            fg_color=COLORS["bg_console"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family="Consolas", size=12),
            height=32,
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.input_entry.bind("<Return>", lambda e: self._send_input())

        ctk.CTkButton(
            input_frame,
            text="Send",
            width=70,
            height=32,
            fg_color=COLORS["button_primary"],
            hover_color=COLORS["button_hover"],
            font=ctk.CTkFont(size=12),
            command=self._send_input,
        ).pack(side="right")

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
        self._pipeline_start_time = time.time()
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

    def _send_input(self):
        """Send input from entry to pipeline subprocess."""
        text = self.input_entry.get().strip()
        if not text:
            return
        if self.runner.send_input(text):
            self._log(f"> {text}\n")
        self.input_entry.delete(0, "end")

    # ==================== Callbacks ====================
    def _on_output(self, line: str):
        """Handle pipeline output line."""
        self.after(0, lambda: self._process_line(line))

    def _process_line(self, line: str):
        """Process a log line and update UI."""
        self._log(line)
        result = self.parser.parse(line)

        # Detect prompts file from pipeline output
        if "Prompts saved" in line and ":" in line:
            # Extract path from "Prompts saved: /path/to/file.json" or similar
            parts = line.split(":", 1)
            if len(parts) > 1:
                path = parts[-1].strip().rstrip('"').lstrip('"')
                if path.endswith(".json"):
                    self.latest_prompts_file = path

        # Detect report file from pipeline output
        if "Report saved:" in line or "Report:" in line:
            parts = line.split(":", 1)
            if len(parts) > 1:
                path = parts[-1].strip().rstrip('"').lstrip('"')
                if path.endswith(".md"):
                    self.latest_report_file = path

        if result.phase_update:
            phase, state = result.phase_update
            self.update_idletasks()

        if result.agent_activation:
            self.agent_flow.add_agent(result.agent_activation)

        # Update performance graph when we have new metrics
        # Track if we got new data worth graphing
        should_update_graph = False

        if result.coverage:
            self.stats_cards["coverage"].update_stats(
                f"{result.coverage}%", "Lines covered"
            )
            should_update_graph = True

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

        # Update graph only when coverage changes
        if should_update_graph:
            self._graph_iteration += 1
            try:
                coverage = float(result.coverage)
            except (ValueError, TypeError):
                coverage = 0.0
            elapsed = time.time() - getattr(self, "_pipeline_start_time", time.time())
            self.graph.add_point(self._graph_iteration, coverage, elapsed)

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
        self.agent_flow.show_end()
        self._log(f"\n{'=' * 60}\nPipeline execution finished.\n")

        # Auto-load prompts file if available
        if self.latest_prompts_file:
            from pathlib import Path

            if Path(self.latest_prompts_file).exists():
                self._log(f"\n📂 Loading prompts: {self.latest_prompts_file}\n")
                self.prompts_frame.load_file(self.latest_prompts_file)
                self.prompts_frame.file_entry.delete(0, "end")
                self.prompts_frame.file_entry.insert(0, self.latest_prompts_file)
            self.latest_prompts_file = None  # Reset for next run

        # Auto-load report file if available
        if self.latest_report_file:
            if Path(self.latest_report_file).exists():
                self._log(f"\n📊 Loading report: {self.latest_report_file}\n")
                self.report_frame.load_file(self.latest_report_file)
                self.report_frame.file_entry.delete(0, "end")
                self.report_frame.file_entry.insert(0, self.latest_report_file)
                self._show_tab("report")  # Switch to report tab
            self.latest_report_file = None  # Reset for next run

    # ==================== Helpers ====================
    def _reset_ui(self):
        """Reset UI to initial state."""
        self.agent_flow.reset()
        for name, value, subtext, _ in self.STATS:
            self.stats_cards[name.lower()].update_stats(value, subtext)
        self.graph.reset()
        self.report_frame.reset()
        self._clear_log()
        self._graph_iteration = 0  # Track iterations for graph

    @contextmanager
    def _log_editable(self):
        """Context manager for safe log text editing."""
        self.log_text.configure(state="normal")
        yield self.log_text
        self.log_text.configure(state="disabled")

    def _log(self, msg: str):
        """Append message to log console."""
        with self._log_editable():
            self.log_text.insert("end", msg)
            self.log_text.see("end")

    def _clear_log(self):
        """Clear the log console."""
        with self._log_editable():
            self.log_text.delete("1.0", "end")
