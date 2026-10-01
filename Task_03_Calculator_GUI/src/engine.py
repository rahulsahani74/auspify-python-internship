"""
Core Calculator Engine and Safe Mathematical Expression Evaluator.

Provides the SafeEvaluator class using Python's Abstract Syntax Tree (ast)
to securely parse and compute mathematical expressions without unsafe eval().
Also provides the CalculatorEngine class managing calculator state, history,
and user input transitions.
"""

import ast
import math
import operator
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union


# Supported binary operators mapped to standard functions
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
}

# Supported unary operators
SAFE_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class EvaluationError(Exception):
    """Base exception for expression evaluation errors."""
    pass


class DivisionByZeroError(EvaluationError):
    """Raised when an expression attempts to divide by zero."""
    pass


class InvalidExpressionError(EvaluationError):
    """Raised when an expression is malformed or contains invalid syntax."""
    pass


class SecurityError(EvaluationError):
    """Raised when an expression contains forbidden AST nodes."""
    pass


class SafeEvaluator:
    """Safely evaluates mathematical expressions using AST traversal.

    Only permits numbers, binary operations (+, -, *, /, %, **), unary (+, -),
    and parentheses. Prevents arbitrary code execution, attribute access, and function calls.
    """

    @classmethod
    def evaluate(cls, expression: str) -> Union[int, float]:
        """Parse and safely compute a mathematical expression string.

        Args:
            expression: Mathematical expression string.

        Returns:
            The calculated numeric result (int or float).

        Raises:
            DivisionByZeroError: If division by zero occurs.
            InvalidExpressionError: If syntax is malformed.
            SecurityError: If disallowed AST structures are encountered.
        """
        cleaned = cls._sanitize(expression)
        if not cleaned:
            raise InvalidExpressionError("Expression is empty.")

        try:
            tree = ast.parse(cleaned, mode="eval")
        except SyntaxError as exc:
            raise InvalidExpressionError(f"Malformed syntax in expression: {exc}")

        return cls._eval_node(tree.body)

    @classmethod
    def _sanitize(cls, expr: str) -> str:
        """Normalize visual symbols to Python math operators."""
        # Replace display symbols
        sanitized = expr.replace("×", "*").replace("÷", "/").replace("−", "-")
        sanitized = sanitized.replace("^", "**")

        # Replace percent followed by an operator, parenthesis, or end of string with /100
        # e.g., "50%" -> "(50/100)", "200*10%" -> "200*(10/100)"
        sanitized = re.sub(r"(\d+(\.\d+)?)%", r"(\1/100)", sanitized)

        return sanitized.strip()

    @classmethod
    def _eval_node(cls, node: ast.AST) -> Union[int, float]:
        """Recursively evaluate an AST node adhering to strict safety rules."""
        # Numbers (ast.Constant in Python 3.8+, ast.Num in older)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise SecurityError(f"Disallowed constant type: {type(node.value).__name__}")

        # Unary operations (e.g. -5, +3)
        if isinstance(node, ast.UnaryOp):
            op_func = SAFE_UNARY_OPERATORS.get(type(node.op))
            if op_func is None:
                raise SecurityError(f"Disallowed unary operator: {type(node.op).__name__}")
            operand = cls._eval_node(node.operand)
            return op_func(operand)

        # Binary operations (e.g. 5 + 3, 10 / 2)
        if isinstance(node, ast.BinOp):
            op_func = SAFE_OPERATORS.get(type(node.op))
            if op_func is None:
                raise SecurityError(f"Disallowed binary operator: {type(node.op).__name__}")

            left = cls._eval_node(node.left)
            right = cls._eval_node(node.right)

            # Division-by-zero check
            if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                if right == 0:
                    raise DivisionByZeroError("Cannot divide by zero.")

            try:
                # Prevent massive exponents causing CPU denial of service
                if isinstance(node.op, ast.Pow):
                    if abs(left) > 1000 and right > 100:
                        raise InvalidExpressionError("Exponent too large to compute.")
                    if right > 1000:
                        raise InvalidExpressionError("Exponent too large to compute.")
                return op_func(left, right)
            except ZeroDivisionError:
                raise DivisionByZeroError("Cannot divide by zero.")
            except OverflowError:
                raise InvalidExpressionError("Result overflowed numerical limits.")

        # Reject any other node (calls, attributes, variables, loops, etc.)
        raise SecurityError(f"Disallowed expression node: {type(node).__name__}")


@dataclass
class CalculationRecord:
    """Represents a single completed calculation record."""
    expression: str
    result: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


