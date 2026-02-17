"""Data models and storage for expenses."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List

from config import DATA_FILE


@dataclass
class Expense:
    id: str
    amount: float
    category: str
    description: str
    date: str
    payment_method: str
    is_income: bool = False

    @classmethod
    def create(
        cls,
        amount: float,
        category: str,
        description: str,
        payment_method: str,
        is_income: bool = False,
    ):
        return cls(
            id=datetime.now().strftime("%Y%m%d%H%M%S%f"),
            amount=amount,
            category=category,
            description=description,
            date=datetime.now().strftime("%Y-%m-%d"),
            payment_method=payment_method,
            is_income=is_income,
        )


class ExpenseStorage:
    def __init__(self):
        self.path = Path(__file__).parent / DATA_FILE
        self.expenses: List[Expense] = self._load()

    def _load(self) -> List[Expense]:
        if self.path.exists():
            data = json.loads(self.path.read_text())
            return [Expense(**e) for e in data]
        return []

    def save(self):
        self.path.write_text(json.dumps([asdict(e) for e in self.expenses], indent=2))

    def add(self, expense: Expense):
        self.expenses.insert(0, expense)
        self.save()

    def delete(self, expense_id: str):
        self.expenses = [e for e in self.expenses if e.id != expense_id]
        self.save()

    def filter_by_category(self, category: str) -> List[Expense]:
        if category == "All":
            return self.expenses
        return [e for e in self.expenses if e.category == category]

    def get_summary(self):
        income = sum(e.amount for e in self.expenses if e.is_income)
        expenses = sum(e.amount for e in self.expenses if not e.is_income)
        return income, expenses, income - expenses
