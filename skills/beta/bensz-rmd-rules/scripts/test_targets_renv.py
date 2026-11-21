import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_targets_renv.py"
PIPELINE = ROOT / "scripts" / "check_pipeline_contract.py"


class TargetsRenvChecks(unittest.TestCase):
    def run_check(self, root, *args):
        return self.run_cli(SCRIPT, root, *args)

    @staticmethod
    def run_cli(script, root, *args):
        out = subprocess.run(
            [sys.executable, str(script), str(root), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        return out.returncode, json.loads(out.stdout)

    @staticmethod
    def add_renv(root: Path) -> None:
        (root / "renv.lock").write_text('{"R":{"Version":"4.5.0"},"Packages":{}}\n', encoding="utf-8")
        (root / "renv").mkdir()
        (root / "renv" / "activate.R").write_text("renv::load()\n", encoding="utf-8")

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
            (root / "R").mkdir()
            (root / "_targets.R").write_text('targets::tar_source("R")\n# targets\n', encoding="utf-8")
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
                    (root / "R").mkdir()
                    (root / "_targets.R").write_text('targets::tar_source("R")\n# targets\n', encoding="utf-8")
                entry = root / "scripts" / "tests" / "smoke_test.R"
                entry.parent.mkdir(parents=True)
                entry.write_text(
                    (ROOT / "templates" / "tests" / f"{mode}_smoke_test.R").read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
                code, result = self.run_check(root, "--project-state", "new", "--workflow-mode", mode)
                self.assertEqual(code, 1, result)
                self.assertIn("missing-test-harness", {item["code"] for item in result["issues"]})
                shutil.copy2(ROOT / "templates/tests/test_harness.R", entry.parent)
                code, result = self.run_check(
                    root, "--project-state", "new", "--workflow-mode", mode
                )
                self.assertEqual(code, 0, result)

    def test_preflight_rejects_wrong_types_and_empty_environment_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.add_smoke(root)
            (root / "renv.lock").mkdir()
            (root / "renv").mkdir()
            (root / "renv/activate.R").write_text("# TODO\n", encoding="utf-8")
            (root / "R").write_text("not a directory", encoding="utf-8")
            (root / "_targets.R").write_text("# tar_source('R')\n", encoding="utf-8")
            code, result = self.run_check(root, "--project-state", "new", "--workflow-mode", "pipeline")
            self.assertEqual(code, 1)
            codes = {item["code"] for item in result["issues"]}
            self.assertTrue({"invalid-project-path-type", "empty-renv-activation", "targets-not-r-first"} <= codes)
            (root / "renv.lock").rmdir()
            (root / "renv.lock").write_text("{}", encoding="utf-8")
            _, result = self.run_check(root, "--project-state", "new", "--workflow-mode", "pipeline")
            self.assertIn("invalid-renv-lockfile", {item["code"] for item in result["issues"]})

    def test_complex_store_shape_and_simple_ignores_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.add_renv(root)
            self.add_smoke(root)
            self.assertEqual(self.run_check(root, "--workflow-mode", "simple", "--test-store", "unused")[0], 0)
            for invalid in ("tmp/tests", "tmp/tests/_targets", "tmp/tests/run/other", "tmp//tests/run/_targets"):
                with self.subTest(invalid=invalid):
                    _, result = self.run_check(root, "--workflow-mode", "complex", "--test-store", invalid)
                    self.assertIn("test-store-not-isolated", {item["code"] for item in result["issues"]})
            _, result = self.run_check(root, "--workflow-mode", "complex", "--test-store", r"tmp\tests\smoke\_targets")
            self.assertNotIn("test-store-not-isolated", {item["code"] for item in result["issues"]})
            (root / "tmp").write_text("not a directory", encoding="utf-8")
            _, result = self.run_check(root, "--workflow-mode", "complex")
            self.assertIn("unsafe-test-store", {item["code"] for item in result["issues"]})

    def test_conflicting_modes_do_not_pass_either_checker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, result = self.run_check(root, "--project-state", "existing", "--workflow-mode", "complex")
            self.assertEqual(code, 1)
            self.assertIn("_targets.R", result["missing"])
            self.assertEqual(self.run_cli(PIPELINE, root, "--workflow-mode", "complex")[0], 1)
            (root / "_targets.R").write_text("", encoding="utf-8")
            (root / "R").mkdir()
            self.assertEqual(self.run_check(root, "--workflow-mode", "simple")[0], 1)
            self.assertEqual(self.run_cli(PIPELINE, root, "--workflow-mode", "simple")[0], 1)
            _, result = self.run_cli(PIPELINE, root, "--workflow-mode", "pipeline")
            self.assertIn("r-source-not-declared", {f["code"] for f in result["findings"]})

    def test_pipeline_scans_deliverable_code_and_skips_generated_trees(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "templates" / "project name"
            (root / "R").mkdir(parents=True)
            (root / "_targets.R").write_text('targets::tar_source("R")\n', encoding="utf-8")
            for dirname in ("tmp", "renv", "templates", "_targets", ".bensz-api"):
                (root / dirname).mkdir()
                (root / dirname / "ignored.Rmd").write_text("not a report", encoding="utf-8")
            report = root / "results.rmd"
            fence = chr(96) * 3
            report.write_text(
                "Use tar_read(x).\n\n"
                f"{fence}{{r}}\n# tar_load(x)\nmessage('try tar_read(x)')\ntarchetypes::tar_render('other.Rmd')\n"
                f"readr::read_tsv(file.path('raw', 'input.tsv'))\n{fence}\n",
                encoding="utf-8",
            )
            code, result = self.run_cli(PIPELINE, root)
            self.assertEqual(code, 1, result)
            self.assertEqual(result["reports_checked"], ["results.rmd"])
            self.assertEqual({f["code"] for f in result["findings"]}, {"rmd-bypasses-targets", "rmd-reads-raw-directly"})
            report.write_text("# Results\n\nCount: \x60r nrow(targets::tar_read(data))\x60\n", encoding="utf-8")
            code, result = self.run_cli(PIPELINE, root)
            self.assertEqual(code, 0, result)

    def test_existing_lowercase_rmd_and_bom_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "analysis.rmd").write_text("# Existing analysis\n", encoding="utf-8")
            self.assertEqual(self.run_check(root)[1]["project_state"], "existing")
            self.add_renv(root)
            lock = root / "renv.lock"
            lock.write_text(lock.read_text(encoding="utf-8"), encoding="utf-8-sig")
            self.add_smoke(root)
            self.assertEqual(self.run_check(root, "--project-state", "new")[0], 0)

    def test_existing_targets_project_auto_resolves_complex(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "analysis.R").write_text("# existing\n", encoding="utf-8")
            self.add_renv(root)
            (root / "R").mkdir()
            (root / "_targets.R").write_text('targets::tar_source("R")\n# targets\n', encoding="utf-8")
            self.add_smoke(
                root,
                'run_id <- Sys.getenv("BENSZ_TEST_RUN_ID", unset = "smoke")\n'
                'test_store <- file.path("tmp", "tests", run_id, "_targets")\n'
                "targets::tar_make(store = test_store)\n",
            )
            code, result = self.run_check(root, "--project-state", "existing", "--workflow-mode", "auto")
            self.assertEqual(code, 0)
            self.assertEqual(result["project_state"], "existing")
            self.assertEqual(result["workflow_mode"], "complex")
            self.assertEqual(result["missing"], [])
            self.assertEqual(result["issues"], [])
            self.assertTrue(result["observed_mechanisms"]["targets"])

    def test_existing_without_targets_reports_mechanisms_as_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "analysis.R").write_text("# existing\n", encoding="utf-8")
            before = sorted(path.relative_to(root) for path in root.rglob("*"))
            code, result = self.run_check(root, "--project-state", "auto")
            after = sorted(path.relative_to(root) for path in root.rglob("*"))
            self.assertEqual(code, 0)
            self.assertEqual(result["project_state"], "existing")
            self.assertEqual(result["workflow_mode"], "simple")
            self.assertEqual(result["missing"], [])
            self.assertEqual(result["issues"], [])
            self.assertGreaterEqual(len(result["warnings"]), 2)
            self.assertFalse(result["observed_mechanisms"]["renv"])
            self.assertFalse(result["observed_mechanisms"]["targets"])
            self.assertEqual(before, after)

    def test_legacy_mode_alias_remains_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "analysis.R").write_text("# existing\n", encoding="utf-8")
            code, result = self.run_check(root, "--mode", "existing")
            self.assertEqual(code, 0)
            self.assertEqual(result["mode"], "existing")
            self.assertEqual(result["workflow_mode"], "simple")

    def test_disagreeing_state_arguments_fail_stably(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, result = self.run_check(
                Path(tmp), "--mode", "new", "--project-state", "existing"
            )
            self.assertEqual(code, 2)
            self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()
