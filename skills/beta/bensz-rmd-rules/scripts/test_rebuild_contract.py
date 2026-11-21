"""Execute shipped templates in disposable projects; never use production data."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[2]
RSCRIPT = shutil.which("Rscript")


def has_runtime() -> bool:
    if not RSCRIPT:
        return False
    result = subprocess.run(
        [RSCRIPT, "--vanilla", "-e",
         'quit(status=if(all(vapply(c("renv","targets","rmarkdown","luckyBase","yaml"), '
         'requireNamespace, logical(1), quietly=TRUE)) && rmarkdown::pandoc_available()) 0 else 1)'],
        capture_output=True, check=False,
    )
    return result.returncode == 0


@unittest.skipUnless(has_runtime(), "R + renv/targets/rmarkdown/luckyBase/yaml + Pandoc required")
class RebuildContractExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parent = Path(os.environ.get("BENSZ_TEST_TMP", REPO / "tmp"))
        parent.mkdir(parents=True, exist_ok=True)
        cls.root = Path(tempfile.mkdtemp(prefix="rmd-rebuild-", dir=parent))
        cls.installed = cls.root / "installed" / "bensz-rmd-rules"
        shutil.copytree(SKILL, cls.installed, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
        cls.seed_project = cls.root / "environment"
        cls.seed_project.mkdir()
        cls.run_r(
            # Preserve the actual installed binary when its original source is
            # unknown. This is a local, platform-specific test dependency, not
            # a replacement package or a claim of cross-platform restoration.
            "sources <- .libPaths(); pkg <- system.file(package='luckyBase'); "
            "archive <- file.path(getwd(), paste0('luckyBase_', packageVersion('luckyBase'), '.tgz')); "
            "local({ old <- getwd(); on.exit(setwd(old)); setwd(dirname(pkg)); "
            "utils::tar(archive, files=basename(pkg), compression='gzip', tar='internal') }); "
            "renv::init(bare=TRUE, restart=FALSE); "
            "pkgs <- c('renv','targets','rmarkdown','luckyBase','yaml'); "
            "renv::hydrate(packages=pkgs, sources=sources, prompt=FALSE, report=FALSE); "
            "renv::install(archive, prompt=FALSE); "
            "renv::snapshot(packages=pkgs, prompt=FALSE)", cls.seed_project,
        )

    @classmethod
    def run_r(cls, code, cwd, *, success=True, extra_env=None):
        env = os.environ.copy()
        # Each test explicitly sets its input and output configuration.
        for key in ("BENSZ_ANALYSIS_INPUT", "BENSZ_PRODUCTS_DIR", "BENSZ_REPORTS_DIR",
                    "BENSZ_TARGETS_STORE", "BENSZ_TEST_RUN_ROOT", "BENSZ_ANALYSIS_ENTRY",
                    "BENSZ_REPORT_ENTRY", "BENSZ_TEST_STYLE", "BENSZ_SOURCE_DATA"):
            env.pop(key, None)
        env.update(extra_env or {})
        result = subprocess.run(
            [RSCRIPT, "--vanilla", "-e", code], cwd=cwd, env=env,
            text=True, capture_output=True, check=False, timeout=180,
        )
        if (result.returncode == 0) != success:
            raise AssertionError(result.stdout + result.stderr)
        return result

    def project(self, name, mode):
        root = self.root / name
        shutil.copytree(self.seed_project, root)
        bootstrap = subprocess.run(
            [os.sys.executable, str(self.installed / "scripts/bootstrap_liquid_glass.py"),
             "--project-root", str(root), "--with-env", *(["--with-pipeline"] if mode == "complex" else [])],
            cwd=self.root, text=True, capture_output=True, check=False,
        )
        self.assertEqual(bootstrap.returncode, 0, bootstrap.stderr)
        tests = root / "scripts/tests"
        tests.mkdir(parents=True)
        for src, dst in (("test_harness.R", "test_harness.R"),
                         ("synthetic_fixture.R", "test_data.R"),
                         (f"{mode}_smoke_test.R", "smoke_test.R")):
            shutil.copy2(self.installed / "templates/tests" / src, tests / dst)
        (root / "raw").mkdir()
        (root / "raw/input.tsv").write_text(
            "sample_id\tgroup\tvalue\nS01\tcontrol\t1\nS02\tcontrol\t1.3\n"
            "S03\tcontrol\t\nS04\tcontrol\t1.8\nS05\ttreated\t2\n"
            "S06\ttreated\t2.4\nS07\ttreated\t8\nS08\ttreated\t2.8\n", encoding="utf-8",
        )
        return root

    def test_complex_template_rebuild_loss_change_and_relocation(self):
        root = self.project("complex project", "complex")
        functions = root / "R/analysis_functions.R"
        functions.write_text(functions.read_text(encoding="utf-8") + "\n"
            "analyze_data <- function(prepared_data) {\n"
            "  stopifnot(!exists('hidden_dependency', inherits=TRUE))\n"
            "  data.frame(mean = mean(prepared_data$value, na.rm=TRUE))\n}\n", encoding="utf-8")
        dag = root / "_targets.R"
        dag.write_text(dag.read_text(encoding="utf-8").replace(
            "list(\n  # ---- Stage", "list(\n  targets::tar_target(reference_constant, 7L),\n  # ---- Stage"
        ), encoding="utf-8")
        (root / "brief.Rmd").write_text(
            "---\ntitle: Isolated pipeline report\noutput: html_document\n---\n\n"
            "\x60\x60\x60{r}\n"
            "result <- targets::tar_read(analysis_results, store = Sys.getenv('BENSZ_TARGETS_STORE', '_targets'))\n"
            "stopifnot(abs(result$mean - 19.3/7) < 1e-12)\nresult\n"
            "\x60\x60\x60\n", encoding="utf-8",
        )
        self.run_r(
            "hidden_dependency <- 999; source('scripts/tests/smoke_test.R')", root,
            extra_env={"BENSZ_TEST_RUN_ID": "template", "BENSZ_REPORT_ENTRY": "brief.Rmd"},
        )
        record = (root / "tmp/tests/template/run-record.md").read_text(encoding="utf-8")
        self.assertIn("cold_rebuild: PASS", record)
        self.assertIn("missing_delivery: PASS", record)
        self.assertIn("relocated_project: NOT_RUN", record)
        self.assertIn("test_style: synthetic_fixture", record)
        self.assertIn("preflight: NOT_RUN", record)
        self.assertIn("lightweight_execution: PASS", record)
        self.assertIn("configured report rendered from isolated store", record)
        self.assertTrue((root / "tmp/tests/template/reports/brief.html").is_file())
        self.assertFalse((root / "brief.html").exists())
        self.assertFalse((root / "tmp/tests/template/input").exists())
        self.assertFalse((root / "Rplots.pdf").exists())
        make = 'source("renv/activate.R"); targets::tar_make(); '
        check = 'stopifnot(abs(targets::tar_read(analysis_results)$mean - 19.3/7) < 1e-12); '
        self.run_r(make + check + "saveRDS(targets::tar_meta(fields=c(name,time)), 'before.rds')", root)
        (root / "products/analysis_results.rds").unlink()
        self.run_r(make + check +
            "old <- readRDS('before.rds'); new <- targets::tar_meta(fields=c(name,time)); "
            "stopifnot(identical(old$time[old$name=='analysis_results'], new$time[new$name=='analysis_results'])); "
            "stopifnot(identical(readRDS('products/analysis_results.rds'), targets::tar_read(analysis_results)))", root)
        # Change content at the same path, preserving all code and settings.
        raw = root / "raw/input.tsv"
        raw.write_text(raw.read_text(encoding="utf-8").replace("treated\t8\n", "treated\t12\n"), encoding="utf-8")
        self.run_r(make +
            "stopifnot(abs(targets::tar_read(analysis_results)$mean - 23.3/7) < 1e-12); "
            "old <- readRDS('before.rds'); new <- targets::tar_meta(fields=c(name,time)); "
            "stopifnot(identical(old$time[old$name=='reference_constant'], new$time[new$name=='reference_constant'])); "
            "stopifnot(!identical(old$time[old$name=='analysis_results'], new$time[new$name=='analysis_results']))", root)
        moved = self.root / "moved complex project"
        shutil.copytree(root, moved, ignore=shutil.ignore_patterns("_targets", "products", "reports", "tmp", "before.rds"))
        self.run_r(make + "stopifnot(abs(targets::tar_read(analysis_results)$mean - 23.3/7) < 1e-12)", moved)
        self.assertTrue((moved / "products/analysis_results.rds").is_file())
        self.assertFalse((moved / "Rplots.pdf").exists())
        # The environment refuses an unrelated cwd before creating outputs.
        bad = self.run_r(f"source({str(moved / '00.Environment.R')!r})", self.root, success=False)
        self.assertIn("project root", bad.stderr)
        # Actual downstream failure and resume, separate from an unchanged run.
        control = root / "raw/recovery-control.txt"
        control.write_text("fail\n", encoding="utf-8")
        dag.write_text(dag.read_text(encoding="utf-8").replace(
            "list(\n  targets::tar_target(reference_constant",
            "list(\n  targets::tar_target(recovery_control, 'raw/recovery-control.txt', format='file'),\n"
            "  targets::tar_target(fragile_delivery, {\n"
            "    if (readLines(recovery_control) == 'fail') stop('injected downstream failure')\n"
            "    analysis_results\n  }),\n  targets::tar_target(reference_constant",
        ), encoding="utf-8")
        self.run_r("source('renv/activate.R'); saveRDS(targets::tar_meta(fields=c(name,time)), 'resume-before.rds')", root)
        failed = self.run_r(make, root, success=False)
        self.assertIn("injected downstream failure", failed.stdout + failed.stderr)
        control.write_text("pass\n", encoding="utf-8")
        self.run_r(make +
            "old <- readRDS('resume-before.rds'); new <- targets::tar_meta(fields=c(name,time)); "
            "stopifnot(identical(old$time[old$name=='analysis_results'], new$time[new$name=='analysis_results'])); "
            "stopifnot(identical(targets::tar_read(fragile_delivery), targets::tar_read(analysis_results)))", root)

    def test_simple_template_clean_render_rebuild_and_relocation(self):
        root = self.project("simple project", "simple")
        rmd = root / "report.Rmd"
        text = (self.installed / "templates/Rmd_simple_template.Rmd").read_text(encoding="utf-8")
        text += "\n```{r deliver-result}\nstopifnot(!exists('hidden_dependency', inherits=TRUE))\n" \
                "dir.create(products_dir, recursive=TRUE, showWarnings=FALSE)\n" \
                "saveRDS(mean(raw_data$value, na.rm=TRUE), file.path(products_dir, 'mean.rds'))\n```\n"
        rmd.write_text(text, encoding="utf-8")
        failed = self.run_r("source('scripts/tests/smoke_test.R')", root, success=False,
                            extra_env={"BENSZ_ANALYSIS_ENTRY": "report.Rmd", "BENSZ_TEST_RUN_ID": "no-assertions"})
        self.assertIn("assert_results.R", failed.stderr)
        self.assertFalse((root / "tmp/tests/no-assertions/run-record.md").exists())
        (root / "scripts/tests/assert_results.R").write_text(
            "stopifnot(abs(readRDS(file.path(context$products_dir, 'mean.rds')) - 19.3/7) < 1e-12)\n",
            encoding="utf-8",
        )
        self.run_r("hidden_dependency <- 999; source('scripts/tests/smoke_test.R')", root,
                   extra_env={"BENSZ_ANALYSIS_ENTRY": "report.Rmd", "BENSZ_TEST_RUN_ID": "template"})
        render = 'source("renv/activate.R"); rmarkdown::render("report.Rmd", quiet=TRUE); '
        self.run_r(render + "stopifnot(abs(readRDS('products/mean.rds')-19.3/7)<1e-12)", root)
        (root / "report.html").unlink()
        self.run_r(render + "stopifnot(file.info('report.html')$size>0)", root)
        raw = root / "raw/input.tsv"
        raw.write_text(raw.read_text(encoding="utf-8").replace("treated\t8\n", "treated\t12\n"), encoding="utf-8")
        self.run_r(render + "stopifnot(abs(readRDS('products/mean.rds')-23.3/7)<1e-12)", root)
        moved = self.root / "moved simple project"
        shutil.copytree(root, moved, ignore=shutil.ignore_patterns("products", "reports", "tmp", "report.html"))
        self.run_r(render + "stopifnot(abs(readRDS('products/mean.rds')-23.3/7)<1e-12)", moved)
        self.assertFalse((moved / "_targets.R").exists())

    def test_identity_environment_restore_and_deletion_guard(self):
        root = self.project("guards", "complex")
        self.run_r(
            "source('scripts/tests/test_harness.R'); "
            "Sys.setenv(BENSZ_ANALYSIS_INPUT='prior-input', BENSZ_TARGETS_STORE='prior-store'); "
            "x <- bensz_test_begin('new','complex','synthetic_fixture','_targets.R'); "
            "Sys.setenv(BENSZ_ANALYSIS_INPUT='changed', BENSZ_TARGETS_STORE='changed'); "
            "bensz_test_restore_environment(x); "
            "stopifnot(Sys.getenv('BENSZ_ANALYSIS_INPUT')=='prior-input', Sys.getenv('BENSZ_TARGETS_STORE')=='prior-store'); "
            "a <- x$subject_identity; cat('\\n# changed', file='renv/activate.R', append=TRUE); "
            "stopifnot(!identical(a, .bensz_subject_identity(x$run_root, x$identity_entries))); "
            "x$products_dir <- x$input_dir; "
            "failure <- tryCatch({bensz_test_remove_outputs(x); FALSE}, error=function(e) TRUE); "
            "stopifnot(failure, dir.exists(x$input_dir)); "
            "x$products_dir <- 'raw'; "
            "failure <- tryCatch({bensz_test_remove_outputs(x); FALSE}, error=function(e) TRUE); "
            "stopifnot(failure, file.exists('raw/input.tsv'))", root,
        )

    def test_harness_rejects_redirected_tmp_and_reused_run(self):
        root = self.project("run isolation", "complex")
        (root / "tmp").mkdir()
        (root / "tmp/tests").mkdir()
        (root / "tmp/tests/existing").mkdir()
        init = ("source('scripts/tests/test_harness.R'); "
                "bensz_test_begin('new','complex','synthetic_fixture','_targets.R')")
        failure = self.run_r(init, root, success=False, extra_env={"BENSZ_TEST_RUN_ID": "existing"})
        self.assertIn("already exists", failure.stderr)
        (root / "tmp/tests/existing").rmdir()
        (root / "tmp/tests").rmdir()
        try:
            (root / "tmp/tests").symlink_to(root / "raw", target_is_directory=True)
        except OSError as err:
            self.skipTest(f"directory symlinks not available: {err}")
        failure = self.run_r(init, root, success=False, extra_env={"BENSZ_TEST_RUN_ID": "isolated"})
        self.assertIn("Test directory", failure.stderr)
        self.assertFalse((root / "raw/isolated").exists())

    def test_subset_requires_explicit_source_and_does_not_claim_execution(self):
        root = self.project("subset contract", "complex")
        shutil.copy2(self.installed / "templates/tests/project_subset.R", root / "scripts/tests/test_data.R")
        self.run_r(
            "source('scripts/tests/test_harness.R'); "
            "x <- bensz_test_begin('new','complex','synthetic_fixture','_targets.R'); "
            "failure <- tryCatch({bensz_test_prepare_input(x); ''}, error=conditionMessage); "
            "stopifnot(grepl('authorized project_subset', failure, fixed=TRUE)); "
            "bensz_test_restore_environment(x); "
            "Sys.setenv(BENSZ_TEST_RUN_ID='explicit'); "
            "x <- bensz_test_begin('new','complex','project_subset','_targets.R'); "
            "failure <- tryCatch({bensz_test_prepare_input(x); ''}, error=conditionMessage); "
            "stopifnot(grepl('BENSZ_SOURCE_DATA', failure, fixed=TRUE)); "
            "Sys.setenv(BENSZ_SOURCE_DATA='raw/input.tsv'); "
            "path <- bensz_test_prepare_input(x); "
            "d <- read.delim(path); stopifnot(setequal(d$group, c('control','treated')), anyNA(d$value)); "
            "bensz_test_finish(x, 'data preparation only')",
            root, extra_env={"BENSZ_TEST_RUN_ID": "default"},
        )
        record = (root / "tmp/tests/explicit/run-record.md").read_text(encoding="utf-8")
        self.assertIn("preflight: NOT_RUN", record)
        self.assertIn("lightweight_execution: NOT_RUN", record)
        self.assertIn("full_data_execution: NOT_RUN", record)


if __name__ == "__main__":
    unittest.main()
