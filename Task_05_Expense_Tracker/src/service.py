"""
Service layer for the Expense Tracker System.

Implements business workflows, financial analytics, monthly report synthesis,
CSV data interchange, and transaction validation.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.database import Database
from src.models import Expense, current_date_str


class ExpenseService:
    """Provides high-level business operations and reporting on expenses."""

    def __init__(self, db: Optional[Database] = None):
        """Initialize service with a Database instance.

        Args:
            db: Database instance. If None, default storage is used.
        """
        self.db = db or Database()

    def add_expense(
        self,
        date: str,
        amount: float,
        category: str = "Miscellaneous",
        description: str = "",
        payment_method: str = "Cash",
    ) -> Expense:
        """Create and store a validated expense record."""
        expense = Expense(
            date=date.strip(),
            amount=round(float(amount), 2),
            category=category.strip(),
            description=description.strip(),
            payment_method=payment_method.strip(),
        )
        return self.db.add_expense(expense)

    def update_expense(
        self,
        expense_id: int,
        date: str,
        amount: float,
        category: str,
        description: str,
        payment_method: str = "Cash",
    ) -> Expense:
        """Update an existing expense record by ID."""
        existing = self.db.get_expense(expense_id)
        if existing is None:
            raise KeyError(f"Expense with ID {expense_id} not found.")

        updated = Expense(
            id=expense_id,
            date=date.strip(),
            amount=round(float(amount), 2),
            category=category.strip(),
            description=description.strip(),
            payment_method=payment_method.strip(),
            created_at=existing.created_at,
        )
        success = self.db.update_expense(updated)
        if not success:
            raise RuntimeError(f"Failed to update expense with ID {expense_id}.")
        return updated

    def delete_expense(self, expense_id: int) -> bool:
        """Remove an expense record by ID."""
        return self.db.delete_expense(expense_id)

    def get_expense(self, expense_id: int) -> Optional[Expense]:
        """Retrieve single expense by ID."""
        return self.db.get_expense(expense_id)

    def get_all_expenses(self) -> List[Expense]:
        """Retrieve all stored expenses."""
        return self.db.get_all_expenses()

    def filter_expenses(
        self,
        category: Optional[str] = None,
        month: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[Expense]:
        """Filter expenses by category, month ('YYYY-MM'), or search string."""
        return self.db.filter_expenses(
            category=category,
            month=month,
            search_query=search_query,
        )

    def get_categories(self) -> List[str]:
        """Return available categories."""
        return self.db.get_categories()

    def get_months(self) -> List[str]:
        """Return list of distinct YYYY-MM months recorded."""
        return self.db.get_distinct_months()

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Retrieve top-level spending statistics."""
        return self.db.get_analytics_summary()

    def get_monthly_report(self, target_month: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive monthly financial report.

        Args:
            target_month: 'YYYY-MM' period string. Defaults to current month.

        Returns:
            Dictionary with month metrics, category breakdown, daily average,
            and top spending categories.
        """
        month = target_month.strip() if target_month else current_date_str()[:7]
        total_spending = self.db.get_total_spending(month=month)
        category_breakdown = self.db.get_category_breakdown(month=month)
        expenses_in_month = self.db.filter_expenses(month=month)

        transaction_count = len(expenses_in_month)

        # Calculate daily average based on days in month or today's day if current month
        days_count = 30  # Standard normalization
        try:
            now = datetime.now()
            if month == now.strftime("%Y-%m"):
                days_count = max(1, now.day)
            else:
                # Approximate 30 days for past months
                days_count = 30
        except Exception:
            days_count = 30

        daily_avg = round(total_spending / days_count, 2) if total_spending > 0 else 0.0

        # Top 3 categories
        top_categories = category_breakdown[:3]

        # Highest single expense in this month
        highest_expense = max((e.amount for e in expenses_in_month), default=0.0)

        return {
            "month": month,
            "total_spending": total_spending,
            "transaction_count": transaction_count,
            "daily_average": daily_avg,
            "category_breakdown": category_breakdown,
            "top_categories": top_categories,
            "highest_expense": round(highest_expense, 2),
        }

    # --- CSV Export / Import ---

    def export_to_csv(
        self,
        filepath: Path | str,
        expenses: Optional[Sequence[Expense]] = None,
    ) -> int:
        """Export expense records to a CSV file.

        Args:
            filepath: Destination CSV file path.
            expenses: Optional subset of expenses. If None, exports all records.

        Returns:
            Number of rows exported.
        """
        records = expenses if expenses is not None else self.get_all_expenses()
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Date", "Category", "Amount", "Description", "Payment Method", "Created At"])
            for e in records:
                writer.writerow([
                    e.id,
                    e.date,
                    e.category,
                    f"{e.amount:.2f}",
                    e.description,
                    e.payment_method,
                    e.created_at,
                ])

        return len(records)

    def import_from_csv(self, filepath: Path | str) -> Tuple[int, List[str]]:
        """Import expense records from a CSV file.

        Returns:
            Tuple of (imported_count, list_of_error_warnings).
        """
        path = Path(filepath)
        if not path.exists():
            return 0, [f"File '{path.name}' does not exist."]

        imported = 0
        warnings: List[str] = []

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return 0, ["CSV file is empty."]

            for line_no, row in enumerate(reader, start=2):
                if not row or all(c.strip() == "" for c in row):
                    continue

                try:
                    # Expected standard columns: ID(optional), Date, Category, Amount, Description, Payment Method
                    if len(row) >= 5:
                        date_str = row[1].strip() if len(row) > 6 else row[0].strip()
                        cat_str = row[2].strip() if len(row) > 6 else row[1].strip()
                        amt_str = row[3].strip() if len(row) > 6 else row[2].strip()
                        desc_str = row[4].strip() if len(row) > 6 else row[3].strip()
                        pm_str = row[5].strip() if len(row) > 5 else "Cash"

                        amt = float(amt_str)
                        self.add_expense(
                            date=date_str,
                            amount=amt,
                            category=cat_str,
                            description=desc_str,
                            payment_method=pm_str,
                        )
                        imported += 1
                    else:
                        warnings.append(f"Row {line_no}: Insufficient columns.")
                except Exception as exc:
                    warnings.append(f"Row {line_no}: {exc}")

        return imported, warnings
