import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_targets_renv.py"


class TargetsRenvChecks(unittest.TestCase):
    def run_check(self, root, *args):
        out = subprocess.run(
            [sys.executable, str(SCRIPT), str(root), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        return out.returncode, json.loads(out.stdout)

    @staticmethod
    def add_renv(root: Path) -> None:
        (root / "renv.lock").write_text("{}\n", encoding="utf-8")
        (root / "renv").mkdir()
        (root / "renv" / "activate.R").write_text("# renv\n", encoding="utf-8")

    @staticmethod
    def add_smoke(root: Path, content: str = "run_id <- Sys.getenv('BENSZ_TEST_RUN_ID')\nsource('analysis.R')\n") -> None:
        entry = root / "scripts" / "tests" / "smoke_test.R"
        entry.parent.mkdir(parents=True)
        entry.write_text(content, encoding="utf-8")

    def test_new_simple_requires_renv_and_test_entry_but_not_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, result = self.run_check(
                Path(tmp), "--project-state", "new", "--workflow-mode", "simple"
            )
            self.assertEqual(code, 1)
            self.assertEqual(
                result["missing"],
                ["renv.lock", "renv/activate.R", "scripts/tests/smoke_test.R"],
            )
            self.assertNotIn("_targets.R", result["missing"])

    def test_new_simple_passes_without_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.add_renv(root)
            self.add_smoke(root)
            before = sorted(path.relative_to(root) for path in root.rglob("*"))
            code, result = self.run_check(
                root, "--project-state", "new", "--workflow-mode", "simple"
            )
            after = sorted(path.relative_to(root) for path in root.rglob("*"))
            self.assertEqual(code, 0)
            self.assertEqual(result["workflow_mode"], "simple")
            self.assertEqual(before, after)
            self.assertFalse((root / "_targets.R").exists())

    def test_new_complex_requires_targets_and_isolated_test_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.add_renv(root)
            self.add_smoke(root, "targets::tar_make(store = '_targets')\n")
            code, result = self.run_check(
                root, "--project-state", "new", "--workflow-mode", "complex"
            )
            self.assertEqual(code, 1)
            self.assertIn("_targets.R", result["missing"])
            codes = {item["code"] for item in result["issues"]}
            self.assertIn("complex-test-store-unbound", codes)
            self.assertIn("complex-test-uses-formal-store", codes)

    def test_new_complex_passes_with_isolated_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.add_renv(root)
            (root / "_targets.R").write_text("# targets\n", encoding="utf-8")
            self.add_smoke(
                root,
                'run_id <- Sys.getenv("BENSZ_TEST_RUN_ID", unset = "smoke")\n'
                'test_store <- file.path("tmp", "tests", run_id, "_targets")\n'
                "targets::tar_make(store = test_store)\n",
            )
            code, result = self.run_check(
                root, "--project-state", "new", "--workflow-mode", "complex"
            )
            self.assertEqual(code, 0)
            self.assertEqual(result["test_store"], "tmp/tests/<run-id>/_targets")

    def test_packaged_smoke_templates_delegate_unique_run_root_to_harness(self):
        for mode in ("simple", "complex"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.add_renv(root)
                if mode == "complex":
                    (root / "_targets.R").write_text("# targets\n", encoding="utf-8")
                entry = root / "scripts" / "tests" / "smoke_test.R"
                entry.parent.mkdir(parents=True)
                entry.write_text(
                    (ROOT / "templates" / "tests" / f"{mode}_smoke_test.R").read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
                code, result = self.run_check(
                    root, "--project-state", "new", "--workflow-mode", mode
                )
                self.assertEqual(code, 0, result)

    def test_existing_project_is_read_only_and_missing_mechanisms_are_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "analysis.R").write_text("# existing\n", encoding="utf-8")
            before = sorted(path.relative_to(root) for path in root.rglob("*"))
            code, result = self.run_check(root, "--project-state", "auto")
            after = sorted(path.relative_to(root) for path in root.rglob("*"))
            self.assertEqual(code, 0)
            self.assertEqual(result["project_state"], "existing")
            self.assertEqual(result["workflow_mode"], "preserved-existing")
            self.assertEqual(result["missing"], [])
            self.assertEqual(before, after)
            self.assertGreaterEqual(len(result["warnings"]), 2)
            self.assertFalse(result["observed_mechanisms"]["renv"])
            self.assertFalse(result["observed_mechanisms"]["targets"])

    def test_legacy_mode_alias_remains_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "analysis.R").write_text("# existing\n", encoding="utf-8")
            code, result = self.run_check(root, "--mode", "existing")
            self.assertEqual(code, 0)
            self.assertEqual(result["mode"], "existing")

    def test_existing_rejects_new_project_workflow_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "analysis.R").write_text("# existing\n", encoding="utf-8")
            code, result = self.run_check(
                root, "--project-state", "existing", "--workflow-mode", "simple"
            )
            self.assertEqual(code, 1)
            self.assertEqual(result["workflow_mode"], "preserved-existing")
            self.assertIn(
                "existing-workflow-mode-not-preserved",
                {item["code"] for item in result["issues"]},
            )

    def test_disagreeing_state_arguments_fail_stably(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, result = self.run_check(
                Path(tmp), "--mode", "new", "--project-state", "existing"
            )
            self.assertEqual(code, 2)
            self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()
