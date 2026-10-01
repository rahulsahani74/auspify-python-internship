"""
Service layer for the To-Do List Application.

Encapsulates all task business logic, CRUD operations, state transitions,
search, filtering, and statistical summaries.
"""

from typing import Any, Dict, List, Optional

from src.models import (
    ALLOWED_CATEGORIES,
    ALLOWED_PRIORITIES,
    DEFAULT_CATEGORY,
    DEFAULT_PRIORITY,
    Task,
)
from src.repository import TaskRepository


class TodoService:
    """Provides high-level business operations on To-Do tasks."""

    def __init__(self, repository: Optional[TaskRepository] = None):
        """Initialize service and load persisted tasks.

        Args:
            repository: TaskRepository instance. If None, default storage is used.
        """
        self.repository = repository or TaskRepository()
        self._tasks: List[Task] = []
        self._next_id: int = 1
        self.startup_warnings: List[str] = []
        self.reload()

    def reload(self) -> None:
        """Reload tasks from the persistence repository."""
        self._tasks, self._next_id, self.startup_warnings = self.repository.load_tasks()

    def save(self) -> None:
        """Persist current task state to storage."""
        self.repository.save_tasks(self._tasks, self._next_id)

    def get_all_tasks(self) -> List[Task]:
        """Return a list of all current tasks."""
        return list(self._tasks)

    def get_task(self, task_id: int) -> Optional[Task]:
        """Find a task by its unique ID.

        Args:
            task_id: Integer task identifier.

        Returns:
            The Task instance if found, otherwise None.
        """
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def add_task(
        self,
        title: str,
        description: str = "",
        priority: str = DEFAULT_PRIORITY,
        category: str = DEFAULT_CATEGORY,
        due_date: Optional[str] = None,
    ) -> Task:
        """Create, validate, and store a new task.

        Args:
            title: Task summary title (required).
            description: Extended notes or instructions.
            priority: Urgency ('High', 'Medium', 'Low').
            category: Category grouping ('General', 'Work', 'Personal', 'Study', 'Urgent').
            due_date: Optional due date in 'YYYY-MM-DD' format.

        Returns:
            The newly created Task instance.

        Raises:
            ValueError: If validation fails for title, priority, or date format.
        """
        task = Task(
            id=self._next_id,
            title=title,
            description=description,
            priority=priority,
            category=category,
            due_date=due_date,
        )

        errors = task.validate()
        if errors:
            raise ValueError("; ".join(errors))

        self._tasks.append(task)
        self._next_id += 1
        self.save()
        return task

    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> Task:
        """Update fields of an existing task.

        Args:
            task_id: ID of the task to update.
            title: New title, or None to keep existing.
            description: New description, or None to keep existing.
            priority: New priority, or None to keep existing.
            category: New category, or None to keep existing.
            due_date: New due date string, or None to keep existing.

        Returns:
            The updated Task instance.

        Raises:
            KeyError: If no task with task_id exists.
            ValueError: If updated fields fail validation.
        """
        task = self.get_task(task_id)
        if task is None:
            raise KeyError(f"Task with ID {task_id} not found.")

        # Stash current values for rollback if validation fails
        old_title = task.title
        old_description = task.description
        old_priority = task.priority
        old_category = task.category
        old_due_date = task.due_date

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = priority
        if category is not None:
            task.category = category
        if due_date is not None:
            # Empty string indicates clearing the due date
            task.due_date = due_date if due_date != "" else None

        errors = task.validate()
        if errors:
            # Rollback
            task.title = old_title
            task.description = old_description
            task.priority = old_priority
            task.category = old_category
            task.due_date = old_due_date
            raise ValueError("; ".join(errors))

        self.save()
        return task

    def mark_completed(self, task_id: int) -> Task:
        """Mark a task as completed.

        Args:
            task_id: ID of the task.

        Returns:
            The updated Task.

        Raises:
            KeyError: If task_id does not exist.
        """
        task = self.get_task(task_id)
        if task is None:
            raise KeyError(f"Task with ID {task_id} not found.")
        task.mark_completed()
        self.save()
        return task

    def mark_incomplete(self, task_id: int) -> Task:
        """Mark a task as incomplete / pending.

        Args:
            task_id: ID of the task.

        Returns:
            The updated Task.

        Raises:
            KeyError: If task_id does not exist.
        """
        task = self.get_task(task_id)
        if task is None:
            raise KeyError(f"Task with ID {task_id} not found.")
        task.mark_incomplete()
        self.save()
        return task

    def toggle_status(self, task_id: int) -> Task:
        """Toggle task status between completed and pending.

        Args:
            task_id: ID of the task.

        Returns:
            The updated Task.

        Raises:
            KeyError: If task_id does not exist.
        """
        task = self.get_task(task_id)
        if task is None:
            raise KeyError(f"Task with ID {task_id} not found.")
        task.toggle()
        self.save()
        return task

    def delete_task(self, task_id: int) -> Task:
        """Delete a task by its ID.

        Args:
            task_id: ID of the task to remove.

        Returns:
            The deleted Task instance.

        Raises:
            KeyError: If task_id does not exist.
        """
        task = self.get_task(task_id)
        if task is None:
            raise KeyError(f"Task with ID {task_id} not found.")
        self._tasks.remove(task)
        self.save()
        return task

    def clear_completed(self) -> int:
        """Remove all completed tasks.

        Returns:
            Number of tasks deleted.
        """
        initial_count = len(self._tasks)
        self._tasks = [t for t in self._tasks if not t.completed]
        removed_count = initial_count - len(self._tasks)
        if removed_count > 0:
            self.save()
        return removed_count

    def filter_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Task]:
        """Filter tasks according to status, priority, and category criteria.

        Args:
            status: 'completed', 'pending', or None for all.
            priority: 'High', 'Medium', 'Low', or None for all.
            category: Specific category name or None for all.

        Returns:
            Filtered list of tasks.
        """
        results = list(self._tasks)

        if status:
            norm_status = status.strip().lower()
            if norm_status in ("completed", "done", "finished", "true"):
                results = [t for t in results if t.completed]
            elif norm_status in ("pending", "incomplete", "todo", "false"):
                results = [t for t in results if not t.completed]

        if priority:
            norm_prio = priority.strip().capitalize()
            if norm_prio in ALLOWED_PRIORITIES:
                results = [t for t in results if t.priority == norm_prio]

        if category:
            norm_cat = category.strip().lower()
            results = [t for t in results if t.category.lower() == norm_cat]

        return results

    def search_tasks(self, query: str) -> List[Task]:
        """Search tasks by title, description, or category keyword.

        Args:
            query: Search string.

        Returns:
            List of matching tasks.
        """
        cleaned_query = query.strip().lower()
        if not cleaned_query:
            return list(self._tasks)

        return [
            t
            for t in self._tasks
            if cleaned_query in t.title.lower()
            or cleaned_query in t.description.lower()
            or cleaned_query in t.category.lower()
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate overall task and productivity metrics.

        Returns:
            Dictionary with total, completed, pending, completion rate,
            priority breakdown, and category breakdown.
        """
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks if t.completed)
        pending = total - completed
        rate = round((completed / total * 100), 1) if total > 0 else 0.0

        prio_counts = {p: 0 for p in ALLOWED_PRIORITIES}
        cat_counts: Dict[str, int] = {}

        for t in self._tasks:
            prio_counts[t.priority] = prio_counts.get(t.priority, 0) + 1
            cat_counts[t.category] = cat_counts.get(t.category, 0) + 1

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "completion_rate": rate,
            "priorities": prio_counts,
            "categories": cat_counts,
        }
