"""Base viewer mixin providing common toolbar UI pattern for viewer widgets."""

import customtkinter as ctk
from ..theme import COLORS


class ViewerToolbarMixin:
    """Mixin providing common toolbar UI pattern for viewer widgets.

    This mixin reduces code duplication across ConversationViewer, ReportViewer,
    and CoverageViewer by providing shared toolbar building logic.

    Subclasses should call _build_toolbar() and then add any custom controls
    to the returned inner frame.
    """

    def _build_toolbar(
        self,
        label_text: str,
        placeholder_text: str,
        browse_callback,
        status_text: str = "No data",
    ):
        """Build the common toolbar with file entry and browse button.

        Args:
            label_text: Label text shown before the file entry (e.g., "📁 Load:")
            placeholder_text: Placeholder text for the file entry
            browse_callback: Callback function for the browse button
            status_text: Initial status label text

        Returns:
            CTkFrame: The inner frame for adding additional controls
        """
        bar = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"], corner_radius=12, height=60
        )
        bar.pack(fill="x", pady=(0, 16))
        bar.pack_propagate(False)

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        # Label
        ctk.CTkLabel(
            inner,
            text=label_text,
            font=ctk.CTkFont(size=17),
            text_color=COLORS["text_secondary"],
        ).pack(side="left")

        # File entry
        self.file_entry = ctk.CTkEntry(
            inner,
            placeholder_text=placeholder_text,
            width=350,
            height=36,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
        )
        self.file_entry.pack(side="left", padx=8)

        # Browse button
        ctk.CTkButton(
            inner,
            text="Browse",
            width=70,
            height=36,
            fg_color=COLORS["button_primary"],
            hover_color=COLORS["button_hover"],
            command=browse_callback,
        ).pack(side="left", padx=(0, 16))

        # Status label
        self.status = ctk.CTkLabel(
            inner,
            text=status_text,
            font=ctk.CTkFont(size=15),
            text_color=COLORS["text_muted"],
        )
        self.status.pack(side="right")

        return inner
