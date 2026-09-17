from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SKILL_ROOT = Path(__file__).resolve().parents[1]
CHECKER = SKILL_ROOT / "scripts" / "check_analysis_workflow.py"
RUNNER = SKILL_ROOT / "scripts" / "run_analysis_workflow.py"


class AnalysisWorkflowTests(unittest.TestCase):
    def make_project(self, root: Path) -> None:
        (root / "00.Environment.R").write_text("options(stringsAsFactors = FALSE)\n", encoding="utf-8")
        (root / "raw").mkdir()
        (root / "raw" / "input.tsv").write_text("x\n1\n", encoding="utf-8")
        (root / "01.00.00. 数据整理.R").write_text("x <- readRDS('input.rds')\n", encoding="utf-8")
        (root / "01.00.00. 数据整理_functions.R").write_text("f <- function(x) x\n", encoding="utf-8")
        (root / "02.00.00. 结果报告.Rmd").write_text("---\ntitle: test\n---\n", encoding="utf-8")
        (root / "templates").mkdir()
        (root / "templates" / "checkpoint_helpers.R").write_text("# fixture helper\n", encoding="utf-8")
        plan = {
            "workflow": "main",
            "requirements": [
                {"id": "REQ-01", "description": "prepare and report data", "units": ["01.00.00", "02.00.00"]}
            ],
            "units": [
                {
                    "id": "01.00.00",
                    "name": "数据整理",
                    "purpose": "prepare data",
                    "depends_on": [],
                    "inputs": ["raw/input.tsv"],
                    "code": ["01.00.00. 数据整理.R", "01.00.00. 数据整理_functions.R"],
                    "products": ["products/main/01.00.00. 数据整理/main.rds"],
                    "cache": True,
                    "reports": [],
                    "completion": "checkpoint complete",
                },
                {
                    "id": "02.00.00",
                    "name": "结果报告",
                    "purpose": "report data",
                    "depends_on": ["01.00.00"],
                    "inputs": ["products/main/01.00.00. 数据整理/main.rds"],
                    "code": ["02.00.00. 结果报告.Rmd"],
                    "products": [],
                    "cache": False,
                    "reports": ["02.00.00. 结果报告.html"],
                    "completion": "report rendered",
                },
            ],
        }
        (root / "analysis-plan.yaml").write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")

        product = root / "products" / "main" / "01.00.00. 数据整理"
        product.mkdir(parents=True)
        main = product / "main.rds"
        main.write_bytes(b"checkpoint")
        (product / "summary.md").write_text("# summary\n", encoding="utf-8")
        metadata = {
            "unit_id": "01.00.00",
            "cache_identity": "abc123",
            "product_identity": "product123",
            "output_contract_version": 1,
            "output_structure": {"class": ["data.frame"], "dimensions": [1, 1]},
            "outputs": [
                {"path": "main.rds", "md5": hashlib.md5(main.read_bytes()).hexdigest()},
                {
                    "path": "summary.md",
                    "md5": hashlib.md5((product / "summary.md").read_bytes()).hexdigest(),
                },
            ],
        }
        (product / "metadata.yaml").write_text(
            yaml.safe_dump(metadata, allow_unicode=True), encoding="utf-8"
        )
        (product / "SUCCESS").write_text("abc123\n", encoding="utf-8")

    def run_checker(self, root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKER), str(root), "--plan", "analysis-plan.yaml", "--json", *extra],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_valid_numbered_workflow_passes_strict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            result = self.run_checker(root, "--strict")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["findings"], [])
            self.assertEqual(len(report["numbered_units"]), 2)

    def test_forward_dependency_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            plan_path = root / "analysis-plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            plan["units"][0]["depends_on"] = ["02.00.00"]
            plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
            result = self.run_checker(root, "--strict")
            self.assertEqual(result.returncode, 1)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("forward-dependency", codes)

    def test_product_inputs_require_earlier_explicit_dependency(self) -> None:
        cases = (
            (
                "missing-dependency",
                1,
                [],
                ["products/main/01.00.00. 数据整理/main.rds"],
                "product-input-dependency",
            ),
            (
                "future-product",
                0,
                [],
                ["products/main/02.00.00. 结果报告/main.rds"],
                "product-input-order",
            ),
        )
        for label, index, depends_on, inputs, expected in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.make_project(root)
                plan_path = root / "analysis-plan.yaml"
                plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
                plan["units"][index]["depends_on"] = depends_on
                plan["units"][index]["inputs"] = inputs
                plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
                result = self.run_checker(root, "--strict")
                self.assertEqual(result.returncode, 1)
                codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
                self.assertIn(expected, codes)

    def test_code_must_match_unit_stem(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            plan_path = root / "analysis-plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            plan["units"][0]["code"] = ["02.00.00. 结果报告.Rmd"]
            plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
            result = self.run_checker(root, "--strict")
            self.assertEqual(result.returncode, 1)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("code-unit-mismatch", codes)

    def test_cached_unit_requires_boolean_flag_and_root_main_script(self) -> None:
        cases = (
            ("string-cache", "true", ["01.00.00. 数据整理.R"], "invalid-cache"),
            (
                "rmd-only",
                True,
                ["01.00.00. 数据整理_functions.R"],
                "cached-unit-main-script",
            ),
        )
        for label, cache_value, code, expected in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.make_project(root)
                plan_path = root / "analysis-plan.yaml"
                plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
                plan["units"][0]["cache"] = cache_value
                plan["units"][0]["code"] = code
                plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
                result = self.run_checker(root, "--strict")
                self.assertEqual(result.returncode, 1)
                codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
                self.assertIn(expected, codes)

    def test_product_path_cannot_escape_unit_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            plan_path = root / "analysis-plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            plan["units"][0]["products"] = [
                "products/main/01.00.00. 数据整理/main.rds",
                "products/main/01.00.00. 数据整理/../../../raw/evil.rds",
            ]
            plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
            result = self.run_checker(root, "--strict")
            self.assertEqual(result.returncode, 1)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("parent-path-segment", codes)
            self.assertIn("cache-product-mismatch", codes)
            self.assertIn("product-boundary", codes)

    def test_workflow_cannot_be_parent_segment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            plan_path = root / "analysis-plan.yaml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            plan["workflow"] = ".."
            plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
            result = self.run_checker(root, "--strict")
            self.assertEqual(result.returncode, 1)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("invalid-workflow", codes)

    def test_unit_name_must_be_portable_to_windows(self) -> None:
        for bad_name in ("CON", "trailing.", "bad:name"):
            with self.subTest(name=bad_name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.make_project(root)
                plan_path = root / "analysis-plan.yaml"
                plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
                plan["units"][0]["name"] = bad_name
                plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
                result = self.run_checker(root, "--strict")
                self.assertEqual(result.returncode, 1)
                codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
                self.assertIn("unsafe-unit-name", codes)

    def test_report_mode_does_not_block_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            (root / "03.00.00. 未登记.R").write_text("x <- 1\n", encoding="utf-8")
            result = self.run_checker(root)
            self.assertEqual(result.returncode, 0)

    def test_damaged_checkpoint_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            (root / "products" / "main" / "01.00.00. 数据整理" / "main.rds").write_bytes(b"damaged")
            result = self.run_checker(root, "--strict")
            self.assertEqual(result.returncode, 1)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("damaged-checkpoint-output", codes)

    def test_runner_preflight_allows_recoverable_damaged_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            (root / "products" / "main" / "01.00.00. 数据整理" / "main.rds").write_bytes(b"damaged")
            result = subprocess.run(
                [sys.executable, str(RUNNER), str(root), "--dry-run"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("damaged-checkpoint-output", result.stdout)

    def test_empty_outputs_and_bad_success_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            product = root / "products" / "main" / "01.00.00. 数据整理"
            metadata_path = product / "metadata.yaml"
            metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
            metadata["outputs"] = []
            metadata_path.write_text(yaml.safe_dump(metadata, allow_unicode=True), encoding="utf-8")
            (product / "SUCCESS").write_text("wrong\n", encoding="utf-8")
            result = self.run_checker(root, "--strict")
            self.assertEqual(result.returncode, 1)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("empty-checkpoint-outputs", codes)
            self.assertIn("success-identity-mismatch", codes)

    def test_checkpoint_metadata_symlink_is_rejected_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            product = root / "products" / "main" / "01.00.00. 数据整理"
            metadata_path = product / "metadata.yaml"
            backup = root / "outside-metadata.yaml"
            metadata_path.replace(backup)
            try:
                os.symlink(backup, metadata_path)
            except OSError as exc:
                self.skipTest(f"symlink unavailable: {exc}")
            result = self.run_checker(root, "--strict")
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stderr)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("checkpoint-symlink", codes)
            self.assertEqual(json.loads(result.stdout)["project_root"], ".")

    def test_required_project_entries_reject_missing_or_symlinked_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            (root / "00.Environment.R").unlink()
            result = self.run_checker(root, "--strict")
            self.assertEqual(result.returncode, 1)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("missing-environment", codes)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            helper = root / "templates" / "checkpoint_helpers.R"
            outside = root / "outside-helper.R"
            helper.replace(outside)
            try:
                os.symlink(outside, helper)
            except OSError as exc:
                self.skipTest(f"symlink unavailable: {exc}")
            result = self.run_checker(root, "--strict")
            self.assertEqual(result.returncode, 1)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("unsafe-checkpoint-helper", codes)

    def test_legacy_tmp_project_is_non_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tmp").mkdir()
            (root / "legacy.R").write_text('out <- file.path("tmp", "legacy")\n', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(CHECKER), str(root), "--strict", "--json"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("legacy-unnumbered-file", codes)

    def test_unrelated_tmp_does_not_hide_unnumbered_new_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tmp").mkdir()
            (root / "analysis.R").write_text("x <- 1\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(CHECKER), str(root), "--strict", "--json"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 1)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("unnumbered-root-file", codes)

    def test_simple_numbered_rmd_needs_no_plan_or_products(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "00.Environment.R").write_text("options(stringsAsFactors = FALSE)\n", encoding="utf-8")
            (root / "01.00.00. 数据概览.Rmd").write_text("---\ntitle: test\n---\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(CHECKER), str(root), "--strict", "--json"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["findings"], [])

    def test_write_to_raw_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            (root / "01.00.00. 数据整理.R").write_text(
                'saveRDS(x, file.path("raw", "changed.rds"))\n', encoding="utf-8"
            )
            result = self.run_checker(root, "--strict")
            self.assertEqual(result.returncode, 1)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("write-to-raw", codes)

    def test_templates_keep_compute_and_report_parameters_separate(self) -> None:
        config = (SKILL_ROOT / "config.yaml").read_text(encoding="utf-8")
        rmd = (SKILL_ROOT / "templates" / "Rmd_template.Rmd").read_text(encoding="utf-8")
        self.assertNotIn("analysis_mode", config)
        self.assertNotIn("analysis_mode", rmd)
        self.assertNotIn("dv_mut_mode", config)
        self.assertIn('file.path("products", "main", upstream_stem)', rmd)
        self.assertIn('plot_language: "en"', config)
        self.assertIn('plot_language: "en"', rmd)
        simple_rmd = (SKILL_ROOT / "templates" / "Rmd_simple_template.Rmd").read_text(encoding="utf-8")
        self.assertNotIn('file.path("products"', simple_rmd)
        self.assertIn('file.path("raw", "input.tsv")', simple_rmd)

    def test_runner_dry_run_uses_number_order_and_skips_function_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            result = subprocess.run(
                [sys.executable, str(RUNNER), str(root), "--dry-run"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            plan_lines = [line for line in result.stdout.splitlines() if line.startswith("[PLAN]")]
            self.assertEqual(plan_lines, ["[PLAN] 01.00.00: 01.00.00. 数据整理.R"])

    def test_runner_does_not_inherit_stale_control_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            fake_rscript = root / "fake-rscript"
            fake_rscript.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os\n"
                "from pathlib import Path\n"
                "Path('runner-env.json').write_text(json.dumps({\n"
                "  'force': os.environ.get('BENSZ_FORCE_STEP'),\n"
                "  'resume': os.environ.get('BENSZ_RESUME_FROM'),\n"
                "}), encoding='utf-8')\n",
                encoding="utf-8",
            )
            fake_rscript.chmod(0o755)
            stale_env = os.environ.copy()
            stale_env["BENSZ_FORCE_STEP"] = "99.99.99"
            stale_env["BENSZ_RESUME_FROM"] = "88.88.88"

            result = subprocess.run(
                [sys.executable, str(RUNNER), str(root), "--rscript", str(fake_rscript)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=stale_env,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            observed = json.loads((root / "runner-env.json").read_text(encoding="utf-8"))
            self.assertEqual(observed, {"force": None, "resume": None})

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    str(root),
                    "--rscript",
                    str(fake_rscript),
                    "--force-step",
                    "01.00.00",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=stale_env,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            observed = json.loads((root / "runner-env.json").read_text(encoding="utf-8"))
            self.assertEqual(observed, {"force": "01.00.00", "resume": None})


if __name__ == "__main__":
    unittest.main()
