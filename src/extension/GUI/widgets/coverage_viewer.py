"""CoverageViewer Widget - Hierarchical code coverage visualization."""

import json
import subprocess
from pathlib import Path
from tkinter import filedialog
from typing import Dict, List, Optional

import customtkinter as ctk
from ..theme import COLORS
from .base_viewer import ViewerToolbarMixin

__all__ = ["CoverageViewer"]


def _get_color_for_pct(pct: float) -> str:
    """Return color based on coverage percentage."""
    if pct >= 80:
        return COLORS["accent_green"]
    return "#facc15" if pct >= 50 else COLORS["accent_red"]


def _format_line_ranges(lines: List[int], limit: int = 5) -> str:
    """Format line numbers into condensed ranges."""
    if not lines:
        return ""
    ranges, start, end = [], lines[0], lines[0]
    for ln in lines[1:]:
        if ln == end + 1:
            end = ln
        else:
            ranges.append(f"{start}-{end}" if start != end else str(start))
            start = end = ln
    ranges.append(f"{start}-{end}" if start != end else str(start))
    return ", ".join(ranges[:limit]) + ("..." if len(ranges) > limit else "")


class CodeContextViewer(ctk.CTkFrame):
    """Viewer for source code with coverage highlighting."""

    def __init__(self, parent, file_path: str, uncovered_lines: List[int], **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.file_path = file_path
        self.uncovered_lines = set(uncovered_lines)
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="Source Code", font=ctk.CTkFont(size=17, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=4, pady=(0, 4))

        self.textbox = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=17),
            fg_color=COLORS["bg_card"], text_color=COLORS["text_primary"],
            wrap="none", height=300
        )
        self.textbox.pack(fill="both", expand=True)
        
        try:
            self.textbox._textbox.tag_config("uncovered", background="#3f1313", foreground="#fca5a5")
            self.textbox._textbox.tag_config("covered", background="#0c2e17", foreground="#86efac")
            self.textbox._textbox.tag_config("linenum", foreground=COLORS["text_muted"])
        except Exception:
            pass
        
        self._load_content()

    def _load_content(self):
        path = Path(self.file_path)
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        
        if not path.exists():
            self.textbox.insert("end", f"File not found: {self.file_path}")
        else:
            try:
                for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(keepends=True), 1):
                    self.textbox.insert("end", f"{i:4d} ", "linenum")
                    self.textbox.insert("end", line, "uncovered" if i in self.uncovered_lines else "covered")
            except Exception as e:
                self.textbox.insert("end", f"Error loading file: {e}")
        
        self.textbox.configure(state="disabled")


