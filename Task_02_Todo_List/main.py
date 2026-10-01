"""
Main entry point for the To-Do List Application CLI.

Coordinates the command-line menu loop, user interactions, and calls into
the TodoService business logic layer.
"""

import sys
from src.cli import (
    BANNER,
    MAIN_MENU,
    print_separator,
    read_choice,
    read_date,
    read_int,
    read_string,
    read_yes_no,
    render_statistics,
    render_task_card,
    render_task_table,
)
from src.models import (
    ALLOWED_CATEGORIES,
    ALLOWED_PRIORITIES,
    DEFAULT_CATEGORY,
    DEFAULT_PRIORITY,
)
from src.service import TodoService


def handle_view_tasks(service: TodoService) -> None:
    """Display all tasks with optional detailed inspection."""
    tasks = service.get_all_tasks()
    render_task_table(tasks, "ALL TASKS")

    if tasks:
        inspect = read_yes_no("Would you like to view full details of a specific task?", default=False)
        if inspect:
            task_id = read_int("Enter Task ID to view", min_val=1)
            task = service.get_task(task_id)
            if task:
                render_task_card(task)
            else:
                print(f"  [!] Task with ID {task_id} not found.")


def handle_add_task(service: TodoService) -> None:
    """Prompt for task details and add a new task."""
    print("\n  --- ADD NEW TASK ---")
    title = read_string("Task Title (required)", allow_empty=False)
    description = read_string("Description (optional)", default="", allow_empty=True)
    priority = read_choice("Priority", ALLOWED_PRIORITIES, default=DEFAULT_PRIORITY)
    category = read_string(f"Category (e.g. {', '.join(ALLOWED_CATEGORIES)})", default=DEFAULT_CATEGORY, allow_empty=True)
    due_date = read_date("Due Date (YYYY-MM-DD)", default=None, allow_empty=True)

    try:
        task = service.add_task(
            title=title,
            description=description,
            priority=priority,
            category=category,
            due_date=due_date,
        )
        print(f"\n  [OK] Task #{task.id} '{task.title}' added successfully!")
    except ValueError as err:
        print(f"\n  [!] Validation error: {err}")


def handle_toggle_task(service: TodoService) -> None:
    """Toggle the completion status of a task."""
    tasks = service.get_all_tasks()
    if not tasks:
        print("\n  [!] No tasks available to update.")
        return

    print("\n  --- TOGGLE TASK STATUS ---")
    task_id = read_int("Enter Task ID to toggle", min_val=1)
    task = service.get_task(task_id)
    if not task:
        print(f"  [!] Task #{task_id} not found.")
        return

    was_completed = task.completed
    service.toggle_status(task_id)
    new_status = "COMPLETED [X]" if not was_completed else "PENDING [ ]"
    print(f"\n  [OK] Task #{task_id} is now marked as {new_status}.")


def handle_edit_task(service: TodoService) -> None:
    """Edit fields of an existing task."""
    tasks = service.get_all_tasks()
    if not tasks:
        print("\n  [!] No tasks available to edit.")
        return

    print("\n  --- EDIT TASK ---")
    task_id = read_int("Enter Task ID to edit", min_val=1)
    task = service.get_task(task_id)
    if not task:
        print(f"  [!] Task #{task_id} not found.")
        return

    print(f"\n  Editing Task #{task.id} (press Enter to keep existing value):")
    new_title = read_string("New Title", default=task.title, allow_empty=False)
    new_desc = read_string("New Description", default=task.description, allow_empty=True)
    new_prio = read_choice("New Priority", ALLOWED_PRIORITIES, default=task.priority)
    new_cat = read_string("New Category", default=task.category, allow_empty=True)
    new_due = read_date("New Due Date (YYYY-MM-DD)", default=task.due_date, allow_empty=True)

    try:
        service.update_task(
            task_id=task.id,
            title=new_title,
            description=new_desc,
            priority=new_prio,
            category=new_cat,
            due_date=new_due,
        )
        print(f"\n  [OK] Task #{task.id} updated successfully!")
    except (ValueError, KeyError) as err:
        print(f"\n  [!] Update failed: {err}")


