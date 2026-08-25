from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from workspace_paths import (  # noqa: E402
    infer_active_workspace_from_session,
    resolve_legacy_workspace,
    resolve_workspace,
)


DIRECTORIES = {"plans": "output/plans", "tests": "output/tests"}


class WorkspacePathsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(prefix="auto-test-project-paths-")
        self.project_root = Path(self.tempdir.name) / "project"
        self.project_root.mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_explicit_task_root_is_reused_without_overwriting_readme(self) -> None:
        task_root = self.project_root / ".bensz-api" / "task-20260808-2204-project-test"
        first = resolve_workspace(
            project_root=self.project_root,
            task_root_arg=str(task_root),
            task_description="ignored",
            directories=DIRECTORIES,
            create=True,
        )
        self.assertTrue(first.created_task_root)
        self.assertTrue(first.plans_dir.is_dir())
        self.assertTrue(first.tests_dir.is_dir())

        readme = task_root / "README.md"
        readme.write_text("custom task readme\n", encoding="utf-8")
        second = resolve_workspace(
            project_root=self.project_root,
            task_root_arg=str(task_root),
            task_description="ignored",
            directories=DIRECTORIES,
            create=True,
        )
        self.assertFalse(second.created_task_root)
        self.assertEqual(second.task_root, first.task_root)
        self.assertEqual(readme.read_text(encoding="utf-8"), "custom task readme\n")

    def test_new_task_allocation_uses_short_collision_suffix(self) -> None:
        now = dt.datetime(2026, 8, 8, 22, 4)
        first = resolve_workspace(
            project_root=self.project_root,
            task_root_arg="",
            task_description="项目测试",
            directories=DIRECTORIES,
            create=True,
            now=now,
        )
        second = resolve_workspace(
            project_root=self.project_root,
            task_root_arg="",
            task_description="项目测试",
            directories=DIRECTORIES,
            create=True,
            now=now,
        )
        self.assertEqual(first.task_root.name, "task-20260808-2204-项目测试")
        self.assertEqual(second.task_root.name, "task-20260808-2204-项目测试-a")

    def test_invalid_or_escaping_task_roots_are_rejected(self) -> None:
        invalid = [
            "../task-20260808-2204-escape",
            str(Path(self.tempdir.name) / "task-20260808-2204-outside"),
            ".bensz-api/not-a-task",
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolve_workspace(
                    project_root=self.project_root,
                    task_root_arg=value,
                    task_description="ignored",
                    directories=DIRECTORIES,
                    create=True,
                )

    def test_invalid_directory_config_does_not_allocate_task_root(self) -> None:
        with self.assertRaises(ValueError):
            resolve_workspace(
                project_root=self.project_root,
                task_root_arg="",
                task_description="invalid-config",
                directories={"plans": "../escape", "tests": "output/tests"},
                create=True,
            )
        self.assertFalse((self.project_root / ".bensz-api").exists())

    def test_symlink_task_root_is_rejected(self) -> None:
        bensz_root = self.project_root / ".bensz-api"
        bensz_root.mkdir()
        outside = Path(self.tempdir.name) / "outside"
        outside.mkdir()
        link = bensz_root / "task-20260808-2204-linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (NotImplementedError, OSError):
            self.skipTest("directory symlinks are unavailable")
        with self.assertRaises(ValueError):
            resolve_workspace(
                project_root=self.project_root,
                task_root_arg=str(link),
                task_description="ignored",
                directories=DIRECTORIES,
                create=True,
            )

    def test_legacy_root_is_explicit_and_read_only(self) -> None:
        legacy = self.project_root / ".bensz-api" / "skills" / "auto-test-project"
        (legacy / "output" / "plans").mkdir(parents=True)
        (legacy / "output" / "tests").mkdir(parents=True)
        before = sorted(path.relative_to(self.project_root) for path in self.project_root.rglob("*"))
        layout = resolve_legacy_workspace(
            project_root=self.project_root,
            legacy_root_arg=str(legacy),
            directories=DIRECTORIES,
        )
        after = sorted(path.relative_to(self.project_root) for path in self.project_root.rglob("*"))
        self.assertTrue(layout.legacy)
        self.assertEqual(before, after)

        with self.assertRaises(ValueError):
            infer_active_workspace_from_session(
                project_root=self.project_root,
                session_dir=layout.tests_dir / "v202608082204",
                directories=DIRECTORIES,
            )

    def test_active_session_inference_uses_task_local_suffixes(self) -> None:
        layout = resolve_workspace(
            project_root=self.project_root,
            task_root_arg=".bensz-api/task-20260808-2204-infer",
            task_description="ignored",
            directories=DIRECTORIES,
            create=True,
        )
        session = layout.tests_dir / "v202608082204"
        session.mkdir()
        inferred = infer_active_workspace_from_session(
            project_root=self.project_root,
            session_dir=session,
            directories=DIRECTORIES,
        )
        self.assertEqual(inferred.task_root, layout.task_root)
        self.assertEqual(inferred.plans_dir, layout.plans_dir)


if __name__ == "__main__":
    unittest.main()
