"""PromptCard Widget - Displays a prompt entry with collapsible sections."""

import customtkinter as ctk
from ..theme import COLORS


def blend(base: str, tint: str, amt: float) -> str:
    """Blend two hex colors."""
    b = base.lstrip("#")
    t = tint.lstrip("#")
    b = "".join(c * 2 for c in b) if len(b) == 3 else b
    t = "".join(c * 2 for c in t) if len(t) == 3 else t
    return "#{:02x}{:02x}{:02x}".format(
        *[
            int(
                int(b[i : i + 2], 16)
                + (int(t[i : i + 2], 16) - int(b[i : i + 2], 16)) * amt
            )
            for i in (0, 2, 4)
        ]
    )


ICONS = {"System Prompt": "📜", "User Prompt": "👤", "Response": "🤖"}
AGENT_COLORS = {
    "identification_agent": COLORS["agent_red"],
    "implementation_agent": COLORS["agent_green"],
    "implementation_agent_improvement": COLORS["agent_green_dark"],
    "evaluation_agent": COLORS["agent_blue"],
}


class CollapsibleSection(ctk.CTkFrame):
    """Collapsible section with copy button."""

    def __init__(self, parent, title: str, content: str, accent: str, **kwargs):
        super().__init__(
            parent, fg_color=blend("#1a1a1a", accent, 0.12), corner_radius=6, **kwargs
        )
        self.expanded, self.text, self.accent = True, content, accent

        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=6, pady=4)

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkFrame(left, fg_color=accent, width=3, height=18, corner_radius=1).pack(
            side="left", padx=(0, 6)
        )

        self.toggle = ctk.CTkButton(
            left,
            text="▼",
            width=16,
            height=16,
            fg_color="transparent",
            hover_color=COLORS["border"],
            text_color=accent,
            font=ctk.CTkFont(size=9),
            command=self._toggle,
        )
        self.toggle.pack(side="left")

        ctk.CTkLabel(
            left,
            text=f"{ICONS.get(title, '📋')} {title}",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=accent,
        ).pack(side="left", padx=4)
        ctk.CTkLabel(
            left,
            text=f"{len(content):,} chars",
            font=ctk.CTkFont(size=9),
            text_color=COLORS["text_muted"],
        ).pack(side="left", padx=6)

        self.copy_btn = ctk.CTkButton(
            hdr,
            text="📋",
            width=28,
            height=18,
            fg_color=COLORS["border"],
            hover_color=COLORS["button_primary"],
            font=ctk.CTkFont(size=10),
            command=self._copy,
        )
        self.copy_btn.pack(side="right")

        # Content
        self.content = ctk.CTkTextbox(
            self,
            fg_color=blend("#0a0a0a", accent, 0.05),
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family="Consolas", size=10),
            corner_radius=4,
            height=80,
            wrap="word",
        )
        self.content.insert("1.0", content)
        self.content.configure(state="disabled")
        self.content.pack(fill="both", expand=True, padx=6, pady=(0, 4))

    def _toggle(self):
        self.expanded = not self.expanded
        (
            self.content.pack(fill="both", expand=True, padx=6, pady=(0, 4))
            if self.expanded
            else self.content.pack_forget()
        )
        self.toggle.configure(text="▼" if self.expanded else "▶")

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.text)
        self.copy_btn.configure(text="✓")
        self.after(1000, lambda: self.copy_btn.configure(text="📋"))

    def expand(self):
        self.expanded or self._toggle()

    def collapse(self):
        self.expanded and self._toggle()


class PromptCard(ctk.CTkFrame):
    """Displays a prompt with header and collapsible sections."""

    def __init__(self, parent, data: dict, index: int = 0, total: int = 0, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=8, **kwargs)

        agent = data.get("agent", "unknown")
        color = AGENT_COLORS.get(agent, COLORS["agent_gray"])
        self.sections = []

        # Left accent
        ctk.CTkFrame(self, fg_color=color, width=4, corner_radius=2).pack(
            side="left", fill="y", pady=4
        )

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        # Header
        hdr = ctk.CTkFrame(main, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 4))

        if total > 0:
            idx = ctk.CTkFrame(hdr, fg_color=COLORS["border"], corner_radius=3)
            idx.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(
                idx,
                text=f"{index}/{total}",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=COLORS["text_secondary"],
            ).pack(padx=4, pady=1)

        icon = (
            "🔍"
            if "identification" in agent
            else "⚙️"
            if "implementation" in agent
            else "📊"
        )
        badge = ctk.CTkFrame(hdr, fg_color=color, corner_radius=4)
        badge.pack(side="left")
        ctk.CTkLabel(
            badge,
            text=f"{icon} {agent}",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#fff",
        ).pack(padx=6, pady=2)

        ctk.CTkLabel(
            hdr,
            text=data.get("timestamp", ""),
            font=ctk.CTkFont(size=9),
            text_color=COLORS["text_muted"],
        ).pack(side="left", padx=8)

        model = data.get("model", "").split("/")[-1]
        tag = ctk.CTkFrame(hdr, fg_color=COLORS["border"], corner_radius=3)
        tag.pack(side="right")
        ctk.CTkLabel(
            tag,
            text=model,
            font=ctk.CTkFont(size=8),
            text_color=COLORS["text_secondary"],
        ).pack(padx=4, pady=1)

        # Sections
        for title, key in [
            ("System Prompt", "system_prompt"),
            ("User Prompt", "user_prompt"),
            ("Response", "response"),
        ]:
            if content := data.get(key, ""):
                s = CollapsibleSection(main, title, content, color)
                s.pack(fill="x", pady=2)
                self.sections.append(s)

    def expand_all(self):
        for s in self.sections:
            s.expand()

    def collapse_all(self):
        for s in self.sections:
            s.collapse()
