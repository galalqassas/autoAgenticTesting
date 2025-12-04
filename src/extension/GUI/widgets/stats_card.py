"""Stats card widget for displaying metrics."""

import customtkinter as ctk
from ..theme import COLORS


class StatsCard(ctk.CTkFrame):
    """A card displaying a metric value with title and subtext."""

    def __init__(
        self, master, title: str, value: str, subtext: str, accent_color: str, **kwargs
    ):
        super().__init__(master, fg_color=COLORS["bg_card"], corner_radius=12, **kwargs)
        self.accent_color = accent_color
        self._build_ui(title, value, subtext)

    def _build_ui(self, title: str, value: str, subtext: str):
        """Build the card UI."""
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        )
        self.title_label.pack(anchor="w", padx=16, pady=(16, 4))

        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.accent_color,
        )
        self.value_label.pack(anchor="w", padx=16, pady=(0, 4))

        self.subtext_label = ctk.CTkLabel(
            self,
            text=subtext,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        )
        self.subtext_label.pack(anchor="w", padx=16, pady=(0, 16))

    def update_stats(self, value: str, subtext: str):
        """Update the displayed values."""
        self.value_label.configure(text=value)
        self.subtext_label.configure(text=subtext)
        self.update_idletasks()
