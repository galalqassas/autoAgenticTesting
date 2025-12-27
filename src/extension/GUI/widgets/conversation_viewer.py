"""ConversationViewer Widget - Main container for viewing prompt conversations."""

import json
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk
from ..theme import COLORS
from .prompt_card import PromptCard

AGENT_TYPES = [
    "🌐 All Agents",
    "🔍 identification_agent",
    "⚙️ implementation_agent",
    "🔧 implementation_agent_improvement",
    "📊 evaluation_agent",
]


class ConversationViewer(ctk.CTkFrame):
    """Viewer widget with file loader, filter, and scrollable prompt cards."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.prompts_data, self.prompt_cards, self.current_filter = [], [], "All Agents"
        self._build_toolbar()
        self._build_scroll_area()

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"], corner_radius=12, height=60
        )
        toolbar.pack(fill="x", pady=(0, 16))
        toolbar.pack_propagate(False)

        inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        # File loader
        ctk.CTkLabel(
            inner,
            text="📁 Load:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(side="left")
        self.file_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Select prompts JSON...",
            width=300,
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

        # Filter
        ctk.CTkLabel(
            inner,
            text="🔎",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(side="left")
        self.filter_dd = ctk.CTkOptionMenu(
            inner,
            values=AGENT_TYPES,
            width=240,
            height=36,
            fg_color=COLORS["input_bg"],
            button_color=COLORS["button_primary"],
            button_hover_color=COLORS["button_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["accent_blue"],
            font=ctk.CTkFont(size=11),
            corner_radius=8,
            command=self._on_filter,
        )
        self.filter_dd.pack(side="left", padx=8)

        # Expand/Collapse
        for text, cmd in [
            ("⊞ Expand", self._expand_all),
            ("⊟ Collapse", self._collapse_all),
        ]:
            ctk.CTkButton(
                inner,
                text=text,
                width=80,
                height=28,
                fg_color=COLORS["bg_dark"],
                hover_color=COLORS["border"],
                font=ctk.CTkFont(size=10),
                command=cmd,
            ).pack(side="left", padx=2)

        self.stats = ctk.CTkLabel(
            inner,
            text="No prompts",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        )
        self.stats.pack(side="right")

    def _build_scroll_area(self):
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg_dark"],
            corner_radius=12,
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["text_muted"],
        )
        self.scroll.pack(fill="both", expand=True)
        self.empty = ctk.CTkLabel(
            self.scroll,
            text="📂 No prompts loaded.\nClick 'Browse' to load.",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_muted"],
            justify="center",
        )
        self.empty.pack(expand=True, pady=100)

    def _browse(self):
        if path := filedialog.askopenfilename(
            title="Select Prompts JSON", filetypes=[("JSON", "*.json")]
        ):
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, path)
            self.load_file(path)

    def load_file(self, filepath: str):
        try:
            path = Path(filepath)
            if not path.exists():
                return self._error(f"File not found: {filepath}")

            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "prompts" in data:
                self.prompts_data = data.get("prompts", [])
                self._update_stats(
                    f"Run: {data.get('run_id', '?')} | Model: {data.get('model', '?')}"
                )
            elif isinstance(data, list):
                self.prompts_data = data
                self._update_stats()
            else:
                return self._error("Invalid JSON: expected 'prompts' array")
            self._render()
        except json.JSONDecodeError as e:
            self._error(f"Invalid JSON: {e}")
        except Exception as e:
            self._error(f"Error: {e}")

    def _render(self):
        for c in self.prompt_cards:
            c.destroy()
        self.prompt_cards.clear()
        self.empty.pack_forget()

        # Filter
        agent = (
            self.current_filter.split(" ", 1)[-1]
            if " " in self.current_filter
            else self.current_filter
        )
        filtered = (
            self.prompts_data
            if "All Agents" in self.current_filter
            else [p for p in self.prompts_data if p.get("agent") == agent]
        )

        # Create cards
        for i, p in enumerate(filtered, 1):
            card = PromptCard(self.scroll, p, index=i, total=len(filtered))
            card.pack(fill="x", padx=4, pady=(0, 10))
            self.prompt_cards.append(card)

        self.stats.configure(
            text=f"{len(filtered)}/{len(self.prompts_data)} prompts"
            + (f" ({agent})" if "All" not in self.current_filter else "")
        )
        if not self.prompt_cards:
            self.empty.configure(text="🔍 No prompts match filter.")
            self.empty.pack(expand=True, pady=100)

    def _on_filter(self, val: str):
        self.current_filter = val
        if self.prompts_data:
            self._render()

    def _update_stats(self, info: str = None):
        text = f"Total: {len(self.prompts_data)}"
        self.stats.configure(text=f"{info} | {text}" if info else text)

    def _error(self, msg: str):
        self.prompts_data = []
        self._render()
        self.empty.configure(text=f"❌ {msg}")
        self.empty.pack(expand=True, pady=100)
        self.stats.configure(text="Error")

    def reset(self):
        self.prompts_data = []
        self.file_entry.delete(0, "end")
        self.filter_dd.set("🌐 All Agents")
        self.current_filter = "All Agents"
        for c in self.prompt_cards:
            c.destroy()
        self.prompt_cards.clear()
        self.empty.configure(text="📂 No prompts loaded.\nClick 'Browse' to load.")
        self.empty.pack(expand=True, pady=100)
        self.stats.configure(text="No prompts")

    def _expand_all(self):
        for c in self.prompt_cards:
            c.expand_all()

    def _collapse_all(self):
        for c in self.prompt_cards:
            c.collapse_all()
