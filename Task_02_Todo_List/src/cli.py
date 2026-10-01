"""
Command Line Interface formatting and user interaction helpers.

Provides ASCII table formatting, input prompts, input validation,
and visual presentation components for the To-Do application.
"""

import io
import sys
from typing import Any, Dict, List, Optional, Sequence

from src.models import (
    ALLOWED_CATEGORIES,
    ALLOWED_PRIORITIES,
    DEFAULT_CATEGORY,
    DEFAULT_PRIORITY,
    Task,
    validate_date_format,
)


# Reconfigure stdout to UTF-8 defensively for Windows compatibility
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, io.UnsupportedOperation):
    pass


BANNER = """
+-------------------------------------------------------------+
|                     TO-DO LIST MANAGER                      |
|             Task Tracking & Productivity System             |
+-------------------------------------------------------------+
"""

MAIN_MENU = """
+------------------------ MENU -------------------------------+
|  1. View All Tasks              6. Search Tasks             |
|  2. Add New Task                7. Filter Tasks             |
|  3. Toggle Task Completion      8. View Task Statistics     |
|  4. Edit Task Details           9. Clear Completed Tasks    |
|  5. Delete Task                 0. Exit Application         |
+-------------------------------------------------------------+
"""


def print_separator(char: str = "-", length: int = 63) -> None:
    """Print a horizontal divider."""
    print(char * length)


def format_table_row(id_str: str, status: str, title: str, priority: str, category: str, due: str) -> str:
    """Format a single row in the tasks table."""
    return f"| {id_str:<4} | {status:<6} | {title:<24} | {priority:<8} | {category:<10} | {due:<10} |"


def render_task_table(tasks: Sequence[Task], title_header: str = "TASKS") -> None:
    """Render a clean ASCII table of tasks.

    Args:
        tasks: Sequence of Task instances.
        title_header: Descriptive label above table.
    """
    if not tasks:
        print()
        print_separator("=")
        print(f"  {title_header}: No tasks found.")
        print_separator("=")
        print()
        return

    print()
    print_separator("=")
    print(f"  {title_header} ({len(tasks)} item{'s' if len(tasks) != 1 else ''})")
    print_separator("=")
    header_row = format_table_row("ID", "Status", "Title", "Priority", "Category", "Due Date")
    border = "+------+--------+--------------------------+----------+------------+------------+"
    print(border)
    print(header_row)
    print(border)

    for t in tasks:
        truncated_title = t.title if len(t.title) <= 24 else t.title[:21] + "..."
        due_str = t.due_date if t.due_date else "-"
        prio_display = t.priority
        row = format_table_row(
            str(t.id),
            t.status_label,
            truncated_title,
            prio_display,
            t.category,
            due_str,
        )
        print(row)

    print(border)
    print()


def render_task_card(task: Task) -> None:
    """Display all detailed fields of a single task."""
    print()
    print("+------------------------ Task Details -----------------------+")
    print(f"|  ID           : {task.id:<44}|")
    print(f"|  Title        : {task.title[:44]:<44}|")
    if len(task.title) > 44:
        print(f"|                 {task.title[44:88]:<44}|")
    print(f"|  Status       : {'COMPLETED [X]' if task.completed else 'PENDING [ ]':<44}|")
    print(f"|  Priority     : {task.priority:<44}|")
    print(f"|  Category     : {task.category:<44}|")
    print(f"|  Created At   : {task.created_at:<44}|")
    print(f"|  Due Date     : {task.due_date or 'None':<44}|")
    print(f"|  Completed At : {task.completed_at or 'N/A':<44}|")
    if task.description:
        print("|  Description  :")
        for line in task.description.splitlines():
            print(f"|    {line[:57]:<57}|")
    print("+-------------------------------------------------------------+")
    print()


def render_statistics(stats: Dict[str, Any]) -> None:
    """Display task statistics and completion rate in an ASCII box."""
    print()
    print("+---------------------- Task Statistics ----------------------+")
    print(f"|  Total Tasks        : {stats['total']:<38}|")
    print(f"|  Completed Tasks    : {stats['completed']:<38}|")
    print(f"|  Pending Tasks      : {stats['pending']:<38}|")
    print(f"|  Completion Rate    : {str(stats['completion_rate']) + ' %':<38}|")
    print("+-------------------------------------------------------------+")
    print("|  Priority Breakdown :                                       |")
    for prio, count in stats.get("priorities", {}).items():
        print(f"|    - {prio:<10} : {count:<35}|")
    print("+-------------------------------------------------------------+")
    print("|  Category Breakdown :                                       |")
    for cat, count in stats.get("categories", {}).items():
        print(f"|    - {cat:<10} : {count:<35}|")
    print("+-------------------------------------------------------------+")
    print()


def read_int(prompt: str, default: Optional[int] = None, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    """Prompt user for an integer with bounds checking."""
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"  {prompt}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            val = int(raw)
            if min_val is not None and val < min_val:
                print(f"  [!] Value must be at least {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print(f"  [!] Value must be at most {max_val}.")
                continue
            return val
        except ValueError:
            print("  [!] Please enter a valid whole number.")


def read_string(prompt: str, default: Optional[str] = None, allow_empty: bool = False) -> str:
    """Prompt user for a string with whitespace trimming."""
    while True:
        suffix = f" [{default}]" if default is not None else ""
        val = input(f"  {prompt}{suffix}: ").strip()
        if not val and default is not None:
            return default
        if not val and not allow_empty:
            print("  [!] Input cannot be empty. Please enter a value.")
            continue
        return val


def read_choice(prompt: str, choices: Sequence[str], default: Optional[str] = None) -> str:
    """Prompt user to select from a list of valid choices."""
    lookup = {c.lower(): c for c in choices}
    choices_str = "/".join(choices)
    while True:
        suffix = f" [{default}]" if default is not None else ""
        val = input(f"  {prompt} ({choices_str}){suffix}: ").strip()
        if not val and default is not None:
            return default
        if val.lower() in lookup:
            return lookup[val.lower()]
        print(f"  [!] Invalid choice. Please choose from: {', '.join(choices)}.")


def read_yes_no(prompt: str, default: bool = True) -> bool:
    """Prompt user for a yes/no confirmation."""
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"  {prompt} [{hint}]: ").strip().lower()
        if raw == "":
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  [!] Please enter 'y' for yes or 'n' for no.")


def read_date(prompt: str, default: Optional[str] = None, allow_empty: bool = True) -> Optional[str]:
    """Prompt user for a valid YYYY-MM-DD date."""
    while True:
        suffix = f" [{default}]" if default is not None else (" [optional - press Enter to skip]" if allow_empty else "")
        raw = input(f"  {prompt}{suffix}: ").strip()
        if not raw and default is not None:
            return default
        if not raw and allow_empty:
            return None
        if validate_date_format(raw):
            return raw
        print("  [!] Invalid date format. Please use 'YYYY-MM-DD' (e.g. 2026-10-15).")
