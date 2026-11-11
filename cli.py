"""
cli.py — Argparse CLI wrapper around TaskManager.

Subcommands:
    add    --title TITLE [--desc DESC]
    list   [--all]
    update ID [--title TITLE] [--desc DESC] [--done | --not-done]
    delete ID

Exit codes:  0 = success,  1 = business / validation error.

Run tests:   python3 cli.py --test
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import tempfile
import unittest
from io import StringIO
from typing import Optional
from unittest.mock import patch

from task_manager import InvalidTaskError, Task, TaskError, TaskManager, TaskNotFoundError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "tasks.json"
)

_COL_ID = 36
_COL_STATUS = 9
_COL_TITLE = 30
_COL_DESC = 35
_COL_CREATED = 25

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_manager(filepath: str = DEFAULT_DATA_FILE) -> TaskManager:
    return TaskManager(filepath)


def _make_row(*cells: tuple[str, int]) -> str:
    return " | ".join(str(v).ljust(w) for v, w in cells)


def _print_table(tasks: list[Task], out=None) -> None:
    if out is None:
        out = sys.stdout  # lazy resolve so patch("sys.stdout") works in tests
    header = _make_row(
        ("ID", _COL_ID),
        ("Status", _COL_STATUS),
        ("Title", _COL_TITLE),
        ("Description", _COL_DESC),
        ("Created (UTC)", _COL_CREATED),
    )
    separator = "-" * len(header)
    print(header, file=out)
    print(separator, file=out)
    for t in tasks:
        status = "✓ done" if t.completed else "○ pending"
        print(
            _make_row(
                (t.id, _COL_ID),
                (status, _COL_STATUS),
                (t.title[:_COL_TITLE], _COL_TITLE),
                (t.description[:_COL_DESC], _COL_DESC),
                (t.created_at[:_COL_CREATED], _COL_CREATED),
            ),
            file=out,
        )
    count = len(tasks)
    print(f"\n{count} task{'s' if count != 1 else ''} listed.", file=out)


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------


def cmd_add(args: argparse.Namespace, manager: TaskManager) -> int:
    try:
        task = manager.add_task(args.title, args.desc or "")
    except InvalidTaskError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Task added — ID: {task.id}")
    return 0


def cmd_list(args: argparse.Namespace, manager: TaskManager) -> int:
    include_completed: bool = getattr(args, "all", False)
    tasks = manager.list_tasks(include_completed=include_completed)
    if not tasks:
        label = "tasks" if include_completed else "pending tasks"
        print(f"No {label} found.")
        return 0
    _print_table(tasks)
    return 0


def cmd_update(args: argparse.Namespace, manager: TaskManager) -> int:
    completed: Optional[bool] = None
    if getattr(args, "done", False):
        completed = True
    elif getattr(args, "not_done", False):
        completed = False

    if args.title is None and args.desc is None and completed is None:
        print(
            "Error: at least one of --title, --desc, --done, --not-done is required.",
            file=sys.stderr,
        )
        return 1

    try:
        task = manager.update_task(
            args.id,
            title=args.title,
            description=args.desc,
            completed=completed,
        )
    except TaskNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except InvalidTaskError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Task updated — ID: {task.id}")
    return 0


def cmd_delete(args: argparse.Namespace, manager: TaskManager) -> int:
    try:
        manager.delete_task(args.id)
    except TaskNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Task deleted — ID: {args.id}")
    return 0


# ---------------------------------------------------------------------------
# Parser factory
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Task Manager CLI",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--data-file",
        default=DEFAULT_DATA_FILE,
        metavar="PATH",
        help="Path to the JSON data file (default: tasks.json next to cli.py)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run the built-in unit-test suite instead of the CLI.",
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # add
    p_add = sub.add_parser("add", help="Add a new task.")
    p_add.add_argument("--title", required=True, help="Task title (required).")
    p_add.add_argument("--desc", default="", help="Optional description.")

    # list
    p_list = sub.add_parser("list", help="List tasks.")
    p_list.add_argument(
        "--all", action="store_true",
        help="Include completed tasks (default: pending only)."
    )

    # update
    p_update = sub.add_parser("update", help="Update an existing task.")
    p_update.add_argument("id", help="Task UUID.")
    p_update.add_argument("--title", default=None, help="New title.")
    p_update.add_argument("--desc", default=None, help="New description.")
    done_group = p_update.add_mutually_exclusive_group()
    done_group.add_argument("--done", action="store_true", help="Mark as completed.")
    done_group.add_argument(
        "--not-done", action="store_true", dest="not_done", help="Mark as pending."
    )

    # delete
    p_delete = sub.add_parser("delete", help="Delete a task by ID.")
    p_delete.add_argument("id", help="Task UUID.")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

_HANDLERS = {
    "add": cmd_add,
    "list": cmd_list,
    "update": cmd_update,
    "delete": cmd_delete,
}


def main(argv: Optional[list[str]] = None) -> int:
    """Parse *argv*, dispatch to handler, return exit code (0 or 1)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.test:
        _run_tests()
        return 0  # _run_tests calls sys.exit internally

    if args.command is None:
        parser.print_help()
        return 1

    logging.getLogger("task_manager").setLevel(logging.WARNING)

    manager = _build_manager(args.data_file)
    handler = _HANDLERS[args.command]
    return handler(args, manager)


