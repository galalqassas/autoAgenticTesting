"""Agent flow widget for visualizing sequential agent interactions."""

import customtkinter as ctk
from ..theme import COLORS


class AgentFlow(ctk.CTkFrame):
    """Scrollable timeline showing agent activations: Agent 1 → Agent 2 → Agent 3 → ..."""

    AGENTS = {
        1: ("Identify", "🔍"),
        2: ("Implement", "⚙️"),
        3: ("Verify", "✓"),
    }

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", height=100, **kwargs)
        self.pack_propagate(False)
        self._nodes = []
        self._build_ui()
        self.bind("<Configure>", self._check_scrollbar)

    def _build_ui(self):
        """Build scrollable container with auto-hide scrollbar."""
        self.canvas = ctk.CTkCanvas(
            self, bg=COLORS["bg_dark"], highlightthickness=0, height=80
        )
        self.scrollbar = ctk.CTkScrollbar(
            self, orientation="horizontal", command=self.canvas.xview, height=10
        )
        self.container = ctk.CTkFrame(self.canvas, fg_color="transparent")

        self.canvas.configure(xscrollcommand=self.scrollbar.set)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.container, anchor="nw"
        )
        self.canvas.pack(fill="both", expand=True)
        # Scrollbar hidden initially
        self.container.bind("<Configure>", self._on_container_configure)

    def _on_container_configure(self, event=None):
        """Update scroll region and check if scrollbar needed."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._check_scrollbar()

    def _check_scrollbar(self, event=None):
        """Show scrollbar only when content overflows."""
        self.update_idletasks()
        content_width = self.container.winfo_reqwidth()
        canvas_width = self.canvas.winfo_width()
        if content_width > canvas_width and canvas_width > 1:
            self.scrollbar.pack(side="bottom", fill="x")
        else:
            self.scrollbar.pack_forget()

    def add_agent(self, agent_num: int):
        """Add an agent node to the flow."""
        if agent_num not in self.AGENTS:
            return

        # Mark previous node as completed
        if self._nodes:
            self._set_node_state(self._nodes[-1], "completed")

        # Add connector arrow (centered with icon)
        if self._nodes:
            arrow = ctk.CTkFrame(self.container, fg_color="transparent")
            arrow.pack(side="left", padx=2)
            ctk.CTkLabel(
                arrow, text="→", font=ctk.CTkFont(size=18, weight="bold"),
                text_color=COLORS["border"]
            ).pack(pady=(0, 18))  # Offset to align with icon center

        # Create new node
        label, icon = self.AGENTS[agent_num]
        node = self._create_node(label, icon)
        node.pack(side="left", padx=4)
        self._nodes.append(node)
        self._set_node_state(node, "active")

    def _create_node(self, label: str, icon: str) -> ctk.CTkFrame:
        """Create a single agent node."""
        frame = ctk.CTkFrame(self.container, fg_color="transparent")

        icon_frame = ctk.CTkFrame(
            frame, width=40, height=40, corner_radius=20,
            fg_color=COLORS["bg_card"], border_width=2, border_color=COLORS["border"]
        )
        icon_frame.pack(pady=(0, 4))
        icon_frame.pack_propagate(False)

        icon_label = ctk.CTkLabel(
            icon_frame, text=icon, font=ctk.CTkFont(size=16),
            text_color=COLORS["text_muted"]
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        text_label = ctk.CTkLabel(
            frame, text=label, font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        )
        text_label.pack()

        frame.icon_frame = icon_frame
        frame.icon_label = icon_label
        frame.text_label = text_label
        frame.original_icon = icon
        return frame

    def _set_node_state(self, node, state: str):
        """Set node state: active or completed."""
        if state == "active":
            node.icon_frame.configure(border_color=COLORS["accent_green"])
            node.icon_label.configure(text_color=COLORS["accent_green"])
            node.text_label.configure(text_color=COLORS["accent_green"])
        elif state == "completed":
            node.icon_frame.configure(
                fg_color=COLORS["accent_green"], border_color=COLORS["accent_green"]
            )
            node.icon_label.configure(text="✓", text_color=COLORS["text_primary"])
            node.text_label.configure(text_color=COLORS["accent_green"])

    def show_end(self):
        """Show end marker with flag icon."""
        if self._nodes:
            self._set_node_state(self._nodes[-1], "completed")

        # Arrow
        arrow = ctk.CTkFrame(self.container, fg_color="transparent")
        arrow.pack(side="left", padx=2)
        ctk.CTkLabel(
            arrow, text="→", font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["border"]
        ).pack(pady=(0, 18))

        # End icon node
        end_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        end_frame.pack(side="left", padx=4)

        icon_frame = ctk.CTkFrame(
            end_frame, width=40, height=40, corner_radius=20,
            fg_color=COLORS["accent_green"], border_width=2, border_color=COLORS["accent_green"]
        )
        icon_frame.pack(pady=(0, 4))
        icon_frame.pack_propagate(False)

        ctk.CTkLabel(
            icon_frame, text="✓", font=ctk.CTkFont(size=16),
            text_color=COLORS["text_primary"]
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            end_frame, text="Done", font=ctk.CTkFont(size=10),
            text_color=COLORS["accent_green"]
        ).pack()

    def reset(self):
        """Clear all nodes."""
        for widget in self.container.winfo_children():
            widget.destroy()
        self._nodes = []
