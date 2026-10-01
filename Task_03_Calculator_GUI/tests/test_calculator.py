"""
Comprehensive Automated Unit Tests for Task 03: Calculator with GUI.

Covers:
- SafeEvaluator: basic arithmetic, decimal values, operator precedence, unary signs,
  percentages, power operations, parentheses, division by zero, invalid expressions,
  and AST security against malicious code execution.
- CalculatorEngine: digit entry, decimal guards, operator replacement, sign toggling,
  square root, backspace, clear, clear entry, and history tracking.
- CalculatorGUI: headless initialization, widget construction, and display updates.
"""

import sys
import tkinter as tk
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.engine import (
    CalculatorEngine,
    DivisionByZeroError,
    InvalidExpressionError,
    SafeEvaluator,
    SecurityError,
)
from src.gui import CalculatorGUI


# ===========================================================================
# 1. Safe Evaluator Tests
# ===========================================================================

class TestSafeEvaluator(unittest.TestCase):
    """Test suite for the mathematical AST SafeEvaluator."""

    def test_basic_addition(self):
        self.assertEqual(SafeEvaluator.evaluate("10 + 25"), 35)

    def test_basic_subtraction(self):
        self.assertEqual(SafeEvaluator.evaluate("50 - 18"), 32)

    def test_basic_multiplication(self):
        self.assertEqual(SafeEvaluator.evaluate("6 * 7"), 42)
        # Using visual multiplication symbol
        self.assertEqual(SafeEvaluator.evaluate("6 × 7"), 42)

    def test_basic_division(self):
        self.assertEqual(SafeEvaluator.evaluate("20 / 4"), 5.0)
        # Using visual division symbol
        self.assertEqual(SafeEvaluator.evaluate("20 ÷ 4"), 5.0)

    def test_decimal_calculations(self):
        self.assertAlmostEqual(SafeEvaluator.evaluate("0.1 + 0.2"), 0.3, places=7)
        self.assertEqual(SafeEvaluator.evaluate("10.5 * 2"), 21.0)
        self.assertEqual(SafeEvaluator.evaluate("7.5 - 2.25"), 5.25)

    def test_operator_precedence(self):
        # Multiplication before addition
        self.assertEqual(SafeEvaluator.evaluate("2 + 3 * 4"), 14)
        # Parentheses override precedence
        self.assertEqual(SafeEvaluator.evaluate("(2 + 3) * 4"), 20)

    def test_nested_parentheses(self):
        self.assertEqual(SafeEvaluator.evaluate("((2 + 3) * (4 - 1)) / 5"), 3.0)

    def test_unary_operators(self):
        self.assertEqual(SafeEvaluator.evaluate("-5 + 12"), 7)
        self.assertEqual(SafeEvaluator.evaluate("10 - -3"), 13)
        self.assertEqual(SafeEvaluator.evaluate("-(4 + 6)"), -10)
        self.assertEqual(SafeEvaluator.evaluate("+8 + +2"), 10)

    def test_power_operation(self):
        self.assertEqual(SafeEvaluator.evaluate("2 ** 3"), 8)
        self.assertEqual(SafeEvaluator.evaluate("2 ^ 3"), 8)
        self.assertEqual(SafeEvaluator.evaluate("5 ^ 2"), 25)

    def test_percentage_operation(self):
        # 50% -> 0.5
        self.assertEqual(SafeEvaluator.evaluate("50%"), 0.5)
        # 200 * 10% -> 20.0
        self.assertEqual(SafeEvaluator.evaluate("200 * 10%"), 20.0)
        # 100 + 10% -> 100 + 0.1 = 100.1
        self.assertAlmostEqual(SafeEvaluator.evaluate("100 + 10%"), 100.1, places=5)

    def test_division_by_zero_protection(self):
        with self.assertRaises(DivisionByZeroError):
            SafeEvaluator.evaluate("10 / 0")

        with self.assertRaises(DivisionByZeroError):
            SafeEvaluator.evaluate("10 ÷ 0")

        with self.assertRaises(DivisionByZeroError):
            SafeEvaluator.evaluate("15 / (3 - 3)")

        with self.assertRaises(DivisionByZeroError):
            SafeEvaluator.evaluate("12 % 0")

    def test_invalid_syntax_expressions(self):
        invalid_cases = [
            "",
            "   ",
            "5 +",
            "* 4",
            "5 +* 3",
            "((5 + 2)",
            ")(",
            "5..2 + 1",
        ]
        for expr in invalid_cases:
            with self.subTest(expr=expr):
                with self.assertRaises(InvalidExpressionError):
                    SafeEvaluator.evaluate(expr)

    def test_security_rejection_of_disallowed_nodes(self):
        forbidden_payloads = [
            "__import__('os').system('ls')",
            "print(123)",
            "eval('1 + 1')",
            "open('test.txt', 'w')",
            "x + 1",
            "'hello' + 'world'",
            "[1, 2, 3][0]",
            "abs(-5)",
            "{'a': 1}",
        ]
        for payload in forbidden_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(SecurityError):
                    SafeEvaluator.evaluate(payload)


