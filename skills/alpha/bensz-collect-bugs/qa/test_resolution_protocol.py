from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "resolve_bug.py"


class ResolutionProtocolTests(unittest.TestCase):
    def make_bug_dir(self, root: Path) -> Path:
        bug_dir = root / "demo-skill" / "octocat" / "abc123"
        bug_dir.mkdir(parents=True)
        (bug_dir / "bug-context.json").write_text("{}\n", encoding="utf-8")
        (bug_dir / "BUG_REPORT.md").write_text("# Bug\n", encoding="utf-8")
        return bug_dir

    def command(self, bug_dir: Path, *extra: str) -> list[str]:
        return [
            sys.executable,
            str(SCRIPT),
            "--bug-dir",
            str(bug_dir),
            "--status",
            "fixed",
            "--canonical-root-cause",
            "BRCC-2026-001",
            "--fixed-version-or-commit",
            "v1.2.3",
            "--verification",
            "pytest tests/test_regression.py: 4 passed",
            "--print-json",
            *extra,
        ]

    def test_dry_run_create_and_idempotent_repeat(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bug_dir = self.make_bug_dir(Path(tmpdir))
            dry_run = subprocess.run(self.command(bug_dir, "--dry-run"), check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(dry_run.stdout)["action"], "create")
            self.assertFalse((bug_dir / "RESOLUTION.md").exists())

            created = subprocess.run(self.command(bug_dir), check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(created.stdout)["action"], "create")
            original = (bug_dir / "RESOLUTION.md").read_text(encoding="utf-8")

            repeated = subprocess.run(self.command(bug_dir), check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(repeated.stdout)["action"], "unchanged")
            self.assertEqual((bug_dir / "RESOLUTION.md").read_text(encoding="utf-8"), original)

    def test_conflicting_resolution_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bug_dir = self.make_bug_dir(Path(tmpdir))
            subprocess.run(self.command(bug_dir), check=True, capture_output=True, text=True)
            result = subprocess.run(
                self.command(bug_dir, "--verification", "different evidence"),
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("拒绝覆盖", result.stderr)

    def test_fixed_requires_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bug_dir = self.make_bug_dir(Path(tmpdir))
            command = self.command(bug_dir)
            verification_index = command.index("--verification")
            del command[verification_index : verification_index + 2]
            result = subprocess.run(command, check=False, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--verification", result.stderr)

    def test_duplicate_requires_duplicate_of(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bug_dir = self.make_bug_dir(Path(tmpdir))
            command = self.command(bug_dir)
            command[command.index("fixed")] = "duplicate"
            result = subprocess.run(command, check=False, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--duplicate-of", result.stderr)


if __name__ == "__main__":
    unittest.main()
