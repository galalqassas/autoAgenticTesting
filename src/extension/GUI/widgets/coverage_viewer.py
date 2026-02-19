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


# ── Shared helpers ──────────────────────────────────────────────────


def _open_in_editor(file_path: str, line: int):
    """Open file in VS Code at the specified line."""
    try:
        subprocess.Popen(["code", "-g", f"{file_path}:{line}"], shell=True)
    except Exception as e:
        print(f"Could not open editor: {e}")


# ── Code context viewer (reused across tabs) ───────────────────────


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


# ── Line Coverage card (existing) ──────────────────────────────────


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


# ── Statement Coverage card ────────────────────────────────────────


class StatementCoverageCard(ctk.CTkFrame):
    """Card showing statement coverage for a single file."""

    def __init__(self, parent, file_path: str, stmt_data: dict, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=8, **kwargs)
        self.file_path = file_path
        self.stmt_data = stmt_data
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        header.pack(fill="x", padx=8, pady=6)

        ctk.CTkLabel(
            header, text=Path(self.file_path).name, font=ctk.CTkFont(size=17),
            text_color=COLORS["text_primary"], anchor="w"
        ).pack(side="left", fill="x", expand=True)

        pct = self.stmt_data.get("coverage_percentage", 0.0)
        total = self.stmt_data.get("total_statements", 0)
        covered = self.stmt_data.get("covered_statements", 0)
        color = _get_color_for_pct(pct)

        ctk.CTkLabel(
            header, text=f"{covered}/{total}",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_secondary"],
        ).pack(side="right", padx=(8, 4))

        ctk.CTkLabel(
            header, text=f"{pct:.1f}%",
            font=ctk.CTkFont(size=17, weight="bold"), text_color=color,
        ).pack(side="right", padx=(8, 0))

        progress = ctk.CTkProgressBar(header, width=100, height=8, progress_color=color, fg_color=COLORS["border"])
        progress.set(pct / 100.0)
        progress.pack(side="right")

        # Uncovered statement lines
        uncovered = self.stmt_data.get("uncovered_statement_lines", [])
        if uncovered:
            ctk.CTkLabel(
                self,
                text=f"  Uncovered statements at lines: {_format_line_ranges(uncovered, limit=8)}",
                font=ctk.CTkFont(size=14), text_color=COLORS["accent_red"], anchor="w",
            ).pack(fill="x", padx=12, pady=(0, 6))


# ── Branch Coverage card ───────────────────────────────────────────


class BranchCoverageCard(ctk.CTkFrame):
    """Expandable card showing branch coverage for a single file."""

    _ARM_ICON = {"True": "✅", "False": "❌"}

    def __init__(self, parent, file_path: str, branch_data: dict, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=8, **kwargs)
        self.file_path = file_path
        self.branch_data = branch_data
        self.expanded = False
        self.detail_frame = None
        self._build_header()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        header.pack(fill="x", padx=8, pady=6)
        header.bind("<Button-1>", lambda e: self._toggle())

        self.expand_icon = ctk.CTkLabel(
            header, text="▶", font=ctk.CTkFont(size=14),
            text_color=COLORS["text_muted"], width=20,
        )
        self.expand_icon.pack(side="left", padx=(0, 4))
        self.expand_icon.bind("<Button-1>", lambda e: self._toggle())

        ctk.CTkLabel(
            header, text=Path(self.file_path).name, font=ctk.CTkFont(size=17),
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(side="left", fill="x", expand=True)

        pct = self.branch_data.get("coverage_percentage", 0.0)
        total = self.branch_data.get("total_branches", 0)
        full = self.branch_data.get("fully_covered", 0)
        color = _get_color_for_pct(pct)

        ctk.CTkLabel(
            header, text=f"{full}/{total}",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_secondary"],
        ).pack(side="right", padx=(8, 4))

        ctk.CTkLabel(
            header, text=f"{pct:.1f}%",
            font=ctk.CTkFont(size=17, weight="bold"), text_color=color,
        ).pack(side="right", padx=(8, 0))

        progress = ctk.CTkProgressBar(header, width=100, height=8, progress_color=color, fg_color=COLORS["border"])
        progress.set(pct / 100.0)
        progress.pack(side="right")

    def _toggle(self):
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

        for br in self.branch_data.get("branches", []):
            row = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)

            construct = br.get("construct", "?")
            lineno = br.get("lineno", 0)
            fully = br.get("fully_covered", False)

            icon = "✅" if fully else "⚠️"
            ctk.CTkLabel(
                row,
                text=f"  {icon} {construct} (line {lineno})",
                font=ctk.CTkFont(family="Consolas", size=14),
                text_color=COLORS["accent_green"] if fully else "#facc15",
            ).pack(side="left")

            # Arm details
            arms = br.get("arms", [])
            arm_text = "  ".join(
                f"{'✅' if a.get('covered') else '❌'} {a.get('arm_name', '?')}"
                for a in arms
            )
            ctk.CTkLabel(
                row, text=arm_text,
                font=ctk.CTkFont(size=13), text_color=COLORS["text_secondary"],
            ).pack(side="right", padx=(0, 8))


