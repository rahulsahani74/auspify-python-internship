"""
Data models and validation rules for the Expense Tracker System.

Defines the Expense dataclass, category constants, payment methods,
and strict attribute validation helpers.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence


DEFAULT_CATEGORIES: Sequence[str] = (
    "Food & Dining",
    "Transportation",
    "Housing & Utilities",
    "Entertainment",
    "Healthcare",
    "Shopping",
    "Education",
    "Miscellaneous",
)

PAYMENT_METHODS: Sequence[str] = (
    "Cash",
    "Credit Card",
    "Debit Card",
    "UPI / Mobile",
    "Net Banking",
    "Other",
)

CURRENCY_SYMBOL = "₹"


def validate_date_format(date_str: str) -> bool:
    """Validate if date string strictly follows 'YYYY-MM-DD'."""
    if not date_str or not isinstance(date_str, str):
        return False
    try:
        parsed = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        # Ensure year is reasonable (between 2000 and 2100)
        return 2000 <= parsed.year <= 2100
    except ValueError:
        return False


def current_date_str() -> str:
    """Return today's date formatted as 'YYYY-MM-DD'."""
    return datetime.now().strftime("%Y-%m-%d")


def current_timestamp_str() -> str:
    """Return current timestamp formatted as 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Expense:
    """Represents a single financial expense record.

    Attributes:
        id: Unique database primary key (None for new uncommitted records).
        date: Incurred date string formatted as 'YYYY-MM-DD'.
        amount: Numerical monetary value (must be > 0.0).
        category: Expense classification.
        description: Brief description or memo.
        payment_method: Mode of transaction ('Cash', 'Credit Card', 'UPI', etc.).
        created_at: Audit timestamp when the record was created.
    """

    date: str
    amount: float
    category: str = "Miscellaneous"
    description: str = ""
    payment_method: str = "Cash"
    id: Optional[int] = None
    created_at: str = field(default_factory=current_timestamp_str)

    def validate(self) -> List[str]:
        """Validate expense fields and return a list of error descriptions.

        Returns:
            List of human-readable error messages. Empty list indicates validity.
        """
        errors: List[str] = []

        # Validate Date
        if not validate_date_format(self.date):
            errors.append(
                f"Invalid date '{self.date}'. Must follow 'YYYY-MM-DD' format (e.g. 2026-10-15)."
            )

        # Validate Amount
        if not isinstance(self.amount, (int, float)):
            errors.append(f"Expense amount must be a number, got {type(self.amount).__name__}.")
        elif self.amount <= 0.0:
            errors.append(f"Expense amount must be strictly greater than 0, got {self.amount:.2f}.")
        elif self.amount > 10_000_000.0:
            errors.append(f"Expense amount exceeds maximum allowable limit of 10,000,000.00.")

        # Validate Category
        cleaned_cat = self.category.strip() if isinstance(self.category, str) else ""
        if not cleaned_cat:
            errors.append("Category cannot be empty.")
        elif len(cleaned_cat) > 50:
            errors.append("Category name exceeds maximum length of 50 characters.")

        # Validate Description
        cleaned_desc = self.description.strip() if isinstance(self.description, str) else ""
        if not cleaned_desc:
            errors.append("Description cannot be empty.")
        elif len(cleaned_desc) > 250:
            errors.append("Description exceeds maximum length of 250 characters.")

        # Validate Payment Method
        cleaned_pm = self.payment_method.strip() if isinstance(self.payment_method, str) else ""
        if not cleaned_pm:
            self.payment_method = "Cash"

        return errors

    @property
    def formatted_amount(self) -> str:
        """Formatted monetary value with currency symbol (e.g. '₹ 250.00')."""
        return f"{CURRENCY_SYMBOL} {self.amount:,.2f}"

    @property
    def month_str(self) -> str:
        """Return the 'YYYY-MM' period string."""
        return self.date[:7] if len(self.date) >= 7 else ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize expense to dictionary."""
        return {
            "id": self.id,
            "date": self.date.strip(),
            "amount": round(float(self.amount), 2),
            "category": self.category.strip(),
            "description": self.description.strip(),
            "payment_method": self.payment_method.strip(),
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: Any) -> "Expense":
        """Deserialize database row or mapping to Expense instance.

        Supports sqlite3.Row, tuple, and dict objects.
        """
        if isinstance(row, dict):
            return cls(
                id=int(row["id"]) if row.get("id") is not None else None,
                date=str(row.get("date", current_date_str())),
                amount=float(row.get("amount", 0.0)),
                category=str(row.get("category", "Miscellaneous")),
                description=str(row.get("description", "")),
                payment_method=str(row.get("payment_method", "Cash")),
                created_at=str(row.get("created_at", current_timestamp_str())),
            )

        # Assume tuple / sqlite3.Row: (id, date, amount, category, description, payment_method, created_at)
        return cls(
            id=int(row[0]) if row[0] is not None else None,
            date=str(row[1]),
            amount=float(row[2]),
            category=str(row[3]),
            description=str(row[4]),
            payment_method=str(row[5]) if len(row) > 5 and row[5] else "Cash",
            created_at=str(row[6]) if len(row) > 6 and row[6] else current_timestamp_str(),
        )
