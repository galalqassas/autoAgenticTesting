"""Reusable styled UI components."""

import tkinter as tk
from config import COLORS, CATEGORIES


class StyledButton(tk.Canvas):
    """Rounded button with hover effect."""

    def __init__(self, parent, text, command, width=100, height=40, bg=None):
        super().__init__(
            parent, width=width, height=height, bg=COLORS["card"], highlightthickness=0
        )
        self.bg = bg or COLORS["accent"]
        self.command = command
        self.text = text
        self._draw()
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))
        self.bind("<Button-1>", lambda e: self.command())

    def _draw(self, hover=False):
        self.delete("all")
        color = COLORS["hover"] if hover else self.bg
        h = 40
        r = h // 2
        w = self.winfo_reqwidth()
        self.create_oval(0, 0, h, h, fill=color, outline="")
        self.create_oval(w - h, 0, w, h, fill=color, outline="")
        self.create_rectangle(r, 0, w - r, h, fill=color, outline="")
        self.create_text(
            w // 2,
            h // 2,
            text=self.text,
            fill=COLORS["text"],
            font=("Segoe UI", 11, "bold"),
        )

    def _hover(self, state):
        self._draw(state)


class StyledEntry(tk.Frame):
    """Entry with label and styling."""

    def __init__(self, parent, label, width=20):
        super().__init__(parent, bg=COLORS["card"])
        tk.Label(
            self,
            text=label,
            bg=COLORS["card"],
            fg=COLORS["text_secondary"],
            font=("Segoe UI", 9),
        ).pack(anchor="w")
        self.entry = tk.Entry(
            self,
            width=width,
            bg=COLORS["bg"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            font=("Segoe UI", 11),
            highlightthickness=1,
            highlightcolor=COLORS["accent"],
            highlightbackground=COLORS["border"],
        )
        self.entry.pack(fill="x", ipady=8)

    def get(self):
        return self.entry.get()

    def clear(self):
        self.entry.delete(0, "end")


class ExpenseCard(tk.Frame):
    """Card displaying expense details with hover effect."""

    def __init__(self, parent, expense, on_delete):
        super().__init__(parent, bg=COLORS["card"], padx=20, pady=16)
        self.expense = expense
        self.on_delete = on_delete
        self._build()
        # Bind hover to all children
        self._bind_hover(self)

    def _bind_hover(self, widget):
        widget.bind("<Enter>", lambda e: self._set_bg(COLORS["hover"]))
        widget.bind("<Leave>", lambda e: self._set_bg(COLORS["card"]))
        for child in widget.winfo_children():
            self._bind_hover(child)

    def _set_bg(self, color):
        self.config(bg=color)
        self._update_children_bg(self, color)

    def _update_children_bg(self, widget, color):
        for child in widget.winfo_children():
            try:
                child.config(bg=color)
            except tk.TclError:
                pass
            self._update_children_bg(child, color)

    def _build(self):
        # Left: emoji + info
        left = tk.Frame(self, bg=COLORS["card"])
        left.pack(side="left", fill="both", expand=True)

        # Category emoji in circle
        emoji_frame = tk.Frame(left, bg=COLORS["bg"], width=50, height=50)
        emoji_frame.pack(side="left", padx=(0, 16))
        emoji_frame.pack_propagate(False)
        emoji = CATEGORIES.get(self.expense.category, "📌")
        tk.Label(
            emoji_frame, text=emoji, font=("Segoe UI Emoji", 20), bg=COLORS["bg"]
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Info column
        info = tk.Frame(left, bg=COLORS["card"])
        info.pack(side="left", fill="both")

        desc_text = self.expense.description or self.expense.category
        tk.Label(
            info,
            text=desc_text,
            font=("Segoe UI", 13, "bold"),
            bg=COLORS["card"],
            fg=COLORS["text"],
        ).pack(anchor="w")

        meta = f"{self.expense.category} • {self.expense.date} • {self.expense.payment_method}"
        tk.Label(
            info,
            text=meta,
            font=("Segoe UI", 10),
            bg=COLORS["card"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w")

        # Right: amount + delete
        right = tk.Frame(self, bg=COLORS["card"])
        right.pack(side="right")

        sign = "+" if self.expense.is_income else "-"
        color = COLORS["income"] if self.expense.is_income else COLORS["expense"]
        tk.Label(
            right,
            text=f"{sign}${self.expense.amount:.2f}",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS["card"],
            fg=color,
        ).pack(anchor="e")

        del_btn = tk.Label(
            right,
            text="🗑️",
            font=("Segoe UI Emoji", 12),
            bg=COLORS["card"],
            fg=COLORS["text_secondary"],
            cursor="hand2",
        )
        del_btn.pack(anchor="e", pady=(4, 0))
        del_btn.bind("<Button-1>", lambda e: self.on_delete(self.expense.id))


class SummaryPanel(tk.Frame):
    """Panel showing income/expense/balance summary."""

    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["card"], padx=24, pady=24)
        self.labels = {}
        self._build()

    def _build(self):
        # App title
        tk.Label(
            self,
            text="💳 Expense Tracker",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS["card"],
            fg=COLORS["text"],
        ).pack(anchor="w", pady=(0, 24))

        # Balance section
        tk.Label(
            self,
            text="Current Balance",
            font=("Segoe UI", 11),
            bg=COLORS["card"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w")
        self.labels["balance"] = tk.Label(
            self,
            text="$0.00",
            font=("Segoe UI", 36, "bold"),
            bg=COLORS["card"],
            fg=COLORS["text"],
        )
        self.labels["balance"].pack(anchor="w", pady=(0, 24))

        # Divider
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x", pady=8)

        # Income/Expense rows
        for key, label, color, icon in [
            ("income", "Total Income", COLORS["income"], "📈"),
            ("expense", "Total Expenses", COLORS["expense"], "📉"),
        ]:
            frame = tk.Frame(self, bg=COLORS["card"])
            frame.pack(fill="x", pady=8)
            tk.Label(
                frame,
                text=f"{icon} {label}",
                font=("Segoe UI", 11),
                bg=COLORS["card"],
                fg=COLORS["text_secondary"],
            ).pack(side="left")
            self.labels[key] = tk.Label(
                frame,
                text="$0.00",
                font=("Segoe UI", 14, "bold"),
                bg=COLORS["card"],
                fg=color,
            )
            self.labels[key].pack(side="right")

    def update(self, income, expenses, balance):
        self.labels["income"].config(text=f"+${income:.2f}")
        self.labels["expense"].config(text=f"-${expenses:.2f}")
        color = COLORS["income"] if balance >= 0 else COLORS["expense"]
        sign = "+" if balance >= 0 else ""
        self.labels["balance"].config(text=f"{sign}${balance:.2f}", fg=color)
