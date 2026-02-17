"""Phase step widget for the progress stepper."""

import customtkinter as ctk

from ..theme import COLORS


class PhaseStep(ctk.CTkFrame):
    """A single phase step indicator with icon and label."""

    STATES = {
        "pending": {
            "fg_color": COLORS["bg_card"],
            "border_color": COLORS["border"],
            "text_color": COLORS["text_muted"],
            "show_check": False,
        },
        "active": {
            "fg_color": COLORS["bg_card"],
            "border_color": COLORS["accent_green"],
            "text_color": COLORS["accent_green"],
            "show_check": False,
        },
        "completed": {
            "fg_color": COLORS["accent_green"],
            "border_color": COLORS["accent_green"],
            "text_color": COLORS["accent_green"],
            "show_check": True,
        },
    }

    def __init__(self, master, label: str, icon: str, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.label_text = label
        self.icon = icon
        self._state = "pending"
        self._build_ui()

    def _build_ui(self):
        """Build the widget UI."""
        # Icon circle
        self.icon_frame = ctk.CTkFrame(
            self,
            width=40,
            height=40,
            corner_radius=20,
            fg_color=COLORS["bg_card"],
            border_width=2,
            border_color=COLORS["border"],
        )
        self.icon_frame.pack(pady=(0, 8))
        self.icon_frame.pack_propagate(False)

        self.icon_label = ctk.CTkLabel(
            self.icon_frame,
            text=self.icon,
            font=ctk.CTkFont(size=16),
            text_color=COLORS["text_muted"],
        )
        self.icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # Phase label
        self.phase_label = ctk.CTkLabel(
            self,
            text=self.label_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_muted"],
        )
        self.phase_label.pack()

    def set_state(self, state: str):
        """Set phase state: pending, active, or completed."""
        if state not in self.STATES:
            return
        self._state = state
        style = self.STATES[state]

        self.icon_frame.configure(
            fg_color=style["fg_color"], border_color=style["border_color"]
        )
        self.icon_label.configure(
            text="✓" if style["show_check"] else self.icon,
            text_color=COLORS["text_primary"]
            if style["show_check"]
            else style["text_color"],
        )
        self.phase_label.configure(text_color=style["text_color"])