class FileCoverageCard(ctk.CTkFrame):
    """Expandable card showing file-level coverage with function breakdown."""

    def __init__(self, parent, file_path: str, file_data: dict, on_open_editor=None, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=8, **kwargs)
        self.file_path = file_path
        self.file_data = file_data
        self.on_open_editor = on_open_editor
        self.expanded = False
        self.detail_frame = None
        self._build_header()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        header.pack(fill="x", padx=8, pady=6)
        header.bind("<Button-1>", lambda e: self._toggle_expand())

        self.expand_icon = ctk.CTkLabel(
            header, text="▶", font=ctk.CTkFont(size=14),
            text_color=COLORS["text_muted"], width=20
        )
        self.expand_icon.pack(side="left", padx=(0, 4))
        self.expand_icon.bind("<Button-1>", lambda e: self._toggle_expand())

        ctk.CTkLabel(
            header, text=Path(self.file_path).name, font=ctk.CTkFont(size=17),
            text_color=COLORS["text_primary"], anchor="w"
        ).pack(side="left", fill="x", expand=True)

        pct = self.file_data.get("coverage_percentage", 0.0)
        color = _get_color_for_pct(pct)
        
        ctk.CTkLabel(
            header, text=f"{pct:.1f}%", font=ctk.CTkFont(size=17, weight="bold"), text_color=color
        ).pack(side="right", padx=(8, 0))

        progress = ctk.CTkProgressBar(header, width=100, height=8, progress_color=color, fg_color=COLORS["border"])
        progress.set(pct / 100.0)
        progress.pack(side="right")

    def _toggle_expand(self):
        self.expanded = not self.expanded
        self.expand_icon.configure(text="▼" if self.expanded else "▶")
        
        if self.expanded:
            self._show_details()
        elif self.detail_frame:
            self.detail_frame.destroy()
            self.detail_frame = None

    def _show_details(self):
        self.detail_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=6)
        self.detail_frame.pack(fill="x", padx=12, pady=(0, 8))

        # Functions list
        for fn in self.file_data.get("functions", []):
            self._render_function_row(fn)

        # Uncovered lines info
        uncovered = self.file_data.get("uncovered_lines", [])
        if uncovered:
            row = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=4)
            
            ctk.CTkLabel(
                row, text=f"Uncovered: {_format_line_ranges(uncovered)}",
                font=ctk.CTkFont(size=15), text_color=COLORS["accent_red"]
            ).pack(side="left")

        # Action buttons (always show)
        btn_row = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=4)

        ctk.CTkButton(
            btn_row, text="View Code Context", width=140, height=28,
            fg_color=COLORS["bg_card"], hover_color=COLORS["border"],
            font=ctk.CTkFont(size=15), command=lambda: self._toggle_code_context(uncovered)
        ).pack(side="left")

        if self.on_open_editor:
            ctk.CTkButton(
                btn_row, text="Open in VSCode", width=130, height=28,
                fg_color=COLORS["button_primary"], hover_color=COLORS["button_hover"],
                font=ctk.CTkFont(size=15),
                command=lambda: self.on_open_editor(self.file_path, uncovered[0] if uncovered else 1)
            ).pack(side="right")

    def _toggle_code_context(self, uncovered):
        for widget in self.detail_frame.winfo_children():
            if isinstance(widget, CodeContextViewer):
                widget.destroy()
                return
        CodeContextViewer(self.detail_frame, self.file_path, uncovered, height=300).pack(fill="x", padx=8, pady=8)

    def _render_function_row(self, fn: dict):
        row = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=2)

        pct = fn.get("coverage_percentage", 0.0)
        name, line = fn.get("name", "unknown"), fn.get("start_line", 1)

        ctk.CTkLabel(
            row, text=f"  {name}()", font=ctk.CTkFont(family="Consolas", size=15),
            text_color=COLORS["text_secondary"]
        ).pack(side="left")
        
        ctk.CTkLabel(
            row, text=f"{pct:.0f}%", font=ctk.CTkFont(size=15), text_color=_get_color_for_pct(pct)
        ).pack(side="right", padx=(0, 8))

        if self.on_open_editor:
            row.bind("<Button-1>", lambda e: self.on_open_editor(self.file_path, line))


class CoverageViewer(ViewerToolbarMixin, ctk.CTkFrame):
    """Main coverage visualization widget with summary and file list."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.data: Dict = {}
        self.data_source_path: Optional[Path] = None
        self.file_cards: List[FileCoverageCard] = []
        self._build_ui()

    def _build_ui(self):
        # Use mixin for common toolbar components
        super()._build_toolbar(
            label_text="📊 Coverage:",
            placeholder_text="Select coverage_report.json...",
            browse_callback=self._browse,
            status_text="No data",
        )


        # Scrollable file list
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_dark"], corner_radius=12)
        self.scroll_frame.pack(fill="both", expand=True)

        # Empty state
        self.empty = ctk.CTkLabel(
            self, text="📊 No coverage data loaded.\nRun the pipeline or click 'Browse'.",
            font=ctk.CTkFont(size=20), text_color=COLORS["text_muted"], justify="center"
        )
        self.empty.place(relx=0.5, rely=0.6, anchor="center")

    def _browse(self):
        if path := filedialog.askopenfilename(title="Select Coverage Report", filetypes=[("JSON", "*.json"), ("All", "*.*")]):
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
        for card in self.file_cards:
            card.destroy()
        self.file_cards.clear()


        # Sort by coverage ascending (worst first)
        for file_path, file_data in sorted(self.data.items(), key=lambda x: x[1].get("coverage_percentage", 0)):
            # Resolve path
            full_path = file_path
            if self.data_source_path:
                report_dir = self.data_source_path.parent
                project_root = report_dir.parent if report_dir.name == "tests" else report_dir
                for base in [project_root, report_dir]:
                    resolved = base / file_path
                    if resolved.exists():
                        full_path = str(resolved)
                        break

            card = FileCoverageCard(self.scroll_frame, full_path, file_data, on_open_editor=self._open_in_editor)
            card.pack(fill="x", padx=8, pady=4)
            self.file_cards.append(card)

    def _open_in_editor(self, file_path: str, line: int):
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
        self.empty.configure(text="📊 No coverage data loaded.\nRun the pipeline or click 'Browse'.")
        self.empty.place(relx=0.5, rely=0.6, anchor="center")
        self.status.configure(text="No data")