def _run_tests() -> None:
    sys.argv = [sys.argv[0]]
    unittest.main(module=__name__, verbosity=2, exit=True)


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


class _CLITestBase(unittest.TestCase):
    """Base: fresh TaskManager backed by a temp JSON file per test."""

    def setUp(self) -> None:
        fd, self.data_file = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.unlink(self.data_file)
        logging.getLogger("task_manager").setLevel(logging.CRITICAL)

    def tearDown(self) -> None:
        if os.path.exists(self.data_file):
            os.unlink(self.data_file)

    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        full_argv = ["--data-file", self.data_file] + argv
        out_buf, err_buf = StringIO(), StringIO()
        with patch("sys.stdout", out_buf), patch("sys.stderr", err_buf):
            code = main(full_argv)
        return code, out_buf.getvalue(), err_buf.getvalue()

    def _add_task(self, title: str, desc: str = "") -> str:
        argv = ["add", "--title", title]
        if desc:
            argv += ["--desc", desc]
        code, out, _ = self._run(argv)
        self.assertEqual(code, 0, f"add_task failed: {out}")
        return out.strip().split("ID: ")[-1]


class TestCmdAdd(_CLITestBase):

    def test_add_happy_path_returns_exit_0_and_prints_id(self) -> None:
        code, out, err = self._run(["add", "--title", "Buy groceries", "--desc", "Weekly"])
        self.assertEqual(code, 0)
        self.assertIn("Task added", out)
        self.assertIn("ID:", out)
        self.assertEqual(err, "")

    def test_add_missing_title_flag_exits_nonzero(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            self._run(["add"])
        self.assertNotEqual(ctx.exception.code, 0)

    def test_add_empty_title_returns_exit_1_with_error_message(self) -> None:
        code, _, err = self._run(["add", "--title", ""])
        self.assertEqual(code, 1)
        self.assertIn("Error", err)

    def test_add_whitespace_title_returns_exit_1(self) -> None:
        code, _, err = self._run(["add", "--title", "   "])
        self.assertEqual(code, 1)
        self.assertIn("Error", err)

    def test_add_without_desc_succeeds(self) -> None:
        code, out, _ = self._run(["add", "--title", "No description"])
        self.assertEqual(code, 0)
        self.assertIn("Task added", out)


class TestCmdList(_CLITestBase):

    def test_list_empty_store_returns_exit_0_with_no_tasks_message(self) -> None:
        code, out, _ = self._run(["list"])
        self.assertEqual(code, 0)
        self.assertIn("No pending tasks found", out)

    def test_list_shows_pending_task(self) -> None:
        self._add_task("Task Alpha")
        code, out, _ = self._run(["list"])
        self.assertEqual(code, 0)
        self.assertIn("Task Alpha", out)

    def test_list_hides_completed_task_by_default(self) -> None:
        task_id = self._add_task("Done task")
        self._run(["update", task_id, "--done"])
        code, out, _ = self._run(["list"])
        self.assertEqual(code, 0)
        self.assertIn("No pending tasks found", out)

    def test_list_all_shows_completed_tasks(self) -> None:
        task_id = self._add_task("Done task")
        self._run(["update", task_id, "--done"])
        code, out, _ = self._run(["list", "--all"])
        self.assertEqual(code, 0)
        self.assertIn("Done task", out)
        self.assertIn("done", out)

    def test_list_table_contains_header_columns(self) -> None:
        self._add_task("Header test")
        _, out, _ = self._run(["list"])
        for col in ("ID", "Status", "Title", "Description", "Created"):
            self.assertIn(col, out)


class TestCmdUpdate(_CLITestBase):

    def test_update_title_returns_exit_0(self) -> None:
        task_id = self._add_task("Original")
        code, out, _ = self._run(["update", task_id, "--title", "Updated"])
        self.assertEqual(code, 0)
        self.assertIn("Task updated", out)

    def test_update_mark_done_returns_exit_0(self) -> None:
        task_id = self._add_task("Pending task")
        code, out, _ = self._run(["update", task_id, "--done"])
        self.assertEqual(code, 0)
        self.assertIn("Task updated", out)

    def test_update_mark_not_done_returns_exit_0(self) -> None:
        task_id = self._add_task("Done task")
        self._run(["update", task_id, "--done"])
        code, out, _ = self._run(["update", task_id, "--not-done"])
        self.assertEqual(code, 0)
        self.assertIn("Task updated", out)

    def test_update_nonexistent_id_returns_exit_1(self) -> None:
        code, _, err = self._run(["update", "00000000-0000-0000-0000-000000000000", "--done"])
        self.assertEqual(code, 1)
        self.assertIn("Error", err)

    def test_update_blank_title_returns_exit_1(self) -> None:
        task_id = self._add_task("Real title")
        code, _, err = self._run(["update", task_id, "--title", "   "])
        self.assertEqual(code, 1)
        self.assertIn("Error", err)

    def test_update_no_fields_returns_exit_1(self) -> None:
        task_id = self._add_task("Nothing to update")
        code, _, err = self._run(["update", task_id])
        self.assertEqual(code, 1)
        self.assertIn("Error", err)

    def test_update_desc_only_returns_exit_0(self) -> None:
        task_id = self._add_task("Task")
        code, out, _ = self._run(["update", task_id, "--desc", "New description"])
        self.assertEqual(code, 0)
        self.assertIn("Task updated", out)


class TestCmdDelete(_CLITestBase):

    def test_delete_existing_task_returns_exit_0(self) -> None:
        task_id = self._add_task("Ephemeral")
        code, out, _ = self._run(["delete", task_id])
        self.assertEqual(code, 0)
        self.assertIn("Task deleted", out)
        self.assertIn(task_id, out)

    def test_delete_nonexistent_id_returns_exit_1(self) -> None:
        code, _, err = self._run(["delete", "00000000-0000-0000-0000-000000000000"])
        self.assertEqual(code, 1)
        self.assertIn("Error", err)

    def test_delete_removes_task_from_list(self) -> None:
        task_id = self._add_task("To be removed")
        self._run(["delete", task_id])
        code, out, _ = self._run(["list", "--all"])
        self.assertEqual(code, 0)
        self.assertNotIn(task_id, out)


class TestCmdNoSubcommand(_CLITestBase):

    def test_no_subcommand_returns_exit_1_and_prints_usage(self) -> None:
        code, out, _ = self._run([])
        self.assertEqual(code, 1)
        self.assertIn("usage", out.lower())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())



