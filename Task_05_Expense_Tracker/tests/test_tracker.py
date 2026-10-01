"""
Comprehensive unit and integration test suite for Task 05: Personal Expense Tracker.

Tests models, database persistence, analytical reporting, validation rules,
CSV interchange, and GUI initialization.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import Database
from src.models import (
    CURRENCY_SYMBOL,
    DEFAULT_CATEGORIES,
    PAYMENT_METHODS,
    Expense,
    current_date_str,
    validate_date_format,
)
from src.service import ExpenseService


class TestExpenseModel(unittest.TestCase):
    """Unit tests for the Expense data model and validation helpers."""

    def test_valid_expense_creation(self):
        """Test valid expense initialization and properties."""
        exp = Expense(
            date="2026-10-15",
            amount=450.50,
            category="Food & Dining",
            description="Lunch with team",
            payment_method="UPI / Mobile",
        )
        self.assertEqual(exp.date, "2026-10-15")
        self.assertEqual(exp.amount, 450.50)
        self.assertEqual(exp.category, "Food & Dining")
        self.assertEqual(exp.description, "Lunch with team")
        self.assertEqual(exp.payment_method, "UPI / Mobile")
        self.assertEqual(exp.month_str, "2026-10")
        self.assertIn("450.50", exp.formatted_amount)
        self.assertEqual(exp.validate(), [])

    def test_date_validation_helper(self):
        """Test strict YYYY-MM-DD date validation."""
        self.assertTrue(validate_date_format("2026-10-01"))
        self.assertTrue(validate_date_format("2024-02-29"))  # Leap year
        self.assertFalse(validate_date_format("2026/10/01"))  # Slash delimiter
        self.assertFalse(validate_date_format("01-10-2026"))  # DD-MM-YYYY
        self.assertFalse(validate_date_format("2026-13-01"))  # Invalid month
        self.assertFalse(validate_date_format("2026-10-32"))  # Invalid day
        self.assertFalse(validate_date_format("not-a-date"))
        self.assertFalse(validate_date_format(""))
        self.assertFalse(validate_date_format("1995-05-10"))  # Outside 2000-2100 bounds

    def test_amount_validation(self):
        """Test validation rejects zero, negative, and extreme amounts."""
        # Zero amount
        exp_zero = Expense(date="2026-10-01", amount=0.0, category="Shopping", description="Freebie")
        errors = exp_zero.validate()
        self.assertTrue(any("greater than 0" in e for e in errors))

        # Negative amount
        exp_neg = Expense(date="2026-10-01", amount=-25.0, category="Shopping", description="Refund")
        errors = exp_neg.validate()
        self.assertTrue(any("greater than 0" in e for e in errors))

        # Exceeds maximum limit
        exp_max = Expense(date="2026-10-01", amount=15_000_000.0, category="Shopping", description="Huge")
        errors = exp_max.validate()
        self.assertTrue(any("exceeds maximum" in e for e in errors))

    def test_description_and_category_validation(self):
        """Test rejection of empty descriptions or empty categories."""
        # Empty description
        exp_no_desc = Expense(date="2026-10-01", amount=100.0, category="Shopping", description="   ")
        errors = exp_no_desc.validate()
        self.assertTrue(any("Description cannot be empty" in e for e in errors))

        # Empty category
        exp_no_cat = Expense(date="2026-10-01", amount=100.0, category="", description="Grocery")
        errors = exp_no_cat.validate()
        self.assertTrue(any("Category cannot be empty" in e for e in errors))

    def test_to_dict_and_from_row_serialization(self):
        """Test dict serialization and deserialization from row/tuple/dict."""
        exp = Expense(
            id=12,
            date="2026-10-05",
            amount=89.99,
            category="Transportation",
            description="Metro pass",
            payment_method="Cash",
        )
        d = exp.to_dict()
        self.assertEqual(d["id"], 12)
        self.assertEqual(d["amount"], 89.99)
        self.assertEqual(d["category"], "Transportation")

        # From dict
        reconstructed = Expense.from_row(d)
        self.assertEqual(reconstructed.id, 12)
        self.assertEqual(reconstructed.amount, 89.99)
        self.assertEqual(reconstructed.description, "Metro pass")

        # From tuple
        row_tuple = (15, "2026-10-06", 120.0, "Healthcare", "Medicine", "Credit Card", "2026-10-06 12:00:00")
        from_tuple = Expense.from_row(row_tuple)
        self.assertEqual(from_tuple.id, 15)
        self.assertEqual(from_tuple.amount, 120.0)
        self.assertEqual(from_tuple.category, "Healthcare")


class TestDatabase(unittest.TestCase):
    """Integration tests for SQLite persistence, queries, and aggregations."""

    def setUp(self):
        """Initialize a fresh in-memory database before each test."""
        self.db = Database(":memory:")

    def tearDown(self):
        """Close database connection."""
        self.db.close()

    def test_add_and_get_expense(self):
        """Test adding expense persists record and generates primary key."""
        exp = Expense(
            date="2026-10-10",
            amount=250.0,
            category="Food & Dining",
            description="Dinner with friends",
            payment_method="Credit Card",
        )
        saved = self.db.add_expense(exp)
        self.assertIsNotNone(saved.id)
        self.assertGreater(saved.id, 0)

        retrieved = self.db.get_expense(saved.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.amount, 250.0)
        self.assertEqual(retrieved.description, "Dinner with friends")
        self.assertEqual(retrieved.payment_method, "Credit Card")

    def test_add_invalid_expense_raises_value_error(self):
        """Test that invalid expense throws ValueError on insert."""
        invalid_exp = Expense(
            date="2026-99-99",
            amount=-10.0,
            category="",
            description="",
        )
        with self.assertRaises(ValueError):
            self.db.add_expense(invalid_exp)

    def test_get_all_expenses_ordering(self):
        """Test chronological ordering in get_all_expenses."""
        self.db.add_expense(Expense(date="2026-10-01", amount=100.0, category="Food & Dining", description="Breakfast"))
        self.db.add_expense(Expense(date="2026-10-05", amount=200.0, category="Shopping", description="Shoes"))
        self.db.add_expense(Expense(date="2026-10-03", amount=150.0, category="Transportation", description="Cab"))

        desc_list = self.db.get_all_expenses(order_desc=True)
        self.assertEqual(len(desc_list), 3)
        self.assertEqual(desc_list[0].date, "2026-10-05")
        self.assertEqual(desc_list[-1].date, "2026-10-01")

        asc_list = self.db.get_all_expenses(order_desc=False)
        self.assertEqual(asc_list[0].date, "2026-10-01")
        self.assertEqual(asc_list[-1].date, "2026-10-05")

    def test_update_expense(self):
        """Test updating existing expense record."""
        exp = self.db.add_expense(Expense(date="2026-10-02", amount=80.0, category="Entertainment", description="Movie"))
        exp.amount = 95.50
        exp.description = "IMAX 3D Movie"
        success = self.db.update_expense(exp)
        self.assertTrue(success)

        refreshed = self.db.get_expense(exp.id)
        self.assertEqual(refreshed.amount, 95.50)
        self.assertEqual(refreshed.description, "IMAX 3D Movie")

    def test_update_nonexistent_or_missing_id(self):
        """Test updating nonexistent record returns False; missing id raises ValueError."""
        no_id_exp = Expense(date="2026-10-02", amount=50.0, category="Food", description="Snack")
        with self.assertRaises(ValueError):
            self.db.update_expense(no_id_exp)

        fake_id_exp = Expense(id=99999, date="2026-10-02", amount=50.0, category="Food", description="Snack")
        self.assertFalse(self.db.update_expense(fake_id_exp))

    def test_delete_expense(self):
        """Test deleting an existing expense."""
        exp = self.db.add_expense(Expense(date="2026-10-02", amount=30.0, category="Education", description="Notebook"))
        self.assertTrue(self.db.delete_expense(exp.id))
        self.assertIsNone(self.db.get_expense(exp.id))
        # Deleting again returns False
        self.assertFalse(self.db.delete_expense(exp.id))

    def test_filter_expenses_multi_criteria(self):
        """Test filtering by category, month, and search query."""
        self.db.add_expense(Expense(date="2026-09-15", amount=120.0, category="Food & Dining", description="Groceries"))
        self.db.add_expense(Expense(date="2026-10-02", amount=50.0, category="Food & Dining", description="Coffee snack"))
        self.db.add_expense(Expense(date="2026-10-10", amount=300.0, category="Shopping", description="Winter Jacket"))

        # Filter by category
        food_only = self.db.filter_expenses(category="Food & Dining")
        self.assertEqual(len(food_only), 2)

        # Filter by month
        oct_only = self.db.filter_expenses(month="2026-10")
        self.assertEqual(len(oct_only), 2)

        # Filter by search query
        coffee = self.db.filter_expenses(search_query="coffee")
        self.assertEqual(len(coffee), 1)
        self.assertEqual(coffee[0].description, "Coffee snack")

        # Combined filter
        combined = self.db.filter_expenses(category="Food & Dining", month="2026-10")
        self.assertEqual(len(combined), 1)
        self.assertEqual(combined[0].amount, 50.0)

    def test_distinct_months_and_categories(self):
        """Test retrieving category lists and distinct months."""
        self.db.add_expense(Expense(date="2026-08-01", amount=10.0, category="Custom Hobby", description="Brushes"))
        self.db.add_expense(Expense(date="2026-09-01", amount=20.0, category="Food & Dining", description="Lunch"))

        months = self.db.get_distinct_months()
        self.assertIn("2026-08", months)
        self.assertIn("2026-09", months)

        cats = self.db.get_categories()
        self.assertIn("Food & Dining", cats)
        self.assertIn("Custom Hobby", cats)

    def test_aggregations_and_analytics_summary(self):
        """Test SQLite aggregation queries (sum, avg, max, breakdown)."""
        self.db.add_expense(Expense(date="2026-10-01", amount=100.0, category="Food & Dining", description="Lunch"))
        self.db.add_expense(Expense(date="2026-10-02", amount=300.0, category="Shopping", description="Clothes"))
        self.db.add_expense(Expense(date="2026-10-03", amount=200.0, category="Food & Dining", description="Dinner"))

        total = self.db.get_total_spending()
        self.assertEqual(total, 600.0)

        oct_total = self.db.get_total_spending(month="2026-10")
        self.assertEqual(oct_total, 600.0)

        breakdown = self.db.get_category_breakdown()
        self.assertEqual(len(breakdown), 2)
        # Food & Dining is 300.0 (50.0%), Shopping is 300.0 (50.0%)
        self.assertEqual(breakdown[0]["total"], 300.0)
        self.assertEqual(breakdown[0]["percentage"], 50.0)


class TestExpenseService(unittest.TestCase):
    """Unit tests for the business logic service layer."""

    def setUp(self):
        """Initialize in-memory database and service."""
        self.db = Database(":memory:")
        self.service = ExpenseService(self.db)

    def tearDown(self):
        """Clean up."""
        self.db.close()

    def test_service_crud_workflow(self):
        """Test adding, fetching, updating, and deleting via service."""
        exp = self.service.add_expense(
            date="2026-10-01",
            amount=150.0,
            category="Transportation",
            description="Fuel",
            payment_method="Debit Card",
        )
        self.assertIsNotNone(exp.id)

        # Update
        updated = self.service.update_expense(
            expense_id=exp.id,
            date="2026-10-01",
            amount=180.0,
            category="Transportation",
            description="Fuel + car wash",
            payment_method="Debit Card",
        )
        self.assertEqual(updated.amount, 180.0)

        # Fetch
        retrieved = self.service.get_expense(exp.id)
        self.assertEqual(retrieved.description, "Fuel + car wash")

        # Delete
        self.assertTrue(self.service.delete_expense(exp.id))
        self.assertIsNone(self.service.get_expense(exp.id))

    def test_monthly_report_generation(self):
        """Test generating comprehensive monthly report."""
        self.service.add_expense(date="2026-10-01", amount=100.0, category="Food & Dining", description="Item 1")
        self.service.add_expense(date="2026-10-05", amount=400.0, category="Shopping", description="Item 2")
        self.service.add_expense(date="2026-10-10", amount=50.0, category="Food & Dining", description="Item 3")

        report = self.service.get_monthly_report("2026-10")
        self.assertEqual(report["month"], "2026-10")
        self.assertEqual(report["total_spending"], 550.0)
        self.assertEqual(report["transaction_count"], 3)
        self.assertEqual(report["highest_expense"], 400.0)
        self.assertGreater(report["daily_average"], 0.0)
        self.assertEqual(len(report["category_breakdown"]), 2)

    def test_csv_export_and_import(self):
        """Test CSV export and subsequent re-import."""
        self.service.add_expense(date="2026-10-01", amount=50.0, category="Healthcare", description="Aspirin")
        self.service.add_expense(date="2026-10-02", amount=120.0, category="Education", description="Book")

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "exported_expenses.csv"
            count = self.service.export_to_csv(csv_path)
            self.assertEqual(count, 2)
            self.assertTrue(csv_path.exists())

            # Create a brand new service with fresh DB and import
            new_db = Database(":memory:")
            new_service = ExpenseService(new_db)
            imported_count, warnings = new_service.import_from_csv(csv_path)
            self.assertEqual(imported_count, 2)
            self.assertEqual(len(warnings), 0)

            all_imported = new_service.get_all_expenses()
            self.assertEqual(len(all_imported), 2)
            new_db.close()

    def test_file_persistence_across_restarts(self):
        """Test that data written to an actual SQLite file persists after reconnection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_file = Path(tmpdir) / "persistent_test.db"

            # Session 1: Create and write
            db1 = Database(db_file)
            svc1 = ExpenseService(db1)
            svc1.add_expense(date="2026-10-08", amount=999.0, category="Shopping", description="Headphones")
            db1.close()

            # Session 2: Reopen same file
            db2 = Database(db_file)
            svc2 = ExpenseService(db2)
            items = svc2.get_all_expenses()
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].amount, 999.0)
            self.assertEqual(items[0].description, "Headphones")
            db2.close()


class TestGUIHeadless(unittest.TestCase):
    """Test GUI component instantiation and state handling."""

    def test_gui_instantiation_or_headless_skip(self):
        """Test instantiating GUI window or skipping if headless display is unavailable."""
        import tkinter as tk
        try:
            root = tk.Tk()
            root.withdraw()
            from src.gui import ExpenseTrackerGUI

            mem_db = Database(":memory:")
            mem_service = ExpenseService(mem_db)
            gui = ExpenseTrackerGUI(root, mem_service)

            # Test inserting sample and refreshing
            mem_service.add_expense("2026-10-10", 75.0, "Food & Dining", "Brunch")
            gui.refresh_data()

            self.assertEqual(len(gui.tree.get_children()), 1)

            # Test clear form
            gui.entry_amount.insert(0, "123.45")
            gui._clear_form()
            self.assertEqual(gui.entry_amount.get(), "")

            root.destroy()
            mem_db.close()
        except tk.TclError:
            # Expected on environments without a graphical display server
            self.skipTest("Tkinter display server not available in this environment.")


if __name__ == "__main__":
    unittest.main()
