"""Main expense tracker application."""

import tkinter as tk
from tkinter import ttk

from config import APP_TITLE, CATEGORIES, COLORS, PAYMENT_METHODS
from models import Expense, ExpenseStorage
from widgets import ExpenseCard, StyledButton, StyledEntry, SummaryPanel


class ExpenseApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("1100x750")
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(900, 600)

        self._setup_styles()
        self.storage = ExpenseStorage()
        self.filter_category = tk.StringVar(value="All")
        self._build_ui()
        self._refresh()

    def _setup_styles(self):
        """Configure ttk styles for dark theme."""
        style = ttk.Style()
        style.theme_use("clam")

        # Combobox styling
        style.configure(
            "TCombobox",
            fieldbackground=COLORS["card"],
            background=COLORS["card"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["text"],
            borderwidth=0,
            padding=8,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORS["card"])],
            selectbackground=[("readonly", COLORS["accent"])],
            selectforeground=[("readonly", COLORS["text"])],
        )

        # Dropdown listbox styling
        self.root.option_add("*TCombobox*Listbox.background", COLORS["card"])
        self.root.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLORS["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", COLORS["text"])

    def _build_ui(self):
        # Left panel - summary
        left = tk.Frame(self.root, bg=COLORS["bg"], width=280)
        left.pack(side="left", fill="y", padx=30, pady=30)
        left.pack_propagate(False)

        self.summary = SummaryPanel(left)
        self.summary.pack(fill="x")

        # Right panel - main content
        right = tk.Frame(self.root, bg=COLORS["bg"])
        right.pack(side="right", fill="both", expand=True, padx=(0, 30), pady=30)

        self._build_form(right)
        self._build_list(right)

    def _build_form(self, parent):
        form = tk.Frame(parent, bg=COLORS["card"], padx=24, pady=20)
        form.pack(fill="x", pady=(0, 20))

        # Title
        tk.Label(
            form,
            text="Add New Entry",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["card"],
            fg=COLORS["text"],
        ).pack(anchor="w", pady=(0, 16))

        # Row 1: Amount + Category + Payment + Income
        row1 = tk.Frame(form, bg=COLORS["card"])
        row1.pack(fill="x", pady=(0, 12))

        self.amount_entry = StyledEntry(row1, "Amount ($)", width=15)
        self.amount_entry.pack(side="left", padx=(0, 16))

        cat_frame = tk.Frame(row1, bg=COLORS["card"])
        cat_frame.pack(side="left", padx=(0, 16))
        tk.Label(
            cat_frame,
            text="Category",
            bg=COLORS["card"],
            fg=COLORS["text_secondary"],
            font=("Segoe UI", 9),
        ).pack(anchor="w")
        self.category_var = tk.StringVar(value="Food")
        self.category_combo = ttk.Combobox(
            cat_frame,
            textvariable=self.category_var,
            values=list(CATEGORIES.keys()),
            state="readonly",
            width=16,
            font=("Segoe UI", 10),
        )
        self.category_combo.pack(ipady=2)

        pay_frame = tk.Frame(row1, bg=COLORS["card"])
        pay_frame.pack(side="left", padx=(0, 16))
        tk.Label(
            pay_frame,
            text="Payment",
            bg=COLORS["card"],
            fg=COLORS["text_secondary"],
            font=("Segoe UI", 9),
        ).pack(anchor="w")
        self.payment_var = tk.StringVar(value="Card")
        self.payment_combo = ttk.Combobox(
            pay_frame,
            textvariable=self.payment_var,
            values=PAYMENT_METHODS,
            state="readonly",
            width=12,
            font=("Segoe UI", 10),
        )
        self.payment_combo.pack(ipady=2)

        # Income checkbox with better styling
        income_frame = tk.Frame(row1, bg=COLORS["card"])
        income_frame.pack(side="left", padx=(8, 0))
        self.income_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            income_frame,
            text="💰 Income",
            variable=self.income_var,
            bg=COLORS["card"],
            fg=COLORS["income"],
            selectcolor=COLORS["bg"],
            activebackground=COLORS["card"],
            activeforeground=COLORS["income"],
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=(18, 0))

        # Row 2: Description + Add button
        row2 = tk.Frame(form, bg=COLORS["card"])
        row2.pack(fill="x")

        self.desc_entry = StyledEntry(row2, "Description", width=50)
        self.desc_entry.pack(side="left", fill="x", expand=True, padx=(0, 16))

        btn_frame = tk.Frame(row2, bg=COLORS["card"])
        btn_frame.pack(side="right", pady=(16, 0))
        StyledButton(btn_frame, "➕ Add", self._add_expense, width=100).pack()

    def _build_list(self, parent):
        # Header with filter
        header = tk.Frame(parent, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 12))

        tk.Label(
            header,
            text="Recent Transactions",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"],
        ).pack(side="left")

        filter_frame = tk.Frame(header, bg=COLORS["bg"])
        filter_frame.pack(side="right")
        tk.Label(
            filter_frame,
            text="Filter:",
            bg=COLORS["bg"],
            fg=COLORS["text_secondary"],
            font=("Segoe UI", 10),
        ).pack(side="left", padx=(0, 8))
        filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_category,
            values=["All"] + list(CATEGORIES.keys()),
            state="readonly",
            width=16,
            font=("Segoe UI", 10),
        )
        filter_combo.pack(side="left")
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        # Scrollable list container
        container = tk.Frame(parent, bg=COLORS["bg"])
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(
            container,
            orient="vertical",
            command=self.canvas.yview,
            bg=COLORS["card"],
            troughcolor=COLORS["bg"],
            activebackground=COLORS["accent"],
        )
        self.list_frame = tk.Frame(self.canvas, bg=COLORS["bg"])

        self.list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.list_frame, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Resize list frame width with canvas
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel scroll
        self.canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _add_expense(self):
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            return

        expense = Expense.create(
            amount=amount,
            category=self.category_var.get(),
            description=self.desc_entry.get(),
            payment_method=self.payment_var.get(),
            is_income=self.income_var.get(),
        )
        self.storage.add(expense)
        self.amount_entry.clear()
        self.desc_entry.clear()
        self._refresh()

    def _delete_expense(self, expense_id):
        self.storage.delete(expense_id)
        self._refresh()

    def _refresh(self):
        # Clear list
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        # Populate list
        expenses = self.storage.filter_by_category(self.filter_category.get())
        for expense in expenses:
            card = ExpenseCard(self.list_frame, expense, self._delete_expense)
            card.pack(fill="x", pady=6, padx=4)

        if not expenses:
            empty = tk.Frame(self.list_frame, bg=COLORS["card"], padx=40, pady=60)
            empty.pack(fill="x", pady=20)
            tk.Label(
                empty, text="📋", font=("Segoe UI Emoji", 40), bg=COLORS["card"]
            ).pack()
            tk.Label(
                empty,
                text="No transactions yet",
                font=("Segoe UI", 14),
                bg=COLORS["card"],
                fg=COLORS["text_secondary"],
            ).pack(pady=(8, 0))
            tk.Label(
                empty,
                text="Add your first expense or income above",
                font=("Segoe UI", 10),
                bg=COLORS["card"],
                fg=COLORS["text_secondary"],
            ).pack()

        # Update summary
        income, expenses_total, balance = self.storage.get_summary()
        self.summary.update(income, expenses_total, balance)

    def run(self):
        self.root.mainloop()
