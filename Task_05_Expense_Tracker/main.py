"""
Main entry point for Task 05: Personal Expense Tracker & Analyzer.

Launches the Tkinter desktop GUI by default, and supports a command-line
interface (--cli, --summary, --report) for headless environments and scripting.
"""

import argparse
import sys
import tkinter as tk

# Ensure terminal stdout/stderr handles UTF-8 (e.g. currency symbols on Windows cp1252)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.models import CURRENCY_SYMBOL
from src.service import ExpenseService


def print_ascii_table(headers: list[str], rows: list[list[str]], col_widths: list[int]) -> None:
    """Render a clean ASCII table."""
    border = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    print(border)
    header_str = "|" + "|".join(f" {h:<{col_widths[i]}} " for i, h in enumerate(headers)) + "|"
    print(header_str)
    print(border)
    for r in rows:
        row_str = "|" + "|".join(f" {str(r[i]):<{col_widths[i]}} " for i in range(len(r))) + "|"
        print(row_str)
    print(border)


def run_cli_summary(service: ExpenseService) -> None:
    """Print overall financial analytics summary to terminal."""
    summary = service.get_dashboard_summary()
    print("\n+------------------ EXPENSE SUMMARY ------------------+")
    print(f"|  Total Spending        : {CURRENCY_SYMBOL} {summary['total_spent']:<23,.2f}|")
    print(f"|  This Month's Spending : {CURRENCY_SYMBOL} {summary['this_month_spent']:<23,.2f}|")
    print(f"|  Today's Spending      : {CURRENCY_SYMBOL} {summary['today_spent']:<23,.2f}|")
    print(f"|  Average Expense       : {CURRENCY_SYMBOL} {summary['avg_expense']:<23,.2f}|")
    print(f"|  Highest Single Expense: {CURRENCY_SYMBOL} {summary['highest_expense']:<23,.2f}|")
    print(f"|  Total Transactions    : {summary['total_transactions']:<25}|")
    print("+-----------------------------------------------------+\n")


def run_cli_report(service: ExpenseService, month: str | None = None) -> None:
    """Print monthly financial breakdown report to terminal."""
    rep = service.get_monthly_report(month)
    print(f"\n=======================================================")
    print(f"  MONTHLY EXPENSE REPORT: {rep['month']}")
    print(f"=======================================================")
    print(f"  Total Spending    : {CURRENCY_SYMBOL} {rep['total_spending']:,.2f}")
    print(f"  Daily Average     : {CURRENCY_SYMBOL} {rep['daily_average']:,.2f}")
    print(f"  Transaction Count : {rep['transaction_count']}")
    print(f"  Highest Expense   : {CURRENCY_SYMBOL} {rep['highest_expense']:,.2f}\n")

    if rep["category_breakdown"]:
        headers = ["Category", f"Total ({CURRENCY_SYMBOL})", "Share (%)", "Count"]
        widths = [22, 14, 10, 8]
        rows = [
            [
                b["category"][:22],
                f"{b['total']:,.2f}",
                f"{b['percentage']:.1f}%",
                str(b["count"]),
            ]
            for b in rep["category_breakdown"]
        ]
        print("  CATEGORY BREAKDOWN:")
        print_ascii_table(headers, rows, widths)
    else:
        print("  No transactions recorded for this period.\n")


def run_cli_list(service: ExpenseService) -> None:
    """Print all expense records in terminal table."""
    records = service.get_all_expenses()
    if not records:
        print("\n  [INFO] No expenses recorded yet.\n")
        return

    headers = ["ID", "Date", "Category", "Description", "Payment", f"Amount ({CURRENCY_SYMBOL})"]
    widths = [5, 10, 18, 26, 12, 12]
    rows = [
        [
            str(e.id),
            e.date,
            e.category[:18],
            e.description[:26],
            e.payment_method[:12],
            f"{e.amount:,.2f}",
        ]
        for e in records
    ]
    print(f"\n  ALL RECORDED EXPENSES ({len(records)} items):")
    print_ascii_table(headers, rows, widths)
    print()


def run_gui_mode() -> int:
    """Launch the Tkinter desktop GUI."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"[!] Desktop display unavailable ({exc}). Falling back to CLI mode.\n")
        service = ExpenseService()
        run_cli_summary(service)
        run_cli_list(service)
        return 0

    from src.gui import ExpenseTrackerGUI

    # Center window
    w, h = 960, 680
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    px = max(0, int((sw - w) / 2))
    py = max(0, int((sh - h) / 2))
    root.geometry(f"{w}x{h}+{px}+{py}")

    app = ExpenseTrackerGUI(root)
    root.mainloop()
    return 0


def main() -> None:
    """Command-line argument router."""
    parser = argparse.ArgumentParser(
        description="Task 05: Personal Expense Tracker & Analyzer"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in terminal CLI mode instead of launching GUI.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print financial summary metrics to terminal.",
    )
    parser.add_argument(
        "--report",
        type=str,
        nargs="?",
        const="",
        help="Print monthly report to terminal (optional month: YYYY-MM).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print all expense records in terminal.",
    )
    parser.add_argument(
        "--export-csv",
        type=str,
        metavar="PATH",
        help="Export all recorded expenses to specified CSV file path.",
    )
    parser.add_argument(
        "--import-csv",
        type=str,
        metavar="PATH",
        help="Import expenses from specified CSV file path.",
    )

    args = parser.parse_args()
    service = ExpenseService()

    if args.summary:
        run_cli_summary(service)
        sys.exit(0)
    elif args.report is not None:
        target_month = args.report if args.report else None
        run_cli_report(service, target_month)
        sys.exit(0)
    elif args.list:
        run_cli_list(service)
        sys.exit(0)
    elif args.export_csv:
        count = service.export_to_csv(args.export_csv)
        print(f"[✓] Successfully exported {count} expense records to '{args.export_csv}'.")
        sys.exit(0)
    elif args.import_csv:
        count, warnings = service.import_from_csv(args.import_csv)
        print(f"[✓] Successfully imported {count} expense records from '{args.import_csv}'.")
        if warnings:
            print("  Warnings:")
            for w in warnings:
                print(f"  - {w}")
        sys.exit(0)
    elif args.cli:
        run_cli_summary(service)
        run_cli_list(service)
        sys.exit(0)
    else:
        sys.exit(run_gui_mode())


if __name__ == "__main__":
    main()
