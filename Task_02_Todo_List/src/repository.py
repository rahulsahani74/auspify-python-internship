"""
Repository layer for file persistence.

Handles loading and saving tasks to a local JSON file with atomic write
guarantees, corrupted file recovery, automated backups, and schema safety.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from src.models import Task


DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_STORAGE_FILE = DEFAULT_DATA_DIR / "tasks.json"


class TaskRepository:
    """Manages serialization and persistence of Tasks in JSON format.

    Ensures atomic disk writes and fault-tolerant recovery against missing,
    empty, or malformed data files.
    """

    def __init__(self, filepath: Path | str = DEFAULT_STORAGE_FILE):
        """Initialize the repository with a target file path.

        Args:
            filepath: Path to the JSON persistence file.
        """
        self.filepath = Path(filepath)

    def _ensure_directory(self) -> None:
        """Create parent directory if it does not already exist."""
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def load_tasks(self) -> Tuple[List[Task], int, List[str]]:
        """Load tasks and the next available ID from the JSON file.

        Returns:
            A tuple of (tasks_list, next_id, warnings_list).
            If the file does not exist, returns ([], 1, []).
            If corrupted, creates a backup file and returns empty list with warnings.
        """
        warnings: List[str] = []

        if not self.filepath.exists():
            return [], 1, warnings

        try:
            content = self.filepath.read_text(encoding="utf-8").strip()
        except Exception as exc:
            warnings.append(f"Failed to read file '{self.filepath.name}': {exc}")
            return [], 1, warnings

        if not content:
            warnings.append(f"Data file '{self.filepath.name}' is empty. Initializing new task list.")
            return [], 1, warnings

        try:
            data = json.loads(content)
        except json.JSONDecodeError as err:
            # Corrupted JSON: create safety backup and recover gracefully
            backup_path = self._create_backup("corrupted")
            warnings.append(
                f"Data file '{self.filepath.name}' contained invalid JSON (backed up to {backup_path.name}): {err}"
            )
            return [], 1, warnings

        tasks: List[Task] = []
        next_id = 1

        # Support both new dictionary schema {version, next_id, tasks} and plain list schema
        raw_task_list: list = []
        if isinstance(data, dict):
            next_id = int(data.get("next_id", 1)) if str(data.get("next_id", "")).isdigit() else 1
            raw_task_list = data.get("tasks", [])
            if not isinstance(raw_task_list, list):
                warnings.append("Schema warning: 'tasks' key was not a list. Resetting task list.")
                raw_task_list = []
        elif isinstance(data, list):
            raw_task_list = data
        else:
            backup_path = self._create_backup("invalid_schema")
            warnings.append(
                f"Unexpected JSON structure in '{self.filepath.name}' (backed up to {backup_path.name}). Resetting tasks."
            )
            return [], 1, warnings

        for index, item in enumerate(raw_task_list, start=1):
            if isinstance(item, dict):
                try:
                    task = Task.from_dict(item)
                    tasks.append(task)
                except Exception as exc:
                    warnings.append(f"Skipped corrupted task entry #{index}: {exc}")
            else:
                warnings.append(f"Skipped non-dictionary task record at index {index}.")

        # Ensure next_id is strictly greater than all existing task IDs
        max_existing_id = max((t.id for t in tasks), default=0)
        if next_id <= max_existing_id:
            next_id = max_existing_id + 1

        return tasks, next_id, warnings

    def save_tasks(self, tasks: List[Task], next_id: int) -> None:
        """Atomically write tasks and next_id to the persistence file.

        Uses a temporary file in the same directory and replaces it to ensure
        interrupted writes never corrupt existing persistent data.

        Args:
            tasks: List of Task instances to serialize.
            next_id: Next sequential ID counter.
        """
        self._ensure_directory()

        payload = {
            "version": "1.0",
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "next_id": next_id,
            "tasks": [task.to_dict() for task in tasks],
        }

        # Write to temporary file first in the same directory (required for atomic rename)
        temp_filepath = self.filepath.with_suffix(".tmp")
        try:
            with open(temp_filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            # Atomic replace
            os.replace(temp_filepath, self.filepath)
        except Exception:
            # Clean up temporary file if write failed
            if temp_filepath.exists():
                try:
                    temp_filepath.unlink()
                except OSError:
                    pass
            raise

    def _create_backup(self, tag: str) -> Path:
        """Create a timestamped backup copy of the current file.

        Args:
            tag: Descriptive label for the backup (e.g. 'corrupted').

        Returns:
            The Path of the created backup file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{self.filepath.stem}_{tag}_{timestamp}{self.filepath.suffix}.bak"
        backup_path = self.filepath.parent / backup_filename
        try:
            shutil.copy2(self.filepath, backup_path)
        except OSError:
            pass
        return backup_path