class CalculatorEngine:
    """Manages calculator state, input sequence construction, and evaluation."""

    MAX_HISTORY_ITEMS = 50

    def __init__(self):
        """Initialize a fresh calculator engine state."""
        self._expression: str = ""
        self._last_result: Optional[Union[int, float]] = None
        self._history: List[CalculationRecord] = []
        self._just_calculated: bool = False

    @property
    def expression(self) -> str:
        """Current expression string."""
        return self._expression

    @property
    def history(self) -> List[CalculationRecord]:
        """List of calculation history records."""
        return list(self._history)

    def input_digit(self, digit: str) -> str:
        """Append a numeric digit (0-9).

        If calculation just completed, starts a new expression unless continuing.
        """
        if self._just_calculated:
            self._expression = ""
            self._just_calculated = False

        self._expression += str(digit)
        return self._expression

    def input_decimal(self) -> str:
        """Append a decimal point safely without duplicate decimals in the current operand."""
        if self._just_calculated:
            self._expression = "0."
            self._just_calculated = False
            return self._expression

        # If empty or ends with operator/parenthesis, prepend 0
        if not self._expression or self._expression[-1] in ("+", "-", "×", "÷", "(", "^"):
            self._expression += "0."
            return self._expression

        # Check if the current trailing number token already contains a decimal
        last_token = re.split(r"[+\-×÷^()]", self._expression)[-1]
        if "." in last_token:
            return self._expression

        self._expression += "."
        return self._expression

    def input_operator(self, op: str) -> str:
        """Append or replace a mathematical operator (+, -, ×, ÷, ^)."""
        display_op = op.replace("*", "×").replace("/", "÷")
        self._just_calculated = False

        if not self._expression:
            if display_op == "-":
                # Allow leading negative sign
                self._expression = "-"
            return self._expression

        # If previous character is already an operator, replace it (unless negative sign)
        if self._expression[-1] in ("+", "-", "×", "÷", "^"):
            if len(self._expression) == 1 and self._expression[-1] == "-":
                return self._expression
            self._expression = self._expression[:-1] + display_op
        else:
            self._expression += display_op

        return self._expression

    def input_parenthesis(self, paren: str) -> str:
        """Add opening or closing parenthesis."""
        if self._just_calculated and paren == "(":
            self._expression = ""
            self._just_calculated = False

        self._expression += paren
        return self._expression

    def input_percentage(self) -> str:
        """Apply percentage to the current operand."""
        if self._expression and self._expression[-1] not in ("+", "-", "×", "÷", "(", "^", "%"):
            self._expression += "%"
        return self._expression

    def backspace(self) -> str:
        """Remove the last entered character."""
        if self._just_calculated:
            self._expression = ""
            self._just_calculated = False
            return self._expression

        if self._expression:
            self._expression = self._expression[:-1]
        return self._expression

    def clear(self) -> str:
        """Reset the current expression completely."""
        self._expression = ""
        self._just_calculated = False
        return self._expression

    def clear_entry(self) -> str:
        """Clear only the most recent operand/token."""
        if self._just_calculated or not self._expression:
            return self.clear()

        # Find the last operator boundary
        match = re.search(r"[+\-×÷^()][^+\-×÷^()]*$", self._expression)
        if match:
            # Keep up to the operator
            self._expression = self._expression[:match.start() + 1]
        else:
            self._expression = ""
        return self._expression

    def toggle_sign(self) -> str:
        """Toggle the positive/negative sign of the trailing number."""
        if not self._expression:
            self._expression = "-"
            return self._expression

        # Find trailing number
        match = re.search(r"(-?\d+(\.\d+)?)$", self._expression)
        if match:
            num_str = match.group(1)
            start_idx = match.start(1)
            if num_str.startswith("-"):
                new_num = num_str[1:]
            else:
                new_num = "-" + num_str
            self._expression = self._expression[:start_idx] + new_num

        return self._expression

    def square_root(self) -> Tuple[str, Optional[str]]:
        """Compute the square root of the current expression or trailing number.

        Returns:
            Tuple of (formatted_result, error_message).
        """
        try:
            # If current expression evaluates to a number, sqrt it
            val = SafeEvaluator.evaluate(self._expression) if self._expression else 0
            if val < 0:
                return "", "Cannot calculate square root of negative number"
            res = math.sqrt(val)
            formatted = self._format_number(res)
            self._record_history(f"√({self._expression})", formatted)
            self._expression = formatted
            self._just_calculated = True
            return formatted, None
        except Exception as exc:
            return "", str(exc)

    def calculate(self) -> Tuple[str, Optional[str]]:
        """Evaluate the active expression.

        Returns:
            Tuple of (formatted_result_string, error_message).
            If successful, error_message is None.
            If an error occurred, result is empty string and error_message is populated.
        """
        if not self._expression:
            return "0", None

        # Auto-close unmatched opening parentheses
        open_count = self._expression.count("(")
        close_count = self._expression.count(")")
        if open_count > close_count:
            self._expression += ")" * (open_count - close_count)

        try:
            numeric_res = SafeEvaluator.evaluate(self._expression)
            formatted = self._format_number(numeric_res)
            self._record_history(self._expression, formatted)
            self._last_result = numeric_res
            self._expression = formatted
            self._just_calculated = True
            return formatted, None
        except DivisionByZeroError as exc:
            return "", str(exc)
        except InvalidExpressionError as exc:
            return "", str(exc)
        except SecurityError as exc:
            return "", f"Security error: {exc}"
        except Exception as exc:
            return "", f"Error: {exc}"

    def set_expression(self, expr: str) -> str:
        """Set the active expression directly (e.g. from history selection)."""
        self._expression = str(expr).strip()
        self._just_calculated = False
        return self._expression

    def clear_history(self) -> None:
        """Clear all calculation history."""
        self._history.clear()

    def _record_history(self, expr: str, res: str) -> None:
        """Append calculation to history, keeping max items."""
        record = CalculationRecord(expression=expr, result=res)
        self._history.append(record)
        if len(self._history) > self.MAX_HISTORY_ITEMS:
            self._history.pop(0)

    @classmethod
    def _format_number(cls, value: Union[int, float]) -> str:
        """Format a numeric value cleanly, avoiding float precision artifacts."""
        if isinstance(value, float):
            # Check for integer equivalent
            if value.is_integer():
                return str(int(value))
            # Round float to 10 decimal places to eliminate IEEE 754 precision noise
            rounded = round(value, 10)
            if rounded.is_integer():
                return str(int(rounded))
            # Remove trailing zeros after decimal point
            s = f"{rounded:.10f}".rstrip("0").rstrip(".")
            return s
        return str(value)
