"""Performance graph widget for displaying metrics over iterations."""

import customtkinter as ctk
from ..theme import COLORS

# Try to import matplotlib for the graph
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    FigureCanvasTkAgg = None
    Figure = None
    MATPLOTLIB_AVAILABLE = False


class PerformanceGraph(ctk.CTkFrame):
    """Line chart showing coverage, security, and time over iterations."""

    LINES = [
        ("coverage_data", COLORS["accent_green"], "Coverage"),
        ("security_data", COLORS["accent_blue"], "Security"),
        ("time_data", COLORS["accent_red"], "Time (s)"),
    ]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_card"], corner_radius=12, **kwargs)
        self._init_data()
        self._build_ui()

    def _init_data(self):
        """Initialize data arrays."""
        self.iterations, self.coverage_data, self.security_data, self.time_data = (
            [],
            [],
            [],
            [],
        )

    def _build_ui(self):
        """Build the graph UI."""
        ctk.CTkLabel(
            self,
            text="Performance Over Iterations",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=16, pady=(16, 8))

        if MATPLOTLIB_AVAILABLE:
            self._setup_matplotlib()
        else:
            self._setup_fallback()

    def _setup_matplotlib(self):
        """Setup matplotlib graph."""
        self.fig = Figure(figsize=(4, 2.5), dpi=100, facecolor=COLORS["bg_card"])
        self.ax = self.fig.add_subplot(111)
        self._style_axes()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(
            fill="both", expand=True, padx=16, pady=(0, 16)
        )

    def _style_axes(self):
        """Apply dark theme to axes."""
        self.ax.set_facecolor(COLORS["bg_card"])
        self.ax.tick_params(colors=COLORS["text_muted"], labelsize=8)
        for spine in ["bottom", "left"]:
            self.ax.spines[spine].set_color(COLORS["border"])
        for spine in ["top", "right"]:
            self.ax.spines[spine].set_visible(False)
        self.ax.set_xlabel("Iteration", color=COLORS["text_muted"], fontsize=9)
        self.ax.set_ylabel("Value", color=COLORS["text_muted"], fontsize=9)

    def _setup_fallback(self):
        """Fallback when matplotlib unavailable."""
        ctk.CTkLabel(
            self,
            text="📊 Install matplotlib for graphs\npip install matplotlib",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        ).pack(expand=True, pady=20)

    @staticmethod
    def _clamp(val, typ, min_v=0, max_v=None):
        """Validate and clamp a value to type and range."""
        try:
            val = typ(val) if val is not None else typ()
        except (TypeError, ValueError):
            val = typ()
        val = max(min_v, val)
        return min(max_v, val) if max_v is not None else val

    def add_data_point(
        self, iteration: int, coverage: float, security: int, exec_time: float
    ):
        """Add a data point and refresh."""
        self.iterations.append(self._clamp(iteration, int))
        self.coverage_data.append(self._clamp(coverage, float, 0, 100))
        self.security_data.append(self._clamp(security, int))
        self.time_data.append(self._clamp(exec_time, float))
        if MATPLOTLIB_AVAILABLE:
            self._refresh()

    def _refresh(self):
        """Redraw the graph."""
        self.ax.clear()
        self._style_axes()
        if self.iterations:
            for attr, color, label in self.LINES:
                self.ax.plot(
                    self.iterations,
                    getattr(self, attr),
                    color=color,
                    label=label,
                    linewidth=2,
                )
            self.ax.legend(
                loc="upper left",
                fontsize=7,
                facecolor=COLORS["bg_card"],
                edgecolor=COLORS["border"],
                labelcolor=COLORS["text_secondary"],
            )
        self.fig.tight_layout()
        self.canvas.draw()

    def reset(self):
        """Clear all data."""
        self._init_data()
        if MATPLOTLIB_AVAILABLE:
            self._refresh()
