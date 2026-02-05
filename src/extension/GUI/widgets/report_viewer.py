"""ReportViewer Widget - Markdown report viewer with rendering."""

import re
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk
from ..theme import COLORS

TAGS = {
    "h1": {"font": ("Segoe UI", 28, "bold"), "foreground": "#60a5fa", "spacing3": 12},
    "h2": {
        "font": ("Segoe UI", 22, "bold"),
        "foreground": "#818cf8",
        "spacing1": 16,
        "spacing3": 8,
    },
    "h3": {
        "font": ("Segoe UI", 20, "bold"),
        "foreground": "#a78bfa",
        "spacing1": 12,
        "spacing3": 6,
    },
    "bold": {"font": ("Consolas", 17, "bold"), "foreground": "#f9fafb"},
    "code": {
        "font": ("Consolas", 15),
        "foreground": "#4ade80",
        "background": "#1e293b",
    },
    "th": {"font": ("Consolas", 15, "bold"), "foreground": "#60a5fa"},
    "td": {"font": ("Consolas", 15), "foreground": "#94a3b8"},
    "border": {"font": ("Consolas", 15), "foreground": "#475569"},
    "bullet": {"foreground": "#60a5fa"},
}


class ReportViewer(ctk.CTkFrame):
    """Markdown report viewer with styled headers, tables, and inline formatting."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.report_path = None
        self._build_ui()

    def _build_ui(self):
        # Toolbar
        bar = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"], corner_radius=12, height=60
        )
        bar.pack(fill="x", pady=(0, 16))
        bar.pack_propagate(False)
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            inner,
            text="📄 Report:",
            font=ctk.CTkFont(size=17),
            text_color=COLORS["text_secondary"],
        ).pack(side="left")
        self.file_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Select .md file...",
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
            text="No report",
            font=ctk.CTkFont(size=15),
            text_color=COLORS["text_muted"],
        )
        self.status.pack(side="right")

        # Content
        self.content = ctk.CTkTextbox(
            self,
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family="Consolas", size=17),
            corner_radius=12,
            wrap="word",
        )
        self.content.pack(fill="both", expand=True)
        self.content.configure(state="disabled")
        for name, opts in TAGS.items():
            self.content._textbox.tag_configure(name, **opts)

        self.empty = ctk.CTkLabel(
            self,
            text="📄 No report loaded.\nClick 'Browse' to open.",
            font=ctk.CTkFont(size=20),
            text_color=COLORS["text_muted"],
            justify="center",
        )
        self.empty.place(relx=0.5, rely=0.5, anchor="center")

    def _browse(self):
        if path := filedialog.askopenfilename(
            title="Select Report", filetypes=[("Markdown", "*.md"), ("All", "*.*")]
        ):
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, path)
            self.load_file(path)

    def load_file(self, filepath: str):
        try:
            path = Path(filepath)
            if not path.exists():
                return self._show_error(f"File not found: {filepath}")
            self.report_path, self.empty.place_forget()
            self._render(path.read_text(encoding="utf-8"))
            self.status.configure(text=f"Loaded: {path.name}")
        except Exception as e:
            self._show_error(str(e))

    def _render(self, text: str):
        tb = self.content._textbox
        self.content.configure(state="normal")
        tb.delete("1.0", "end")

        lines, i = text.split("\n"), 0
        while i < len(lines):
            line, s = lines[i], lines[i].strip()
            # Table block
            if s.startswith("|") and s.endswith("|"):
                table = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table.append(lines[i].strip())
                    i += 1
                self._render_table(tb, table)
                continue
            # Headers
            if s.startswith("# "):
                tb.insert("end", s[2:] + "\n", "h1")
            elif s.startswith("## "):
                tb.insert("end", s[3:] + "\n", "h2")
            elif s.startswith("### "):
                tb.insert("end", s[4:] + "\n", "h3")
            elif s.startswith("- "):
                self._insert_inline(tb, "  • " + s[2:] + "\n", "bullet")
            else:
                self._insert_inline(tb, line + "\n")
            i += 1
        self.content.configure(state="disabled")

    def _render_table(self, tb, rows):
        """Render markdown table with box-drawing borders."""
        parsed = [
            [c.strip() for c in r.strip("|").split("|")]
            for r in rows
            if not all(set(c.strip()) <= {"-", ":"} for c in r.strip("|").split("|"))
        ]
        if not parsed:
            return
        cols = max(len(r) for r in parsed)
        widths = [
            max(
                (len(parsed[i][j]) if j < len(parsed[i]) else 0)
                for i in range(len(parsed))
            )
            for j in range(cols)
        ]

        def row_str(cells, tag):
            tb.insert("end", "│", "border")
            for j, w in enumerate(widths):
                tb.insert(
                    "end", f" {(cells[j] if j < len(cells) else '').ljust(w)} ", tag
                )
                tb.insert("end", "│", "border")
            tb.insert("end", "\n")

        tb.insert(
            "end", "┌" + "┬".join("─" * (w + 2) for w in widths) + "┐\n", "border"
        )
        row_str(parsed[0], "th")
        tb.insert(
            "end", "├" + "┼".join("─" * (w + 2) for w in widths) + "┤\n", "border"
        )
        for r in parsed[1:]:
            row_str(r, "td")
        tb.insert(
            "end", "└" + "┴".join("─" * (w + 2) for w in widths) + "┘\n", "border"
        )

    def _insert_inline(self, tb, text, tag=None):
        """Insert text with **bold** and `code` inline formatting."""
        for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
            if part.startswith("**") and part.endswith("**"):
                tb.insert("end", part[2:-2], "bold")
            elif part.startswith("`") and part.endswith("`"):
                tb.insert("end", part[1:-1], "code")
            else:
                tb.insert("end", part, tag) if tag else tb.insert("end", part)

    def _show_error(self, msg: str):
        self.content.configure(state="normal")
        self.content._textbox.delete("1.0", "end")
        self.content.configure(state="disabled")
        self.empty.configure(text=f"❌ {msg}")
        self.empty.place(relx=0.5, rely=0.5, anchor="center")
        self.status.configure(text="Error")

    def reset(self):
        self.report_path = None
        self.file_entry.delete(0, "end")
        self.content.configure(state="normal")
        self.content._textbox.delete("1.0", "end")
        self.content.configure(state="disabled")
        self.empty.configure(text="📄 No report loaded.\nClick 'Browse' to open.")
        self.empty.place(relx=0.5, rely=0.5, anchor="center")
        self.status.configure(text="No report")
