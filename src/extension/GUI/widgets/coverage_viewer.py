"""CoverageViewer Widget - Hierarchical code coverage visualization."""

import json
import subprocess
from pathlib import Path
from tkinter import filedialog
from typing import Dict, List, Optional

import customtkinter as ctk

from ..theme import COLORS

__all__ = ["CoverageViewer"]


class FileCoverageCard(ctk.CTkFrame):
    """Expandable card showing file-level coverage with function breakdown."""

    def __init__(
        self,
        parent,
        file_path: str,
        file_data: dict,
        on_open_editor: callable = None,
        **kwargs,
    ):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=8, **kwargs)
        self.file_path = file_path
        self.file_data = file_data
        self.on_open_editor = on_open_editor
        self.expanded = False
        self.detail_frame = None
        self._build_header()

    def _build_header(self):
        """Build the collapsed header row."""
        header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        header.pack(fill="x", padx=8, pady=6)
        header.bind("<Button-1>", lambda e: self._toggle_expand())

        # Expand icon
        self.expand_icon = ctk.CTkLabel(
            header,
            text="▶",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
            width=20,
        )
        self.expand_icon.pack(side="left", padx=(0, 4))
        self.expand_icon.bind("<Button-1>", lambda e: self._toggle_expand())

        # File name
        name = Path(self.file_path).name
        ctk.CTkLabel(
            header,
            text=name,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_primary"],
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # Coverage percentage
        pct = self.file_data.get("coverage_percentage", 0.0)
        color = self._get_color_for_pct(pct)
        ctk.CTkLabel(
            header,
            text=f"{pct:.1f}%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=color,
        ).pack(side="right", padx=(8, 0))

        # Progress bar
        progress = ctk.CTkProgressBar(
            header, width=100, height=8, progress_color=color, fg_color=COLORS["border"]
        )
        progress.set(pct / 100.0)
        progress.pack(side="right")

    def _get_color_for_pct(self, pct: float) -> str:
        if pct >= 80:
            return COLORS["accent_green"]
        elif pct >= 50:
            return "#facc15"  # Yellow
        else:
            return COLORS["accent_red"]

    def _toggle_expand(self):
        self.expanded = not self.expanded
        self.expand_icon.configure(text="▼" if self.expanded else "▶")
        if self.expanded:
            self._show_details()
        elif self.detail_frame:
            self.detail_frame.destroy()
            self.detail_frame = None

    def _show_details(self):
        """Render the expanded detail view."""
        self.detail_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=6)
        self.detail_frame.pack(fill="x", padx=12, pady=(0, 8))

        # Functions list
        functions = self.file_data.get("functions", [])
        if functions:
            for fn in functions:
                self._render_function_row(fn)

        # Uncovered lines summary
        uncovered = self.file_data.get("uncovered_lines", [])
        if uncovered:
            uncovered_text = self._format_line_ranges(uncovered)
            row = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=4)
            ctk.CTkLabel(
                row,
                text=f"Uncovered: {uncovered_text}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["accent_red"],
            ).pack(side="left")

            # Buttons Frame
            btn_row = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
            btn_row.pack(fill="x", padx=8, pady=4)

            # View Code Context button
            ctk.CTkButton(
                btn_row,
                text="View Code Context",
                width=120,
                height=24,
                fg_color=COLORS["bg_card"],
                hover_color=COLORS["border"],
                font=ctk.CTkFont(size=11),
                command=lambda: self._toggle_code_context(uncovered),
            ).pack(side="left")

            # Open in editor button
            if self.on_open_editor:
                ctk.CTkButton(
                    btn_row,
                    text="Open in VSCode",
                    width=100,
                    height=24,
                    fg_color=COLORS["button_primary"],
                    hover_color=COLORS["button_hover"],
                    font=ctk.CTkFont(size=11),
                    command=lambda: self.on_open_editor(self.file_path, uncovered[0] if uncovered else 1),
                ).pack(side="right")

    def _toggle_code_context(self, uncovered):
        # Implementation to show CodeContextViewer
        # For simplicity, we can create a Toplevel window or append to detail frame
        # Let's append to detail_frame for now
        
        # Check if already shown
        for widget in self.detail_frame.winfo_children():
            if isinstance(widget, CodeContextViewer):
                widget.destroy()
                return

        CodeContextViewer(
            self.detail_frame, 
            self.file_path, 
            uncovered,
            height=300
        ).pack(fill="x", padx=8, pady=8)

    def _render_function_row(self, fn: dict):
        row = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=2)

        pct = fn.get("coverage_percentage", 0.0)
        color = self._get_color_for_pct(pct)
        name = fn.get("name", "unknown")
        line = fn.get("start_line", 1)

        ctk.CTkLabel(
            row,
            text=f"  {name}()",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLORS["text_secondary"],
        ).pack(side="left")
        ctk.CTkLabel(
            row, text=f"{pct:.0f}%", font=ctk.CTkFont(size=11), text_color=color
        ).pack(side="right", padx=(0, 8))

        # Click to open
        if self.on_open_editor:
            row.bind("<Button-1>", lambda e: self.on_open_editor(self.file_path, line))

    def _format_line_ranges(self, lines: List[int]) -> str:
        if not lines:
            return ""
        ranges = []
        start = lines[0]
        end = start
        for ln in lines[1:]:
            if ln == end + 1:
                end = ln
            else:
                ranges.append(f"{start}-{end}" if start != end else str(start))
                start = end = ln
        ranges.append(f"{start}-{end}" if start != end else str(start))
        return ", ".join(ranges[:5]) + ("..." if len(ranges) > 5 else "")


