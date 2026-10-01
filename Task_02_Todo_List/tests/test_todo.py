"""
Comprehensive Automated Unit Tests for Task 02: To-Do List Application.

Covers:
- Task data model: creation, validation, status transitions, serialization/deserialization
- TaskRepository: atomic persistence, missing file, empty file, corrupted JSON recovery, backups
- TodoService: CRUD operations, ID auto-increment, updates with rollback, bulk clear
- Filtering & Search: status, priority, category, case-insensitive keyword queries
- Task Statistics: metric calculations and distribution breakdowns
- Round-trip persistence across application restarts
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models import (
    ALLOWED_CATEGORIES,
    ALLOWED_PRIORITIES,
    Task,
    validate_date_format,
)
from src.repository import TaskRepository
from src.service import TodoService


# ===========================================================================
# 1. Models & Validation Tests
# ===========================================================================

class TestTaskModel(unittest.TestCase):
    """Test suite for the Task data model and validation."""

    def test_task_default_initialization(self):
        task = Task(id=1, title="Write unit tests")
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Write unit tests")
        self.assertEqual(task.description, "")
        self.assertFalse(task.completed)
        self.assertEqual(task.priority, "Medium")
        self.assertEqual(task.category, "General")
        self.assertIsNone(task.due_date)
        self.assertIsNone(task.completed_at)
        self.assertEqual(task.status_label, "[ ]")
        self.assertEqual(task.validate(), [])

    def test_task_custom_initialization(self):
        task = Task(
            id=5,
            title="Deploy release",
            description="Run deployment pipeline",
            completed=True,
            priority="High",
            category="Work",
            due_date="2026-10-15",
            completed_at="2026-09-30 20:00",
        )
        self.assertEqual(task.id, 5)
        self.assertTrue(task.completed)
        self.assertEqual(task.priority, "High")
        self.assertEqual(task.category, "Work")
        self.assertEqual(task.due_date, "2026-10-15")
        self.assertEqual(task.status_label, "[X]")
        self.assertEqual(task.validate(), [])

    def test_validation_empty_title_fails(self):
        task = Task(id=1, title="")
        errors = task.validate()
        self.assertTrue(any("title cannot be empty" in e.lower() for e in errors))

        task_spaces = Task(id=1, title="    ")
        self.assertTrue(any("title cannot be empty" in e.lower() for e in task_spaces.validate()))

    def test_validation_title_length_exceeded_fails(self):
        long_title = "A" * 201
        task = Task(id=1, title=long_title)
        errors = task.validate()
        self.assertTrue(any("exceeds maximum length" in e.lower() for e in errors))

    def test_validation_invalid_id_fails(self):
        task_neg = Task(id=-1, title="Test")
        self.assertTrue(any("positive integer" in e.lower() for e in task_neg.validate()))

        task_zero = Task(id=0, title="Test")
        self.assertTrue(any("positive integer" in e.lower() for e in task_zero.validate()))

    def test_validation_invalid_priority_fails(self):
        task = Task(id=1, title="Test", priority="UrgentCritical")
        errors = task.validate()
        self.assertTrue(any("invalid priority" in e.lower() for e in errors))

    def test_validation_due_date_format(self):
        task_valid = Task(id=1, title="Test", due_date="2026-12-31")
        self.assertEqual(task_valid.validate(), [])

        task_invalid = Task(id=1, title="Test", due_date="31-12-2026")
        self.assertTrue(any("must follow 'yyyy-mm-dd'" in e.lower() for e in task_invalid.validate()))

        task_invalid_month = Task(id=1, title="Test", due_date="2026-13-01")
        self.assertTrue(any("must follow 'yyyy-mm-dd'" in e.lower() for e in task_invalid_month.validate()))

    def test_status_transitions(self):
        task = Task(id=1, title="Status test")
        self.assertFalse(task.completed)
        self.assertIsNone(task.completed_at)

        task.mark_completed()
        self.assertTrue(task.completed)
        self.assertIsNotNone(task.completed_at)

        task.mark_incomplete()
        self.assertFalse(task.completed)
        self.assertIsNone(task.completed_at)

        new_status = task.toggle()
        self.assertTrue(new_status)
        self.assertTrue(task.completed)

        new_status = task.toggle()
        self.assertFalse(new_status)
        self.assertFalse(task.completed)

    def test_to_dict_and_from_dict_roundtrip(self):
        task = Task(
            id=10,
            title="Code review",
            description="Review PR #42",
            completed=True,
            priority="Low",
            category="Study",
            due_date="2026-11-01",
            completed_at="2026-09-30 18:30",
        )
        task_dict = task.to_dict()
        reconstructed = Task.from_dict(task_dict)
        self.assertEqual(reconstructed.id, task.id)
        self.assertEqual(reconstructed.title, task.title)
        self.assertEqual(reconstructed.description, task.description)
        self.assertEqual(reconstructed.completed, task.completed)
        self.assertEqual(reconstructed.priority, task.priority)
        self.assertEqual(reconstructed.category, task.category)
        self.assertEqual(reconstructed.due_date, task.due_date)
        self.assertEqual(reconstructed.completed_at, task.completed_at)

    def test_from_dict_with_corrupt_or_missing_fields(self):
        # Empty dict should provide sensible fallbacks
        task = Task.from_dict({})
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Untitled Task")
        self.assertEqual(task.priority, "Medium")
        self.assertEqual(task.category, "General")
        self.assertFalse(task.completed)

        # Corrupt priority and due_date fall back gracefully
        task2 = Task.from_dict({
            "id": "abc",
            "title": "Clean room",
            "priority": "SuperHigh",
            "due_date": "not-a-date",
        })
        self.assertEqual(task2.id, 1)
        self.assertEqual(task2.priority, "Medium")
        self.assertIsNone(task2.due_date)


# ===========================================================================
# 2. Repository & Persistence Tests
# ===========================================================================

class TestTaskRepository(unittest.TestCase):
    """Test suite for persistence, atomic saving, and corrupted file handling."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_file = Path(self.temp_dir) / "tasks.json"
        self.repo = TaskRepository(self.storage_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_non_existent_file(self):
        tasks, next_id, warnings = self.repo.load_tasks()
        self.assertEqual(tasks, [])
        self.assertEqual(next_id, 1)
        self.assertEqual(warnings, [])

    def test_save_and_load_tasks(self):
        task1 = Task(id=1, title="Task 1", priority="High")
        task2 = Task(id=2, title="Task 2", priority="Low", completed=True)
        self.repo.save_tasks([task1, task2], next_id=3)

        self.assertTrue(self.storage_file.exists())

        loaded_tasks, next_id, warnings = self.repo.load_tasks()
        self.assertEqual(len(loaded_tasks), 2)
        self.assertEqual(next_id, 3)
        self.assertEqual(warnings, [])
        self.assertEqual(loaded_tasks[0].title, "Task 1")
        self.assertEqual(loaded_tasks[1].title, "Task 2")
        self.assertTrue(loaded_tasks[1].completed)

    def test_load_empty_file(self):
        self.storage_file.write_text("", encoding="utf-8")
        tasks, next_id, warnings = self.repo.load_tasks()
        self.assertEqual(tasks, [])
        self.assertEqual(next_id, 1)
        self.assertTrue(any("empty" in w.lower() for w in warnings))

    def test_load_corrupted_json_syntax(self):
        self.storage_file.write_text("{ this is NOT valid JSON }", encoding="utf-8")
        tasks, next_id, warnings = self.repo.load_tasks()
        self.assertEqual(tasks, [])
        self.assertEqual(next_id, 1)
        self.assertTrue(any("invalid json" in w.lower() for w in warnings))

        # Verify a backup was created
        backup_files = list(Path(self.temp_dir).glob("*_corrupted_*.bak"))
        self.assertEqual(len(backup_files), 1)

    def test_load_corrupted_json_schema(self):
        # JSON is valid syntax, but data is an integer
        self.storage_file.write_text("12345", encoding="utf-8")
        tasks, next_id, warnings = self.repo.load_tasks()
        self.assertEqual(tasks, [])
        self.assertEqual(next_id, 1)
        self.assertTrue(any("unexpected json structure" in w.lower() for w in warnings))

    def test_load_skipped_corrupted_task_record(self):
        payload = {
            "version": "1.0",
            "next_id": 3,
            "tasks": [
                {"id": 1, "title": "Valid task", "priority": "High"},
                "This is not a dict",
                {"id": 2, "title": "Another valid task", "priority": "Low"},
            ],
        }
        self.storage_file.write_text(json.dumps(payload), encoding="utf-8")
        tasks, next_id, warnings = self.repo.load_tasks()
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].title, "Valid task")
        self.assertEqual(tasks[1].title, "Another valid task")
        self.assertTrue(any("non-dictionary" in w.lower() for w in warnings))

    def test_next_id_recomputed_if_out_of_sync(self):
        # File reports next_id=1, but tasks exist with id=10
        payload = {
            "version": "1.0",
            "next_id": 1,
            "tasks": [{"id": 10, "title": "Task 10"}],
        }
        self.storage_file.write_text(json.dumps(payload), encoding="utf-8")
        tasks, next_id, _ = self.repo.load_tasks()
        self.assertEqual(next_id, 11)


