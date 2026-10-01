"""
Data models for the To-Do List Application.

Defines the Task dataclass, priority and category enumerations/constants,
validation rules, and serialization/deserialization logic.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


ALLOWED_PRIORITIES = ("High", "Medium", "Low")
DEFAULT_PRIORITY = "Medium"

ALLOWED_CATEGORIES = ("General", "Work", "Personal", "Study", "Urgent")
DEFAULT_CATEGORY = "General"


def current_timestamp() -> str:
    """Return the current local timestamp formatted as YYYY-MM-DD HH:MM."""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def validate_date_format(date_str: str) -> bool:
    """Check if a date string strictly follows YYYY-MM-DD format."""
    if not date_str:
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


@dataclass
class Task:
    """Represents a single to-do task item.

    Attributes:
        id: Unique positive integer identifier.
        title: Short title or summary of the task (required).
        description: Extended description or notes (optional).
        completed: Boolean flag indicating if task is finished.
        priority: Urgency level ('High', 'Medium', 'Low').
        category: Task grouping ('General', 'Work', 'Personal', 'Study', 'Urgent').
        created_at: Timestamp when task was created (YYYY-MM-DD HH:MM).
        due_date: Optional target completion date (YYYY-MM-DD).
        completed_at: Optional timestamp when task was marked complete.
    """

    id: int
    title: str
    description: str = ""
    completed: bool = False
    priority: str = DEFAULT_PRIORITY
    category: str = DEFAULT_CATEGORY
    created_at: str = field(default_factory=current_timestamp)
    due_date: Optional[str] = None
    completed_at: Optional[str] = None

    def validate(self) -> List[str]:
        """Validate task fields and return a list of error descriptions.

        Returns:
            List of validation error strings. Empty list indicates validity.
        """
        errors: List[str] = []

        if not isinstance(self.id, int) or self.id <= 0:
            errors.append(f"Task ID must be a positive integer, got {self.id!r}.")

        cleaned_title = self.title.strip() if isinstance(self.title, str) else ""
        if not cleaned_title:
            errors.append("Task title cannot be empty or purely whitespace.")
        elif len(cleaned_title) > 200:
            errors.append(f"Task title exceeds maximum length of 200 characters (length: {len(cleaned_title)}).")

        normalized_priority = self.priority.capitalize() if isinstance(self.priority, str) else ""
        if normalized_priority not in ALLOWED_PRIORITIES:
            errors.append(
                f"Invalid priority '{self.priority}'. Allowed: {', '.join(ALLOWED_PRIORITIES)}."
            )

        if self.due_date and not validate_date_format(self.due_date):
            errors.append(
                f"Due date '{self.due_date}' must follow 'YYYY-MM-DD' format (e.g. 2026-10-15)."
            )

        return errors

    def mark_completed(self) -> None:
        """Mark task as finished and record completion timestamp."""
        self.completed = True
        self.completed_at = current_timestamp()

    def mark_incomplete(self) -> None:
        """Mark task as pending and clear completion timestamp."""
        self.completed = False
        self.completed_at = None

    def toggle(self) -> bool:
        """Toggle task completion status.

        Returns:
            The new boolean completion status.
        """
        if self.completed:
            self.mark_incomplete()
        else:
            self.mark_completed()
        return self.completed

    @property
    def status_label(self) -> str:
        """Return a human-readable status badge."""
        return "[X]" if self.completed else "[ ]"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize task instance to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "title": self.title.strip(),
            "description": self.description.strip(),
            "completed": self.completed,
            "priority": self.priority.capitalize() if self.priority in ALLOWED_PRIORITIES else DEFAULT_PRIORITY,
            "category": self.category.strip() or DEFAULT_CATEGORY,
            "created_at": self.created_at,
            "due_date": self.due_date,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Deserialize a dictionary to a Task instance with resilient fallbacks.

        Args:
            data: Dictionary containing serialized task data.

        Returns:
            A populated Task instance.
        """
        raw_id = data.get("id")
        task_id = int(raw_id) if raw_id is not None and str(raw_id).isdigit() else 1

        raw_title = str(data.get("title", "Untitled Task")).strip()
        if not raw_title:
            raw_title = "Untitled Task"

        raw_desc = str(data.get("description", "")).strip()

        completed = bool(data.get("completed", False))

        raw_prio = str(data.get("priority", DEFAULT_PRIORITY)).capitalize()
        priority = raw_prio if raw_prio in ALLOWED_PRIORITIES else DEFAULT_PRIORITY

        raw_cat = str(data.get("category", DEFAULT_CATEGORY)).strip()
        category = raw_cat if raw_cat else DEFAULT_CATEGORY

        created_at = str(data.get("created_at") or current_timestamp())

        due_date = data.get("due_date")
        if due_date and not validate_date_format(str(due_date)):
            due_date = None
        elif due_date:
            due_date = str(due_date)

        completed_at = data.get("completed_at")
        if completed_at:
            completed_at = str(completed_at)

        return cls(
            id=task_id,
            title=raw_title,
            description=raw_desc,
            completed=completed,
            priority=priority,
            category=category,
            created_at=created_at,
            due_date=due_date,
            completed_at=completed_at,
        )
