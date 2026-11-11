"""
task_manager.py — Production-grade task manager with JSON atomic persistence.
Run tests: python3 task_manager.py
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import unittest
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("task_manager")

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class TaskError(Exception):
    """Base exception for all task-manager errors."""


class TaskNotFoundError(TaskError):
    """Raised when a task ID cannot be found in the store."""

    def __init__(self, task_id: str) -> None:
        super().__init__(f"Task not found: '{task_id}'")
        self.task_id = task_id


class InvalidTaskError(TaskError):
    """Raised when task data fails validation."""


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------


@dataclass
class Task:
    """Immutable-friendly task entity."""

    id: str
    title: str
    description: str
    completed: bool
    created_at: str  # ISO-8601 UTC string — JSON-safe

    @staticmethod
    def create(title: str, description: str = "") -> "Task":
        """Validate, assign id/timestamp, and return a new Task."""
        title = title.strip()
        if not title:
            raise InvalidTaskError("title must not be empty or whitespace")
        return Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description.strip(),
            completed=False,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "Task":
        try:
            return Task(
                id=data["id"],
                title=data["title"],
                description=data.get("description", ""),
                completed=bool(data["completed"]),
                created_at=data["created_at"],
            )
        except KeyError as exc:
            raise InvalidTaskError(
                f"Malformed task record — missing key {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# TaskManager
# ---------------------------------------------------------------------------


class TaskManager:
    """
    Manages a collection of Tasks persisted to a JSON file.

    Persistence strategy: atomic write via NamedTemporaryFile + os.replace
    so that a crash mid-write never corrupts the data file.
    """

    def __init__(self, filepath: str) -> None:
        self._filepath = filepath
        self._tasks: dict[str, Task] = {}  # keyed by task.id for O(1) lookup
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_task(self, title: str, description: str = "") -> Task:
        """
        Create and persist a new task.

        Raises:
            InvalidTaskError: if title is blank.
        """
        task = Task.create(title, description)
        self._tasks[task.id] = task
        self._save()
        logger.info("Added task id=%s title=%r", task.id, task.title)
        return task

    def update_task(
        self,
        task_id: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> Task:
        """
        Partially update an existing task; only supplied kwargs are changed.

        Raises:
            TaskNotFoundError: if task_id does not exist.
            InvalidTaskError:  if the new title resolves to blank.
        """
        task = self._get_or_raise(task_id)

        new_title = task.title
        if title is not None:
            new_title = title.strip()
            if not new_title:
                raise InvalidTaskError("title must not be empty or whitespace")

        updated = Task(
            id=task.id,
            title=new_title,
            description=description.strip() if description is not None else task.description,
            completed=completed if completed is not None else task.completed,
            created_at=task.created_at,
        )
        self._tasks[task_id] = updated
        self._save()
        logger.info("Updated task id=%s", task_id)
        return updated

    def delete_task(self, task_id: str) -> None:
        """
        Remove a task permanently.

        Raises:
            TaskNotFoundError: if task_id does not exist.
        """
        self._get_or_raise(task_id)
        del self._tasks[task_id]
        self._save()
        logger.info("Deleted task id=%s", task_id)

    def list_tasks(self, include_completed: bool = True) -> list[Task]:
        """
        Return tasks sorted by created_at ascending.

        Args:
            include_completed: when False, only pending tasks are returned.
        """
        tasks = self._tasks.values()
        if not include_completed:
            tasks = (t for t in tasks if not t.completed)
        return sorted(tasks, key=lambda t: t.created_at)

    def get_task(self, task_id: str) -> Task:
        """
        Fetch a single task by id.

        Raises:
            TaskNotFoundError: if task_id does not exist.
        """
        return self._get_or_raise(task_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_or_raise(self, task_id: str) -> Task:
        try:
            return self._tasks[task_id]
        except KeyError:
            raise TaskNotFoundError(task_id)

    def _load(self) -> None:
        """Load tasks from JSON file; silently start fresh if absent or corrupt."""
        if not os.path.exists(self._filepath):
            logger.debug("No data file at %s — starting with empty store.", self._filepath)
            return
        try:
            with open(self._filepath, "r", encoding="utf-8") as fh:
                raw: list[dict] = json.load(fh)
            self._tasks = {r["id"]: Task.from_dict(r) for r in raw}
            logger.info("Loaded %d task(s) from %s", len(self._tasks), self._filepath)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error(
                "Failed to load %s: %s — starting with empty store.",
                self._filepath, exc,
            )
            self._tasks = {}

    def _save(self) -> None:
        """Atomic write: write to a temp file, then os.replace over target."""
        data = [t.to_dict() for t in self._tasks.values()]
        dir_path = os.path.dirname(self._filepath) or "."
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=dir_path,
                delete=False,
                suffix=".tmp",
            ) as tmp:
                json.dump(data, tmp, ensure_ascii=False, indent=2)
                tmp_path = tmp.name
            os.replace(tmp_path, self._filepath)
        except OSError as exc:
            logger.error("Failed to persist tasks: %s", exc)
            raise TaskError(f"Persistence failure: {exc}") from exc


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


class TestTask(unittest.TestCase):
    """Tests for the Task dataclass and its factory/serialisation helpers."""

    def test_create_happy_path_returns_valid_task(self) -> None:
        task = Task.create("Buy milk", "2% fat")
        self.assertEqual(task.title, "Buy milk")
        self.assertEqual(task.description, "2% fat")
        self.assertFalse(task.completed)
        self.assertTrue(uuid.UUID(task.id))
        self.assertIn("T", task.created_at)

    def test_create_strips_whitespace_from_title(self) -> None:
        task = Task.create("  Trim me  ")
        self.assertEqual(task.title, "Trim me")

    def test_create_empty_title_raises_invalid_task_error(self) -> None:
        with self.assertRaises(InvalidTaskError):
            Task.create("")

    def test_create_whitespace_only_title_raises_invalid_task_error(self) -> None:
        with self.assertRaises(InvalidTaskError):
            Task.create("   ")

    def test_to_dict_and_from_dict_roundtrip(self) -> None:
        original = Task.create("Round-trip", "desc")
        restored = Task.from_dict(original.to_dict())
        self.assertEqual(original, restored)

    def test_from_dict_missing_key_raises_invalid_task_error(self) -> None:
        with self.assertRaises(InvalidTaskError):
            Task.from_dict({"id": "x"})


class TestTaskManager(unittest.TestCase):
    """Integration-level tests for TaskManager using a real temp JSON file."""

    def setUp(self) -> None:
        fd, self.filepath = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.unlink(self.filepath)
        self.manager = TaskManager(self.filepath)

    def tearDown(self) -> None:
        if os.path.exists(self.filepath):
            os.unlink(self.filepath)

    # --- add_task ---

    def test_add_task_happy_path_returns_and_persists_task(self) -> None:
        task = self.manager.add_task("Walk the dog", "Morning walk")
        self.assertIsInstance(task, Task)
        self.assertEqual(task.title, "Walk the dog")
        self.assertEqual(len(self.manager.list_tasks()), 1)

    def test_add_task_empty_title_raises_invalid_task_error(self) -> None:
        with self.assertRaises(InvalidTaskError):
            self.manager.add_task("")

    def test_add_task_multiple_tasks_stored_correctly(self) -> None:
        self.manager.add_task("Task A")
        self.manager.add_task("Task B")
        self.assertEqual(len(self.manager.list_tasks()), 2)

    # --- update_task ---

    def test_update_task_title_and_completed(self) -> None:
        task = self.manager.add_task("Old title")
        updated = self.manager.update_task(task.id, title="New title", completed=True)
        self.assertEqual(updated.title, "New title")
        self.assertTrue(updated.completed)
        self.assertEqual(updated.id, task.id)
        self.assertEqual(updated.created_at, task.created_at)

    def test_update_task_not_found_raises_task_not_found_error(self) -> None:
        with self.assertRaises(TaskNotFoundError):
            self.manager.update_task("non-existent-id", title="X")

    def test_update_task_blank_title_raises_invalid_task_error(self) -> None:
        task = self.manager.add_task("Valid title")
        with self.assertRaises(InvalidTaskError):
            self.manager.update_task(task.id, title="   ")

    # --- delete_task ---

    def test_delete_task_removes_task(self) -> None:
        task = self.manager.add_task("Temporary")
        self.manager.delete_task(task.id)
        self.assertEqual(len(self.manager.list_tasks()), 0)

    def test_delete_task_not_found_raises_task_not_found_error(self) -> None:
        with self.assertRaises(TaskNotFoundError):
            self.manager.delete_task("ghost-id")

    # --- list_tasks ---

    def test_list_tasks_include_completed_false_filters_done_tasks(self) -> None:
        self.manager.add_task("Pending")
        done = self.manager.add_task("Done")
        self.manager.update_task(done.id, completed=True)
        pending = self.manager.list_tasks(include_completed=False)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].title, "Pending")

    def test_list_tasks_empty_store_returns_empty_list(self) -> None:
        self.assertEqual(self.manager.list_tasks(), [])

    # --- JSON persistence ---

    def test_json_persistence_survives_manager_reload(self) -> None:
        task = self.manager.add_task("Persist me", "important")
        reloaded = TaskManager(self.filepath)
        tasks = reloaded.list_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, task.id)
        self.assertEqual(tasks[0].title, task.title)
        self.assertEqual(tasks[0].description, task.description)

    def test_json_persistence_after_delete(self) -> None:
        t1 = self.manager.add_task("Keep")
        t2 = self.manager.add_task("Drop")
        self.manager.delete_task(t2.id)
        reloaded = TaskManager(self.filepath)
        tasks = reloaded.list_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, t1.id)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)