# ===========================================================================
# 2. Calculator Engine State Tests
# ===========================================================================

class TestCalculatorEngine(unittest.TestCase):
    """Test suite for the stateful CalculatorEngine."""

    def setUp(self):
        self.engine = CalculatorEngine()

    def test_initial_state(self):
        self.assertEqual(self.engine.expression, "")
        self.assertEqual(len(self.engine.history), 0)

    def test_input_digits(self):
        self.engine.input_digit("4")
        self.engine.input_digit("2")
        self.assertEqual(self.engine.expression, "42")

    def test_decimal_input_guards(self):
        # Initial decimal prepends 0.
        self.engine.input_decimal()
        self.assertEqual(self.engine.expression, "0.")

        # Duplicate decimal in same number is ignored
        self.engine.input_decimal()
        self.assertEqual(self.engine.expression, "0.")

        self.engine.input_digit("5")
        self.engine.input_decimal()  # Ignored: "0.5." is invalid
        self.assertEqual(self.engine.expression, "0.5")

        # Decimal after operator prepends 0.
        self.engine.input_operator("+")
        self.engine.input_decimal()
        self.assertEqual(self.engine.expression, "0.5+0.")

    def test_operator_replacement(self):
        self.engine.input_digit("8")
        self.engine.input_operator("+")
        self.assertEqual(self.engine.expression, "8+")

        # Pressing a different operator replaces the previous one
        self.engine.input_operator("×")
        self.assertEqual(self.engine.expression, "8×")

        self.engine.input_operator("-")
        self.assertEqual(self.engine.expression, "8-")

    def test_leading_minus(self):
        self.engine.input_operator("-")
        self.assertEqual(self.engine.expression, "-")
        self.engine.input_digit("5")
        self.assertEqual(self.engine.expression, "-5")

    def test_backspace(self):
        self.engine.input_digit("1")
        self.engine.input_digit("2")
        self.engine.input_digit("3")
        self.assertEqual(self.engine.expression, "123")

        self.engine.backspace()
        self.assertEqual(self.engine.expression, "12")

        self.engine.backspace()
        self.assertEqual(self.engine.expression, "1")

        self.engine.backspace()
        self.assertEqual(self.engine.expression, "")

        # Backspace on empty string does nothing
        self.engine.backspace()
        self.assertEqual(self.engine.expression, "")

    def test_clear_and_clear_entry(self):
        self.engine.input_digit("1")
        self.engine.input_digit("2")
        self.engine.input_operator("+")
        self.engine.input_digit("9")
        self.engine.input_digit("9")
        self.assertEqual(self.engine.expression, "12+99")

        # Clear Entry removes only "99"
        self.engine.clear_entry()
        self.assertEqual(self.engine.expression, "12+")

        # Full Clear resets completely
        self.engine.clear()
        self.assertEqual(self.engine.expression, "")

    def test_toggle_sign(self):
        self.engine.input_digit("2")
        self.engine.input_digit("5")
        self.assertEqual(self.engine.expression, "25")

        self.engine.toggle_sign()
        self.assertEqual(self.engine.expression, "-25")

        self.engine.toggle_sign()
        self.assertEqual(self.engine.expression, "25")

    def test_square_root(self):
        self.engine.input_digit("4")
        self.engine.input_digit("9")
        result, error = self.engine.square_root()
        self.assertIsNone(error)
        self.assertEqual(result, "7")
        self.assertEqual(self.engine.expression, "7")

        # Square root of negative number yields error
        self.engine.clear()
        self.engine.input_operator("-")
        self.engine.input_digit("9")
        res, err = self.engine.square_root()
        self.assertIsNotNone(err)
        self.assertIn("negative", err.lower())

    def test_calculate_success_and_auto_close_parentheses(self):
        self.engine.input_parenthesis("(")
        self.engine.input_digit("5")
        self.engine.input_operator("+")
        self.engine.input_digit("7")
        # Notice closing parenthesis not explicitly typed: "(5+7"
        res, err = self.engine.calculate()
        self.assertIsNone(err)
        self.assertEqual(res, "12")
        self.assertEqual(self.engine.expression, "12")

    def test_calculate_division_by_zero(self):
        self.engine.input_digit("1")
        self.engine.input_digit("0")
        self.engine.input_operator("÷")
        self.engine.input_digit("0")
        res, err = self.engine.calculate()
        self.assertEqual(res, "")
        self.assertIn("divide by zero", err.lower())

    def test_history_recording_and_clearing(self):
        self.engine.input_digit("3")
        self.engine.input_operator("+")
        self.engine.input_digit("4")
        self.engine.calculate()

        self.engine.input_digit("1")
        self.engine.input_digit("0")
        self.engine.input_operator("×")
        self.engine.input_digit("2")
        self.engine.calculate()

        hist = self.engine.history
        self.assertEqual(len(hist), 2)
        self.assertEqual(hist[0].expression, "3+4")
        self.assertEqual(hist[0].result, "7")
        self.assertEqual(hist[1].expression, "10×2")
        self.assertEqual(hist[1].result, "20")

        self.engine.clear_history()
        self.assertEqual(len(self.engine.history), 0)

    def test_number_formatting(self):
        self.assertEqual(CalculatorEngine._format_number(5.0), "5")
        self.assertEqual(CalculatorEngine._format_number(42), "42")
        self.assertEqual(CalculatorEngine._format_number(0.1 + 0.2), "0.3")
        self.assertEqual(CalculatorEngine._format_number(3.14159), "3.14159")


