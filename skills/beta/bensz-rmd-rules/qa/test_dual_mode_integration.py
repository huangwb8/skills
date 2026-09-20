"""Real lightweight integration checks for bensz-rmd-rules simple/complex modes."""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[2]
CHECKER = SKILL_ROOT / "scripts" / "check_targets_renv.py"
THEME_BOOTSTRAP = SKILL_ROOT / "scripts" / "bootstrap_liquid_glass.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def r_has(packages: list[str], *, require_pandoc: bool = False) -> bool:
    rscript = shutil.which("Rscript")
    if not rscript:
        return False
    checks = " && ".join(f'requireNamespace("{name}", quietly=TRUE)' for name in packages)
    if require_pandoc:
        checks = f"({checks}) && rmarkdown::pandoc_available()"
    result = subprocess.run(
        [rscript, "-e", f"quit(status=if ({checks}) 0 else 1)"],
        text=True,
        capture_output=True,
        check=False,
        env=os.environ.copy(),
    )
    return result.returncode == 0


class DualModeRealExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rscript = shutil.which("Rscript")
        parent = Path(os.environ.get("BENSZ_TEST_TMP", REPO_ROOT / "tmp"))
        parent.mkdir(parents=True, exist_ok=True)
        cls.temp_parent = parent

    def add_renv_contract(self, root: Path, packages: list[str]) -> None:
        result = subprocess.run(
            [
                self.rscript,
                "-e",
                "a <- commandArgs(TRUE); p <- a[[1]]; pkgs <- unique(c('renv', a[-1])); sources <- .libPaths(); renv::init(project=p, bare=TRUE, restart=FALSE); renv::hydrate(project=p, packages=pkgs, sources=sources, prompt=FALSE, report=FALSE); renv::snapshot(project=p, packages=pkgs, prompt=FALSE)",
                str(root),
                *packages,
            ],
            text=True,
            capture_output=True,
            check=False,
            env=os.environ.copy(),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((root / "renv" / "activate.R").is_file())
        self.assertTrue((root / "renv.lock").is_file())

    def assert_renv_synchronized(self, root: Path) -> None:
        result = subprocess.run(
            [
                self.rscript,
                "-e",
                "a <- commandArgs(TRUE); status <- renv::status(project=a[[1]], sources=FALSE); quit(status=if (isTRUE(status$synchronized)) 0 else 1)",
                str(root),
            ],
            text=True,
            capture_output=True,
            check=False,
            env=os.environ.copy(),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def run_checker(self, root: Path, workflow_mode: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(CHECKER),
                str(root),
                "--project-state",
                "new",
                "--workflow-mode",
                workflow_mode,
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_bootstrap_places_non_style_helper_under_scripts_lib(self):
        with tempfile.TemporaryDirectory(prefix="rmd-bootstrap-", dir=self.temp_parent) as tmp:
            root = Path(tmp)
            result = subprocess.run(
                [sys.executable, str(THEME_BOOTSTRAP), "--project-root", str(root), "--with-extras"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((root / "scripts" / "lib" / "checkpoint_helpers.R").is_file())
            self.assertFalse((root / "templates" / "checkpoint_helpers.R").exists())
            self.assertTrue((root / "templates" / "liquid_glass_theme.css").is_file())

    @unittest.skipUnless(r_has(["renv", "rmarkdown"], require_pandoc=True), "R renv + rmarkdown + pandoc required")
    def test_simple_synthetic_fixture_renders_real_rmd_without_targets(self):
        with tempfile.TemporaryDirectory(prefix="rmd-simple-", dir=self.temp_parent) as tmp:
            root = Path(tmp)
            self.add_renv_contract(root, ["rmarkdown"])
            (root / "raw").mkdir()
            raw_path = root / "raw" / "protected.csv"
            raw_path.write_text("id,group,value\nR1,A,10\n", encoding="utf-8")
            raw_before = digest(raw_path)
            report = root / "01.00.00. 分析报告.Rmd"
            report.write_text(
                textwrap.dedent(
                    """\
                    ---
                    title: "Simple integration"
                    output: html_document
                    ---

                    ```{r}
                    input <- Sys.getenv("BENSZ_ANALYSIS_INPUT")
                    data <- utils::read.csv(input, check.names = FALSE)
                    stopifnot(nrow(data) == 6L, !anyDuplicated(data$id))
                    stopifnot(setequal(unique(data$group), c("A", "B")))
                    summary(data$value)
                    ```
                    """
                ),
                encoding="utf-8",
            )
            smoke = root / "scripts" / "tests" / "smoke_test.R"
            smoke.parent.mkdir(parents=True)
            shutil.copy2(
                SKILL_ROOT / "templates" / "tests" / "test_harness.R",
                smoke.parent / "test_harness.R",
            )
            smoke.write_text(
                textwrap.dedent(
                    """\
                    source(file.path("renv", "activate.R"))
                    source(file.path("scripts", "tests", "test_harness.R"))
                    Sys.setenv(BENSZ_TEST_RUN_ID = "simple-integration")
                    run_id <- Sys.getenv("BENSZ_TEST_RUN_ID")
                    context <- bensz_test_begin("new", "simple", "synthetic_fixture", "01.00.00. 分析报告.Rmd")
                    set.seed(20260920L)
                    fixture <- data.frame(
                      id = sprintf("S%02d", 1:6),
                      group = rep(c("A", "B"), each = 3L),
                      value = c(1, NA, 3, 4, 9, 6)
                    )
                    fixture_path <- file.path(context$input_dir, "synthetic_fixture.csv")
                    utils::write.csv(fixture, fixture_path, row.names = FALSE, na = "")
                    Sys.setenv(BENSZ_ANALYSIS_INPUT = normalizePath(fixture_path, mustWork = TRUE))
                    dir.create(context$reports_dir, recursive = TRUE, showWarnings = FALSE)
                    output <- rmarkdown::render(
                      "01.00.00. 分析报告.Rmd",
                      output_dir = context$reports_dir,
                      quiet = TRUE,
                      envir = new.env(parent = globalenv())
                    )
                    stopifnot(file.exists(output), file.info(output)$size > 0)
                    unlink(fixture_path)
                    bensz_test_finish(context, assertions = c("synthetic schema passed", "Rmd rendered"))
                    """
                ),
                encoding="utf-8",
            )

            self.assert_renv_synchronized(root)
            checked = self.run_checker(root, "simple")
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            run = subprocess.run(
                [self.rscript, str(smoke)], cwd=root, text=True, capture_output=True, check=False
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertEqual(digest(raw_path), raw_before)
            run_root = root / "tmp" / "tests" / "simple-integration"
            rendered = list((run_root / "reports").glob("*.html"))
            self.assertEqual(len(rendered), 1)
            self.assertGreater(rendered[0].stat().st_size, 0)
            self.assertTrue((run_root / "run-record.md").is_file())
            record = (run_root / "run-record.md").read_text(encoding="utf-8")
            self.assertIn("full_data_execution: NOT_RUN", record)
            self.assertIn("subject_check: PASS", record)
            self.assertIn("test_style: synthetic_fixture", record)
            self.assertFalse((run_root / "input" / "synthetic_fixture.csv").exists())
            self.assertFalse((root / "_targets.R").exists())
            self.assertFalse((root / "products").exists())

    @unittest.skipUnless(r_has(["renv", "targets"]), "R renv + targets packages required")
    def test_complex_project_subset_runs_real_graph_in_isolated_store(self):
        with tempfile.TemporaryDirectory(prefix="rmd-complex-", dir=self.temp_parent) as tmp:
            root = Path(tmp)
            self.add_renv_contract(root, ["targets"])
            (root / "raw").mkdir()
            raw_path = root / "raw" / "input.csv"
            raw_path.write_text(
                "id,group,value\nA1,A,1\nA2,A,\nA3,A,7\nB1,B,2\nB2,B,9\nB3,B,3\n",
                encoding="utf-8",
            )
            raw_before = digest(raw_path)
            (root / "_targets.R").write_text(
                textwrap.dedent(
                    """\
                    source(file.path("renv", "activate.R"))
                    library(targets)
                    input_path <- Sys.getenv("BENSZ_ANALYSIS_INPUT", unset = file.path("raw", "input.csv"))
                    output_root <- Sys.getenv("BENSZ_PRODUCTS_DIR", unset = "products")
                    list(
                      tar_target(data, utils::read.csv(input_path, check.names = FALSE)),
                      tar_target(
                        summary_file,
                        {
                          dir.create(output_root, recursive = TRUE, showWarnings = FALSE)
                          path <- file.path(output_root, "summary.txt")
                          writeLines(paste("rows", nrow(data)), path)
                          path
                        },
                        format = "file"
                      )
                    )
                    """
                ),
                encoding="utf-8",
            )
            smoke = root / "scripts" / "tests" / "smoke_test.R"
            smoke.parent.mkdir(parents=True)
            shutil.copy2(
                SKILL_ROOT / "templates" / "tests" / "test_harness.R",
                smoke.parent / "test_harness.R",
            )
            smoke.write_text(
                textwrap.dedent(
                    """\
                    source(file.path("renv", "activate.R"))
                    source(file.path("scripts", "tests", "test_harness.R"))
                    Sys.setenv(BENSZ_TEST_RUN_ID = "complex-integration")
                    run_id <- Sys.getenv("BENSZ_TEST_RUN_ID")
                    context <- bensz_test_begin("new", "complex", "project_subset", "_targets.R")
                    source_path <- file.path("raw", "input.csv")
                    raw_before <- unname(tools::md5sum(source_path))
                    full <- utils::read.csv(source_path, check.names = FALSE)
                    ordered <- full[order(full$group, full$id), , drop = FALSE]
                    pick <- !duplicated(ordered$group) | is.na(ordered$value) | ordered$value == max(ordered$value, na.rm = TRUE)
                    subset_data <- ordered[pick, , drop = FALSE]
                    stopifnot(setequal(unique(subset_data$group), c("A", "B")), anyNA(subset_data$value))
                    test_input <- file.path(context$input_dir, "project_subset.csv")
                    utils::write.csv(subset_data, test_input, row.names = FALSE, na = "")
                    Sys.setenv(
                      BENSZ_ANALYSIS_INPUT = normalizePath(test_input, mustWork = TRUE)
                    )
                    targets::tar_make(store = context$targets_store)
                    built <- targets::tar_read(data, store = context$targets_store)
                    stopifnot(nrow(built) == nrow(subset_data))
                    stopifnot(file.exists(file.path(context$products_dir, "summary.txt")))
                    stopifnot(identical(raw_before, unname(tools::md5sum(source_path))))
                    unlink(test_input)
                    bensz_test_finish(context, assertions = c("representative subset passed", "target graph executed"))
                    """
                ),
                encoding="utf-8",
            )

            self.assert_renv_synchronized(root)
            checked = self.run_checker(root, "complex")
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            run = subprocess.run(
                [self.rscript, str(smoke)], cwd=root, text=True, capture_output=True, check=False
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertEqual(digest(raw_path), raw_before)
            run_root = root / "tmp" / "tests" / "complex-integration"
            self.assertTrue((run_root / "_targets").is_dir())
            self.assertTrue((run_root / "run-record.md").is_file())
            record = (run_root / "run-record.md").read_text(encoding="utf-8")
            self.assertIn("full_data_execution: NOT_RUN", record)
            self.assertIn("mutation_check: PASS", record)
            self.assertIn("test_style: project_subset", record)
            self.assertFalse((run_root / "input" / "project_subset.csv").exists())
            self.assertFalse((root / "_targets").exists())
            self.assertFalse((root / "products").exists())
            self.assertFalse((root / "reports").exists())


if __name__ == "__main__":
    unittest.main()
