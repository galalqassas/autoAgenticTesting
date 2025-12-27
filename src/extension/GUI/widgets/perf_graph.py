"""Performance graph widget for displaying coverage and time over iterations."""

import customtkinter as ctk
from ..theme import COLORS

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    FigureCanvasTkAgg = Figure = None
    MATPLOTLIB_AVAILABLE = False


class PerformanceGraph(ctk.CTkFrame):
    """Dual-axis chart: Coverage % (left), Time seconds (right)."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_card"], corner_radius=12, **kwargs)
        self.data = []
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self,
            text="Performance Over Iterations",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=16, pady=(16, 8))

        if not MATPLOTLIB_AVAILABLE:
            ctk.CTkLabel(
                self,
                text="📊 pip install matplotlib",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_muted"],
            ).pack(expand=True, pady=20)
            return

        self.fig = Figure(figsize=(5, 2.2), dpi=100, facecolor=COLORS["bg_card"])
        self.ax = self.fig.add_subplot(111)
        self.ax2 = self.ax.twinx()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(
            fill="both", expand=True, padx=16, pady=(0, 12)
        )
        self._refresh()

    def _style_axes(self):
        """Apply styling to both axes."""
        bg = COLORS["bg_card"]
        self.ax.set_facecolor(bg)
        self.ax2.set_facecolor(bg)

        # Hide all spines except needed ones
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        for spine in self.ax2.spines.values():
            spine.set_visible(False)

        # Left axis (Coverage) - green
        self.ax.spines["left"].set_visible(True)
        self.ax.spines["left"].set_color(COLORS["accent_green"])
        self.ax.spines["bottom"].set_visible(True)
        self.ax.spines["bottom"].set_color(COLORS["border"])
        self.ax.tick_params(axis="y", colors=COLORS["accent_green"], labelsize=8)
        self.ax.tick_params(axis="x", colors=COLORS["text_muted"], labelsize=8)
        self.ax.set_ylabel("Coverage %", color=COLORS["accent_green"], fontsize=9)
        self.ax.set_xlabel("Iteration", color=COLORS["text_muted"], fontsize=9)
        self.ax.set_ylim(0, 105)

        # Right axis (Time) - red
        self.ax2.spines["right"].set_visible(True)
        self.ax2.spines["right"].set_color(COLORS["accent_red"])
        self.ax2.tick_params(axis="y", colors=COLORS["accent_red"], labelsize=8)
        self.ax2.yaxis.set_label_position("right")
        self.ax2.yaxis.tick_right()
        self.ax2.set_ylabel(
            "Time (s)",
            color=COLORS["accent_red"],
            fontsize=9,
            rotation=270,
            labelpad=12,
        )

    def add_point(self, iteration: int, coverage: float, exec_time: float = 0.0):
        """Add or update a data point."""
        coverage, exec_time = max(0, min(100, coverage)), max(0, exec_time)
        for i, (it, _, _) in enumerate(self.data):
            if it == iteration:
                self.data[i] = (iteration, coverage, exec_time)
                break
        else:
            self.data.append((iteration, coverage, exec_time))
        self.data.sort(key=lambda x: x[0])
        if MATPLOTLIB_AVAILABLE:
            self._refresh()

    def _refresh(self):
        self.ax.clear()
        self.ax2.clear()
        self._style_axes()

        if not self.data:
            self.ax.set_xlim(0, 1)
            self.ax.set_xticks([])
            self.fig.tight_layout()
            self.canvas.draw()
            return

        iters, covs, times = zip(*self.data)

        # Plot coverage (green, left)
        self.ax.plot(
            iters,
            covs,
            color=COLORS["accent_green"],
            lw=2,
            marker="o",
            ms=5,
            label="Coverage %",
        )
        self.ax.fill_between(iters, covs, alpha=0.15, color=COLORS["accent_green"])

        # Plot time (red, right)
        self.ax2.plot(
            iters,
            times,
            color=COLORS["accent_red"],
            lw=2,
            marker="^",
            ms=5,
            label="Time (s)",
        )
        self.ax2.fill_between(iters, times, alpha=0.15, color=COLORS["accent_red"])

        # X-axis: integer ticks only
        self.ax.set_xticks(list(iters))
        if len(iters) == 1:
            self.ax.set_xlim(iters[0] - 0.5, iters[0] + 0.5)
        else:
            self.ax.set_xlim(min(iters) - 0.3, max(iters) + 0.3)

        # Combined legend
        h1, l1 = self.ax.get_legend_handles_labels()
        h2, l2 = self.ax2.get_legend_handles_labels()
        self.ax.legend(
            h1 + h2,
            l1 + l2,
            loc="lower right",
            fontsize=7,
            facecolor=COLORS["bg_card"],
            edgecolor=COLORS["border"],
            labelcolor=COLORS["text_secondary"],
        )

        self.fig.tight_layout()
        self.canvas.draw()

    def reset(self):
        self.data = []
        if MATPLOTLIB_AVAILABLE:
            self._refresh()
