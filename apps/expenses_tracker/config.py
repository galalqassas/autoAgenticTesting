"""Configuration: colors, categories, and app settings."""

# Color palette (researched for finance apps)
COLORS = {
    "bg": "#1E2A3A",
    "card": "#303F50",
    "text": "#E0E0E0",
    "text_secondary": "#A0A0A0",
    "income": "#4CAF50",
    "expense": "#EF5350",
    "accent": "#8E7CC3",
    "border": "#444444",
    "hover": "#3D4F63",
}

# Categories with emojis
CATEGORIES = {
    "Food": "🍔",
    "Transport": "🚗",
    "Shopping": "🛒",
    "Bills": "📄",
    "Entertainment": "🎬",
    "Health": "💊",
    "Income": "💰",
    "Other": "📌",
}

# Payment methods
PAYMENT_METHODS = ["Cash", "Card", "Transfer", "Other"]

# App settings
APP_TITLE = "Expense Tracker"
DATA_FILE = "expenses.json"