# ===========================================================================
# 3. Service Layer & CRUD Tests
# ===========================================================================

class TestTodoService(unittest.TestCase):
    """Test suite for TodoService CRUD, filtering, search, and stats."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_file = Path(self.temp_dir) / "tasks.json"
        self.repo = TaskRepository(self.storage_file)
        self.service = TodoService(self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_task_success(self):
        task = self.service.add_task(
            title="Read book",
            description="Chapter 4",
            priority="High",
            category="Study",
            due_date="2026-10-20",
        )
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Read book")
        self.assertEqual(len(self.service.get_all_tasks()), 1)

        # Adding a second task auto-increments ID
        task2 = self.service.add_task(title="Exercise")
        self.assertEqual(task2.id, 2)
        self.assertEqual(len(self.service.get_all_tasks()), 2)

    def test_add_task_invalid_title_raises(self):
        with self.assertRaises(ValueError):
            self.service.add_task(title="")

    def test_add_task_invalid_priority_raises(self):
        with self.assertRaises(ValueError):
            self.service.add_task(title="Task", priority="InvalidPrio")

    def test_add_task_invalid_due_date_raises(self):
        with self.assertRaises(ValueError):
            self.service.add_task(title="Task", due_date="2026/10/20")

    def test_get_task(self):
        t1 = self.service.add_task(title="Task 1")
        self.assertEqual(self.service.get_task(t1.id), t1)
        self.assertIsNone(self.service.get_task(999))

    def test_update_task_success(self):
        t = self.service.add_task(title="Original", priority="Low")
        updated = self.service.update_task(
            task_id=t.id,
            title="Updated Title",
            priority="High",
            category="Work",
            due_date="2026-10-30",
        )
        self.assertEqual(updated.title, "Updated Title")
        self.assertEqual(updated.priority, "High")
        self.assertEqual(updated.category, "Work")
        self.assertEqual(updated.due_date, "2026-10-30")

    def test_update_task_non_existent_id(self):
        with self.assertRaises(KeyError):
            self.service.update_task(task_id=999, title="Non-existent")

    def test_update_task_invalid_rollback(self):
        t = self.service.add_task(title="Stable Title", priority="Medium")
        with self.assertRaises(ValueError):
            self.service.update_task(task_id=t.id, priority="InvalidPrio")

        # Confirm rollback to previous values
        current = self.service.get_task(t.id)
        self.assertEqual(current.title, "Stable Title")
        self.assertEqual(current.priority, "Medium")

    def test_toggle_and_mark_completion(self):
        t = self.service.add_task(title="Complete me")
        self.assertFalse(t.completed)

        self.service.mark_completed(t.id)
        self.assertTrue(self.service.get_task(t.id).completed)
        self.assertIsNotNone(self.service.get_task(t.id).completed_at)

        self.service.mark_incomplete(t.id)
        self.assertFalse(self.service.get_task(t.id).completed)
        self.assertIsNone(self.service.get_task(t.id).completed_at)

        self.service.toggle_status(t.id)
        self.assertTrue(self.service.get_task(t.id).completed)

    def test_delete_task(self):
        t1 = self.service.add_task(title="Task 1")
        t2 = self.service.add_task(title="Task 2")

        deleted = self.service.delete_task(t1.id)
        self.assertEqual(deleted.id, t1.id)
        self.assertEqual(len(self.service.get_all_tasks()), 1)
        self.assertIsNone(self.service.get_task(t1.id))

        with self.assertRaises(KeyError):
            self.service.delete_task(999)

    def test_clear_completed(self):
        self.service.add_task(title="Task 1")
        t2 = self.service.add_task(title="Task 2")
        t3 = self.service.add_task(title="Task 3")
        self.service.mark_completed(t2.id)
        self.service.mark_completed(t3.id)

        cleared_count = self.service.clear_completed()
        self.assertEqual(cleared_count, 2)
        remaining = self.service.get_all_tasks()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].title, "Task 1")

    def test_filter_tasks(self):
        self.service.add_task(title="T1", priority="High", category="Work")
        t2 = self.service.add_task(title="T2", priority="Low", category="Personal")
        t3 = self.service.add_task(title="T3", priority="High", category="Work")
        self.service.mark_completed(t2.id)
        self.service.mark_completed(t3.id)

        # Filter by status
        pending = self.service.filter_tasks(status="pending")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].title, "T1")

        completed = self.service.filter_tasks(status="completed")
        self.assertEqual(len(completed), 2)

        # Filter by priority
        high = self.service.filter_tasks(priority="High")
        self.assertEqual(len(high), 2)

        # Filter by category
        personal = self.service.filter_tasks(category="Personal")
        self.assertEqual(len(personal), 1)
        self.assertEqual(personal[0].title, "T2")

        # Multi-filter
        work_completed = self.service.filter_tasks(status="completed", category="Work")
        self.assertEqual(len(work_completed), 1)
        self.assertEqual(work_completed[0].title, "T3")

    def test_search_tasks(self):
        self.service.add_task(title="Prepare Presentation", description="Slides for conference", category="Work")
        self.service.add_task(title="Buy Groceries", description="Milk, cheese, butter", category="Personal")
        self.service.add_task(title="Study Algorithms", description="Dynamic programming", category="Study")

        # Title search
        res1 = self.service.search_tasks("presentation")
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0].title, "Prepare Presentation")

        # Description search
        res2 = self.service.search_tasks("cheese")
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2[0].title, "Buy Groceries")

        # Category search
        res3 = self.service.search_tasks("study")
        self.assertEqual(len(res3), 1)
        self.assertEqual(res3[0].title, "Study Algorithms")

        # Empty search returns all
        self.assertEqual(len(self.service.search_tasks("")), 3)

        # No match returns empty list
        self.assertEqual(len(self.service.search_tasks("nonexistentkeyword")), 0)

    def test_statistics(self):
        self.service.add_task(title="T1", priority="High", category="Work")
        t2 = self.service.add_task(title="T2", priority="Low", category="Work")
        self.service.mark_completed(t2.id)

        stats = self.service.get_statistics()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["pending"], 1)
        self.assertEqual(stats["completion_rate"], 50.0)
        self.assertEqual(stats["priorities"]["High"], 1)
        self.assertEqual(stats["priorities"]["Low"], 1)
        self.assertEqual(stats["categories"]["Work"], 2)

    def test_persistence_across_restart(self):
        # Add tasks in service session 1
        t1 = self.service.add_task(title="Persist me", priority="High", due_date="2026-11-20")
        self.service.mark_completed(t1.id)

        # Instantiate a brand new service session connecting to the same repository
        new_service = TodoService(self.repo)
        all_tasks = new_service.get_all_tasks()
        self.assertEqual(len(all_tasks), 1)
        self.assertEqual(all_tasks[0].id, t1.id)
        self.assertEqual(all_tasks[0].title, "Persist me")
        self.assertTrue(all_tasks[0].completed)
        self.assertEqual(all_tasks[0].priority, "High")
        self.assertEqual(all_tasks[0].due_date, "2026-11-20")

        # New tasks created in session 2 receive next incremented ID
        t2 = new_service.add_task(title="Next task")
        self.assertEqual(t2.id, 2)


if __name__ == "__main__":
    unittest.main()