# ===========================================================================
# 3. GUI Smoke & Headless Integration Tests
# ===========================================================================

class TestCalculatorGUI(unittest.TestCase):
    """Test suite for Tkinter GUI widget construction and event binding."""

    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()  # Hide window during test
            self.gui = CalculatorGUI(self.root)
        except tk.TclError:
            self.skipTest("Tkinter display not available in this environment")

    def tearDown(self):
        if hasattr(self, "root"):
            try:
                self.root.destroy()
            except tk.TclError:
                pass

    def test_gui_initial_display(self):
        self.assertEqual(self.gui.main_display_var.get(), "0")
        self.assertEqual(self.gui.sub_display_var.get(), "")
        self.assertEqual(self.gui.status_var.get(), "")

    def test_gui_digit_and_operator_buttons(self):
        self.gui._on_digit("9")
        self.gui._on_digit("5")
        self.assertEqual(self.gui.main_display_var.get(), "95")

        self.gui._on_operator("+")
        self.assertEqual(self.gui.main_display_var.get(), "95+")

        self.gui._on_digit("5")
        self.assertEqual(self.gui.main_display_var.get(), "95+5")

        self.gui._on_equal()
        self.assertEqual(self.gui.main_display_var.get(), "100")
        self.assertEqual(self.gui.sub_display_var.get(), "95+5 =")

    def test_gui_division_by_zero_alert(self):
        self.gui._on_digit("8")
        self.gui._on_operator("÷")
        self.gui._on_digit("0")
        self.gui._on_equal()

        self.assertIn("divide by zero", self.gui.status_var.get().lower())

    def test_gui_clear_button(self):
        self.gui._on_digit("7")
        self.gui._on_clear()
        self.assertEqual(self.gui.main_display_var.get(), "0")
        self.assertEqual(self.gui.sub_display_var.get(), "")

    def test_gui_backspace_and_decimal(self):
        self.gui._on_digit("1")
        self.gui._on_digit("2")
        self.gui._on_decimal()
        self.gui._on_digit("5")
        self.assertEqual(self.gui.main_display_var.get(), "12.5")

        self.gui._on_backspace()
        self.assertEqual(self.gui.main_display_var.get(), "12.")

    def test_gui_toggle_sign_and_sqrt(self):
        self.gui._on_digit("9")
        self.gui._on_sqrt()
        self.assertEqual(self.gui.main_display_var.get(), "3")
        self.assertEqual(self.gui.sub_display_var.get(), "√(9) =")

        self.gui._on_toggle_sign()
        self.assertEqual(self.gui.main_display_var.get(), "-3")

    def test_gui_history_window_interaction(self):
        # Perform calculation
        self.gui._on_digit("4")
        self.gui._on_operator("+")
        self.gui._on_digit("6")
        self.gui._on_equal()

        # Open history window
        self.gui._toggle_history_window()
        self.assertIsNotNone(self.gui.history_window)
        self.assertTrue(self.gui.history_window.winfo_exists())

        # Verify listbox populated
        items = self.gui.history_listbox.get(0, tk.END)
        self.assertTrue(any("4+6 = 10" in item for item in items))

        # Close history window
        self.gui.history_window.destroy()


if __name__ == "__main__":
    unittest.main()
