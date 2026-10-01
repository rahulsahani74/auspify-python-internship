"""
Database persistence layer for the Expense Tracker System.

Implements SQLite repository management, schema migrations, parameterized queries,
indexed lookups, and transaction safety.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.models import DEFAULT_CATEGORIES, Expense, current_date_str


DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DB_FILE = DEFAULT_DATA_DIR / "expenses.db"


class Database:
    """Manages SQLite storage and aggregations for financial expense records."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_FILE):
        """Initialize database connection and ensure schema is present.

        Args:
            db_path: Path to SQLite database file or ':memory:' for tests.
        """
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Create tables and performance indices if they do not exist."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                payment_method TEXT DEFAULT 'Cash',
                created_at TEXT NOT NULL
            );
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);")
        self.conn.commit()

    # --- CRUD Operations ---

    def add_expense(self, expense: Expense) -> Expense:
        """Insert an expense record into the database.

        Args:
            expense: Expense instance.

        Returns:
            The persisted Expense instance with assigned database ID.

        Raises:
            ValueError: If expense validation fails.
        """
        errors = expense.validate()
        if errors:
            raise ValueError("; ".join(errors))

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO expenses (date, amount, category, description, payment_method, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                expense.date.strip(),
                round(float(expense.amount), 2),
                expense.category.strip(),
                expense.description.strip(),
                expense.payment_method.strip(),
                expense.created_at,
            ),
        )
        self.conn.commit()
        expense.id = cursor.lastrowid
        return expense

    def get_expense(self, expense_id: int) -> Optional[Expense]:
        """Fetch a single expense by its primary key ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?;", (expense_id,))
        row = cursor.fetchone()
        return Expense.from_row(row) if row else None

    def get_all_expenses(self, order_desc: bool = True) -> List[Expense]:
        """Fetch all stored expenses ordered chronologically."""
        direction = "DESC" if order_desc else "ASC"
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM expenses ORDER BY date {direction}, id {direction};")
        return [Expense.from_row(r) for r in cursor.fetchall()]

    def update_expense(self, expense: Expense) -> bool:
        """Update an existing expense record.

        Args:
            expense: Expense instance with valid id.

        Returns:
            True if a row was updated, False if ID not found.

        Raises:
            ValueError: If validation fails or ID is missing.
        """
        if expense.id is None:
            raise ValueError("Cannot update an expense without an ID.")

        errors = expense.validate()
        if errors:
            raise ValueError("; ".join(errors))

        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE expenses
            SET date = ?, amount = ?, category = ?, description = ?, payment_method = ?
            WHERE id = ?;
            """,
            (
                expense.date.strip(),
                round(float(expense.amount), 2),
                expense.category.strip(),
                expense.description.strip(),
                expense.payment_method.strip(),
                expense.id,
            ),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_expense(self, expense_id: int) -> bool:
        """Permanently delete an expense record by ID."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?;", (expense_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # --- Filtering and Queries ---

    def filter_expenses(
        self,
        category: Optional[str] = None,
        month: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[Expense]:
        """Filter expenses using safe parameterized SQL criteria."""
        clauses: List[str] = []
        params: List[Any] = []

        if category and category.lower() != "all categories":
            clauses.append("category = ?")
            params.append(category.strip())

        if month and month.lower() != "all months":
            clauses.append("date LIKE ?")
            params.append(f"{month.strip()}%")

        if start_date:
            clauses.append("date >= ?")
            params.append(start_date.strip())

        if end_date:
            clauses.append("date <= ?")
            params.append(end_date.strip())

        if search_query:
            query_pattern = f"%{search_query.strip()}%"
            clauses.append("(description LIKE ? OR category LIKE ?)")
            params.extend([query_pattern, query_pattern])

        where_stmt = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM expenses {where_stmt} ORDER BY date DESC, id DESC;"

        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return [Expense.from_row(r) for r in cursor.fetchall()]

    def get_categories(self) -> List[str]:
        """Return combined list of standard categories and any user-custom categories."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM expenses WHERE category != '' ORDER BY category ASC;")
        db_cats = [r[0] for r in cursor.fetchall()]

        # Combine defaults and custom categories preserving distinct order
        combined = list(DEFAULT_CATEGORIES)
        for cat in db_cats:
            if cat not in combined:
                combined.append(cat)
        return combined

    def get_distinct_months(self) -> List[str]:
        """Return list of distinct 'YYYY-MM' periods in descending order."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT substr(date, 1, 7) FROM expenses WHERE date != '' ORDER BY 1 DESC;")
        return [r[0] for r in cursor.fetchall() if r[0]]

    # --- Aggregations & Analytics ---

    def get_total_spending(self, month: Optional[str] = None) -> float:
        """Calculate total spending amount, optionally filtered by 'YYYY-MM'."""
        cursor = self.conn.cursor()
        if month:
            cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM expenses WHERE date LIKE ?;", (f"{month}%",))
        else:
            cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM expenses;")
        row = cursor.fetchone()
        return round(float(row[0]), 2) if row else 0.0

    def get_category_breakdown(self, month: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return breakdown of spending per category with totals and percentages.

        Returns:
            List of dicts: [{'category': str, 'total': float, 'count': int, 'percentage': float}]
        """
        cursor = self.conn.cursor()
        if month:
            sql = """
                SELECT category, SUM(amount) AS total, COUNT(*) AS count
                FROM expenses
                WHERE date LIKE ?
                GROUP BY category
                ORDER BY total DESC;
            """
            cursor.execute(sql, (f"{month}%",))
        else:
            sql = """
                SELECT category, SUM(amount) AS total, COUNT(*) AS count
                FROM expenses
                GROUP BY category
                ORDER BY total DESC;
            """
            cursor.execute(sql)

        rows = cursor.fetchall()
        grand_total = sum(r["total"] for r in rows) if rows else 0.0

        results = []
        for r in rows:
            amt = round(float(r["total"]), 2)
            pct = round((amt / grand_total * 100), 1) if grand_total > 0 else 0.0
            results.append({
                "category": r["category"],
                "total": amt,
                "count": int(r["count"]),
                "percentage": pct,
            })
        return results

    def get_monthly_history(self) -> List[Dict[str, Any]]:
        """Return chronological monthly totals for reports."""
        sql = """
            SELECT substr(date, 1, 7) AS month, SUM(amount) AS total, COUNT(*) AS count
            FROM expenses
            GROUP BY month
            ORDER BY month DESC;
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return [
            {
                "month": r["month"],
                "total": round(float(r["total"]), 2),
                "count": int(r["count"]),
            }
            for r in cursor.fetchall()
        ]

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Compute top-level dashboard metrics in a single coordinated query."""
        today = current_date_str()
        current_month = today[:7]

        cursor = self.conn.cursor()

        # Grand totals, count, avg, max
        cursor.execute("SELECT COALESCE(SUM(amount), 0.0), COUNT(*), COALESCE(AVG(amount), 0.0), COALESCE(MAX(amount), 0.0) FROM expenses;")
        total_spent, count, avg_spent, max_spent = cursor.fetchone()

        # Today's total
        cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM expenses WHERE date = ?;", (today,))
        today_spent = cursor.fetchone()[0]

        # Current Month's total
        cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM expenses WHERE date LIKE ?;", (f"{current_month}%",))
        month_spent = cursor.fetchone()[0]

        return {
            "total_spent": round(float(total_spent), 2),
            "total_transactions": int(count),
            "avg_expense": round(float(avg_spent), 2),
            "highest_expense": round(float(max_spent), 2),
            "today_spent": round(float(today_spent), 2),
            "this_month_spent": round(float(month_spent), 2),
        }

    def close(self) -> None:
        """Close SQLite database connection cleanly."""
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