# ── Metrics Summary Bar ────────────────────────────────────────────


class MetricsSummaryBar(ctk.CTkFrame):
    """Horizontal bar showing all coverage metric percentages."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=12, **kwargs)
        self.metric_labels: Dict[str, ctk.CTkLabel] = {}
        self._build()

    def _build(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        for name in ("Line", "Statement", "Branch"):
            frame = ctk.CTkFrame(inner, fg_color="transparent")
            frame.pack(side="left", expand=True, fill="x", padx=4)

            ctk.CTkLabel(
                frame, text=name,
                font=ctk.CTkFont(size=12), text_color=COLORS["text_secondary"],
            ).pack(anchor="w")

            lbl = ctk.CTkLabel(
                frame, text="--%",
                font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORS["text_muted"],
            )
            lbl.pack(anchor="w")
            self.metric_labels[name.lower()] = lbl

    def update_metrics(self, line_pct: float, stmt_pct: float, branch_pct: float):
        for key, val in [("line", line_pct), ("statement", stmt_pct), ("branch", branch_pct)]:
            lbl = self.metric_labels.get(key)
            if lbl:
                color = _get_color_for_pct(val) if val >= 0 else COLORS["text_muted"]
                text = f"{val:.1f}%" if val >= 0 else "N/A"
                lbl.configure(text=text, text_color=color)


# ── Main CoverageViewer ────────────────────────────────────────────


class CoverageViewer(ViewerToolbarMixin, ctk.CTkFrame):
    """Main coverage visualization widget with tabbed sub-views."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.data: Dict = {}
        self.data_source_path: Optional[Path] = None
        self.file_cards: List[ctk.CTkFrame] = []
        self._build_ui()

    def _build_ui(self):
        # Toolbar (browse bar)
        super()._build_toolbar(
            label_text="📊 Coverage:",
            placeholder_text="Select coverage_report.json...",
            browse_callback=self._browse,
            status_text="No data",
        )

        # Metrics summary bar
        self.metrics_bar = MetricsSummaryBar(self)
        self.metrics_bar.pack(fill="x", pady=(0, 8))

        # Sub-tab selector
        self.sub_tab_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10, height=38)
        self.sub_tab_frame.pack(fill="x", pady=(0, 8))
        self.sub_tab_frame.pack_propagate(False)

        sub_inner = ctk.CTkFrame(self.sub_tab_frame, fg_color="transparent")
        sub_inner.pack(side="left", padx=8, pady=4)

        self.sub_tabs: Dict[str, ctk.CTkButton] = {}
        self.current_sub_tab = "line"
        for i, (key, label) in enumerate([("line", "Line Coverage"), ("statement", "Statement Coverage"), ("branch", "Branch Coverage")]):
            btn = ctk.CTkButton(
                sub_inner, text=label, width=140, height=28,
                fg_color=COLORS["button_primary"] if i == 0 else COLORS["bg_dark"],
                hover_color=COLORS["button_hover"] if i == 0 else COLORS["border"],
                font=ctk.CTkFont(size=12, weight="bold" if i == 0 else "normal"),
                corner_radius=6,
                command=lambda k=key: self._switch_sub_tab(k),
            )
            btn.pack(side="left", padx=(0, 4))
            self.sub_tabs[key] = btn

        # Scrollable content area (all three tabs share this frame)
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_dark"], corner_radius=12)
        self.scroll_frame.pack(fill="both", expand=True)

        # Empty state
        self.empty = ctk.CTkLabel(
            self, text="📊 No coverage data loaded.\nRun the pipeline or click 'Browse'.",
            font=ctk.CTkFont(size=20), text_color=COLORS["text_muted"], justify="center"
        )
        self.empty.place(relx=0.5, rely=0.6, anchor="center")

    def _switch_sub_tab(self, key: str):
        self.current_sub_tab = key
        for name, btn in self.sub_tabs.items():
            if name == key:
                btn.configure(fg_color=COLORS["button_primary"], font=ctk.CTkFont(size=12, weight="bold"))
            else:
                btn.configure(fg_color=COLORS["bg_dark"], font=ctk.CTkFont(size=12))
        self._render()

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
                raw_data = json.load(f)
                # Filter out mutation_report so it doesn't appear as a file
                self.data = {k: v for k, v in raw_data.items() if k != "mutation_report"}

            self.data_source_path = path
            self.empty.place_forget()
            self._update_summary()
            self._render()
            self.status.configure(text=f"Loaded: {path.name}")
        except Exception as e:
            self._show_error(str(e))

    # ── Aggregation helpers ─────────────────────────────────────────

    def _update_summary(self):
        """Compute overall percentages for all three metric types."""
        total_lines = sum(f.get("total_lines", 0) for f in self.data.values())
        covered_lines = sum(f.get("covered_lines", 0) for f in self.data.values())
        line_pct = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0

        total_stmts = sum(
            (f.get("statement_coverage") or {}).get("total_statements", 0)
            for f in self.data.values()
        )
        covered_stmts = sum(
            (f.get("statement_coverage") or {}).get("covered_statements", 0)
            for f in self.data.values()
        )
        stmt_pct = (covered_stmts / total_stmts * 100) if total_stmts > 0 else -1.0

        total_br = sum(
            (f.get("branch_coverage") or {}).get("total_branches", 0)
            for f in self.data.values()
        )
        full_br = sum(
            (f.get("branch_coverage") or {}).get("fully_covered", 0)
            for f in self.data.values()
        )
        branch_pct = (full_br / total_br * 100) if total_br > 0 else -1.0

        self.metrics_bar.update_metrics(line_pct, stmt_pct, branch_pct)

    # ── Rendering ───────────────────────────────────────────────────

    def _render(self):
        """Render the currently selected sub-tab."""
        for card in self.file_cards:
            card.destroy()
        self.file_cards.clear()

        if self.current_sub_tab == "line":
            self._render_line_tab()
        elif self.current_sub_tab == "statement":
            self._render_statement_tab()
        elif self.current_sub_tab == "branch":
            self._render_branch_tab()

    def _resolve_path(self, file_path: str) -> str:
        """Try to resolve a relative path from the report to an absolute one."""
        if self.data_source_path:
            report_dir = self.data_source_path.parent
            project_root = report_dir.parent if report_dir.name == "tests" else report_dir
            for base in [project_root, report_dir]:
                resolved = base / file_path
                if resolved.exists():
                    return str(resolved)
        return file_path

    def _render_line_tab(self):
        for file_path, file_data in sorted(self.data.items(), key=lambda x: x[1].get("coverage_percentage", 0)):
            full_path = self._resolve_path(file_path)
            card = FileCoverageCard(self.scroll_frame, full_path, file_data, on_open_editor=_open_in_editor)
            card.pack(fill="x", padx=8, pady=4)
            self.file_cards.append(card)

    def _render_statement_tab(self):
        for file_path, file_data in sorted(self.data.items(), key=lambda x: (x[1].get("statement_coverage") or {}).get("coverage_percentage", 0)):
            stmt = file_data.get("statement_coverage")
            if not stmt:
                continue
            full_path = self._resolve_path(file_path)
            card = StatementCoverageCard(self.scroll_frame, full_path, stmt)
            card.pack(fill="x", padx=8, pady=4)
            self.file_cards.append(card)

        if not self.file_cards:
            lbl = ctk.CTkLabel(
                self.scroll_frame, text="No statement coverage data available.",
                font=ctk.CTkFont(size=16), text_color=COLORS["text_muted"],
            )
            lbl.pack(pady=20)
            self.file_cards.append(lbl)

    def _render_branch_tab(self):
        for file_path, file_data in sorted(self.data.items(), key=lambda x: (x[1].get("branch_coverage") or {}).get("coverage_percentage", 0)):
            br = file_data.get("branch_coverage")
            if not br or br.get("total_branches", 0) == 0:
                continue
            full_path = self._resolve_path(file_path)
            card = BranchCoverageCard(self.scroll_frame, full_path, br)
            card.pack(fill="x", padx=8, pady=4)
            self.file_cards.append(card)

        if not self.file_cards:
            lbl = ctk.CTkLabel(
                self.scroll_frame, text="No branch coverage data available.",
                font=ctk.CTkFont(size=16), text_color=COLORS["text_muted"],
            )
            lbl.pack(pady=20)
            self.file_cards.append(lbl)

    # ── Error / Reset ───────────────────────────────────────────────

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
        self.metrics_bar.update_metrics(0.0, -1.0, -1.0)
        self.empty.configure(text="📊 No coverage data loaded.\nRun the pipeline or click 'Browse'.")
        self.empty.place(relx=0.5, rely=0.6, anchor="center")
        self.status.configure(text="No data")
