from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
VERIFY_SCRIPT = SKILL_ROOT / "scripts" / "verify_test_session.py"


class WorkspaceCliTest(unittest.TestCase):
    def test_legacy_verification_requires_explicit_read_only_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="auto-test-project-legacy-") as tmp:
            project_root = Path(tmp) / "project"
            legacy_root = project_root / ".bensz-api" / "skills" / "auto-test-project"
            plans_dir = legacy_root / "output" / "plans"
            session_dir = legacy_root / "output" / "tests" / "v202608082204"
            plans_dir.mkdir(parents=True)
            session_dir.mkdir(parents=True)
            (plans_dir / "v202608082204.md").write_text(
                "# Legacy plan\n\n#### P0-1: verified legacy record\n", encoding="utf-8"
            )
            (session_dir / "TEST_PLAN.md").write_text("# TEST_PLAN\n", encoding="utf-8")
            (session_dir / "TEST_REPORT.md").write_text(
                "# TEST_REPORT\n\nP0-1\n\n```text\nlegacy evidence\n```\n",
                encoding="utf-8",
            )
            before = sorted(path.relative_to(project_root) for path in project_root.rglob("*"))

            explicit = subprocess.run(
                [
                    sys.executable,
                    str(VERIFY_SCRIPT),
                    "--project-root",
                    str(project_root),
                    "--legacy-root",
                    str(legacy_root),
                    "--require-plan",
                    "--min-report-length",
                    "10",
                    "--min-issue-count",
                    "1",
                    str(session_dir),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(explicit.returncode, 0, explicit.stdout + explicit.stderr)
            after = sorted(path.relative_to(project_root) for path in project_root.rglob("*"))
            self.assertEqual(before, after)

            implicit = subprocess.run(
                [
                    sys.executable,
                    str(VERIFY_SCRIPT),
                    "--project-root",
                    str(project_root),
                    str(session_dir),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(implicit.returncode, 2)
            self.assertNotIn("Traceback", implicit.stdout + implicit.stderr)


if __name__ == "__main__":
    unittest.main()