class CodeContextViewer(ctk.CTkFrame):
    """Viewer for source code with coverage highlighting."""

    def __init__(self, parent, file_path: str, uncovered_lines: List[int], **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.file_path = file_path
        self.uncovered_lines = set(uncovered_lines)
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=30)
        header.pack(fill="x", padx=4, pady=(0, 4))
        
        ctk.CTkLabel(
            header, 
            text="Source Code", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")

        # Code content
        self.textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text_primary"],
            wrap="none",
            height=300
        )
        self.textbox.pack(fill="both", expand=True)
        
        # Tags for highlighting (using _textbox to access underlying tk widget)
        try:
            self.textbox._textbox.tag_config("uncovered", background="#3f1313", foreground="#fca5a5") # Red bg
            self.textbox._textbox.tag_config("covered", background="#0c2e17", foreground="#86efac")   # Green bg
            self.textbox._textbox.tag_config("linenum", foreground=COLORS["text_muted"])
        except Exception:
            pass  # Fallback if _textbox access fails

        self._load_content()

    def _load_content(self):
        try:
            # Resolve relative paths against the report directory if possible
            path_obj = Path(self.file_path)
            
            # If path not found, and it's relative.
            if not path_obj.exists() and not path_obj.is_absolute():
                pass

            if not path_obj.exists():
                self.textbox.configure(state="normal")
                self.textbox.insert("end", f"File not found: {self.file_path}\n")
                self.textbox.insert("end", f"Current CWD: {Path.cwd()}\n")
                self.textbox.configure(state="disabled")
                return

            with open(path_obj, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            
            for i, line in enumerate(lines, 1):
                # Line number
                self.textbox.insert("end", f"{i:4d} ", "linenum")
                
                # Code line
                tag = "uncovered" if i in self.uncovered_lines else "covered"
                self.textbox.insert("end", line, tag)
                
            self.textbox.configure(state="disabled")
        except Exception as e:
            self.textbox.configure(state="normal")
            self.textbox.insert("end", f"Error loading file: {e}")
            self.textbox.configure(state="disabled")


class CoverageViewer(ctk.CTkFrame):
    """Main coverage visualization widget with summary and file list."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.data: Dict = {}
        self.data_source_path: Optional[Path] = None
        self.file_cards: List[FileCoverageCard] = []
        self._build_ui()

    def _build_ui(self):
        # Toolbar
        bar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12, height=60)
        bar.pack(fill="x", pady=(0, 16))
        bar.pack_propagate(False)
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            inner,
            text="📊 Coverage:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(side="left")

        self.file_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Select coverage_report.json...",
            width=350,
            height=36,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
        )
        self.file_entry.pack(side="left", padx=8)

        ctk.CTkButton(
            inner,
            text="Browse",
            width=70,
            height=36,
            fg_color=COLORS["button_primary"],
            hover_color=COLORS["button_hover"],
            command=self._browse,
        ).pack(side="left", padx=(0, 16))

        self.status = ctk.CTkLabel(
            inner,
            text="No data",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        )
        self.status.pack(side="right")

        # Summary header
        self.summary_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        self.summary_frame.pack(fill="x", pady=(0, 16))
        self.summary_label = ctk.CTkLabel(
            self.summary_frame,
            text="Overall Coverage: --%",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["accent_green"],
        )
        self.summary_label.pack(pady=16)

        # Scrollable file list
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color=COLORS["bg_dark"], corner_radius=12
        )
        self.scroll_frame.pack(fill="both", expand=True)

        # Empty state
        self.empty = ctk.CTkLabel(
            self,
            text="📊 No coverage data loaded.\nRun the pipeline or click 'Browse'.",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_muted"],
            justify="center",
        )
        self.empty.place(relx=0.5, rely=0.6, anchor="center")

    def _browse(self):
        if path := filedialog.askopenfilename(
            title="Select Coverage Report",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        ):
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, path)
            self.load_file(path)

    def load_file(self, filepath: str):
        try:
            path = Path(filepath)
            if not path.exists():
                return self._show_error(f"File not found: {filepath}")
            
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            
            self.data_source_path = path
            self.empty.place_forget()
            self._render()
            self.status.configure(text=f"Loaded: {path.name}")
        except Exception as e:
            self._show_error(str(e))

    def _render(self):
        # Clear existing cards
        for card in self.file_cards:
            card.destroy()
        self.file_cards.clear()

        # Calculate overall
        total_lines = sum(f.get("total_lines", 0) for f in self.data.values())
        covered_lines = sum(f.get("covered_lines", 0) for f in self.data.values())
        overall_pct = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0

        color = COLORS["accent_green"] if overall_pct >= 80 else COLORS["accent_red"]
        self.summary_label.configure(
            text=f"Overall Coverage: {overall_pct:.1f}% ({covered_lines}/{total_lines} lines)",
            text_color=color
        )

        # Sort files by coverage ascending (worst first)
        sorted_files = sorted(
            self.data.items(), key=lambda x: x[1].get("coverage_percentage", 0)
        )

        for file_path, file_data in sorted_files:
            # Resolve absolute path for the file relative to the coverage report location
            full_path = file_path
            if self.data_source_path:
                report_dir = self.data_source_path.parent
                # If report is in 'tests' folder, go up one level
                if report_dir.name == "tests":
                    project_root = report_dir.parent
                else:
                    project_root = report_dir
                
                resolved = project_root / file_path
                if resolved.exists():
                    full_path = str(resolved)
                else:
                    # Fallback matches relative to report dir
                    resolved_direct = report_dir / file_path
                    if resolved_direct.exists():
                        full_path = str(resolved_direct)

            card = FileCoverageCard(
                self.scroll_frame,
                full_path,
                file_data,
                on_open_editor=self._open_in_editor,
            )
            card.pack(fill="x", padx=8, pady=4)
            self.file_cards.append(card)

    def _open_in_editor(self, file_path: str, line: int):
        """Open file in VS Code at the specified line."""
        try:
            subprocess.Popen(["code", "-g", f"{file_path}:{line}"], shell=True)
        except Exception as e:
            print(f"Could not open editor: {e}")

    def _show_error(self, msg: str):
        self.status.configure(text=f"Error: {msg[:30]}...")
        self.empty.configure(text=f"❌ {msg}")
        self.empty.place(relx=0.5, rely=0.6, anchor="center")

    def reset(self):
        self.data = {}
        for card in self.file_cards:
            card.destroy()
        self.file_cards.clear()
        self.file_entry.delete(0, "end")
        self.summary_label.configure(text="Overall Coverage: --%")
        self.empty.configure(
            text="📊 No coverage data loaded.\nRun the pipeline or click 'Browse'."
        )
        self.empty.place(relx=0.5, rely=0.6, anchor="center")
        self.status.configure(text="No data")