def handle_delete_task(service: TodoService) -> None:
    """Prompt for a task ID and delete it after confirmation."""
    tasks = service.get_all_tasks()
    if not tasks:
        print("\n  [!] No tasks available to delete.")
        return

    print("\n  --- DELETE TASK ---")
    task_id = read_int("Enter Task ID to delete", min_val=1)
    task = service.get_task(task_id)
    if not task:
        print(f"  [!] Task #{task_id} not found.")
        return

    confirm = read_yes_no(f"Are you sure you want to permanently delete Task #{task_id} ('{task.title}')?", default=False)
    if confirm:
        service.delete_task(task_id)
        print(f"\n  [OK] Task #{task_id} deleted successfully.")
    else:
        print("\n  [INFO] Deletion cancelled.")


def handle_search_tasks(service: TodoService) -> None:
    """Search tasks by keyword across title, description, and category."""
    print("\n  --- SEARCH TASKS ---")
    query = read_string("Search query", allow_empty=False)
    matches = service.search_tasks(query)
    render_task_table(matches, f"SEARCH RESULTS FOR '{query}'")


def handle_filter_tasks(service: TodoService) -> None:
    """Filter tasks by status, priority, or category."""
    print("\n  --- FILTER TASKS ---")
    print("  Filter by:")
    print("    1. Completion Status (Pending / Completed)")
    print("    2. Priority Level (High / Medium / Low)")
    print("    3. Category")
    print("    4. Back to Main Menu")

    choice = read_choice("Select filter type", ["1", "2", "3", "4"], default="1")
    if choice == "1":
        status_choice = read_choice("Select status", ["Pending", "Completed"], default="Pending")
        filtered = service.filter_tasks(status=status_choice)
        render_task_table(filtered, f"{status_choice.upper()} TASKS")
    elif choice == "2":
        prio_choice = read_choice("Select priority", ALLOWED_PRIORITIES, default="High")
        filtered = service.filter_tasks(priority=prio_choice)
        render_task_table(filtered, f"{prio_choice.upper()} PRIORITY TASKS")
    elif choice == "3":
        cat_choice = read_string("Enter category name", allow_empty=False)
        filtered = service.filter_tasks(category=cat_choice)
        render_task_table(filtered, f"CATEGORY: '{cat_choice}'")


def handle_statistics(service: TodoService) -> None:
    """Render task completion and distribution metrics."""
    stats = service.get_statistics()
    render_statistics(stats)


def handle_clear_completed(service: TodoService) -> None:
    """Delete all completed tasks in bulk after confirmation."""
    completed_tasks = [t for t in service.get_all_tasks() if t.completed]
    if not completed_tasks:
        print("\n  [INFO] No completed tasks found to clear.")
        return

    confirm = read_yes_no(
        f"Are you sure you want to remove all {len(completed_tasks)} completed task(s)?",
        default=False,
    )
    if confirm:
        cleared_count = service.clear_completed()
        print(f"\n  [OK] Cleared {cleared_count} completed task(s).")
    else:
        print("\n  [INFO] Operation cancelled.")


def main() -> None:
    """Main CLI application loop."""
    print(BANNER)

    service = TodoService()

    # Inform user if repository encountered any issues during startup
    if service.startup_warnings:
        print_separator("!")
        print("  [!] Startup Notices:")
        for warning in service.startup_warnings:
            print(f"      - {warning}")
        print_separator("!")

    while True:
        print(MAIN_MENU)
        choice = input("  Select an option (0-9): ").strip()

        if choice == "1":
            handle_view_tasks(service)
        elif choice == "2":
            handle_add_task(service)
        elif choice == "3":
            handle_toggle_task(service)
        elif choice == "4":
            handle_edit_task(service)
        elif choice == "5":
            handle_delete_task(service)
        elif choice == "6":
            handle_search_tasks(service)
        elif choice == "7":
            handle_filter_tasks(service)
        elif choice == "8":
            handle_statistics(service)
        elif choice == "9":
            handle_clear_completed(service)
        elif choice == "0":
            print("\n  Exiting To-Do List Application. Have a productive day!\n")
            sys.exit(0)
        else:
            print("  [!] Invalid choice. Please enter a number between 0 and 9.")


if __name__ == "__main__":
    main()
