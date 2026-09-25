# bensz-rmd-rules

An Agent Skill for **R data analysis, R Markdown reports, reproducible targets workflows, publication-quality plots, and evidence-anchored interpretation**. The current version is `skill_info.version` in [`config.yaml`](config.yaml); this directory is a beta candidate source.

## When to use it

Use it to turn raw data into preprocessing, statistics/models, plots, Rmd/HTML reports, scientific products, and result interpretation, or to maintain an existing R/Rmd project.

Do not use it when the primary deliverable is a reusable cross-project R function, class, stable API, or Package (use `bensz-r-developer`); when only an existing Rmd must be rendered (use `knit-rmd-html`); or for analysis in another language.

## Minimal prompt

```text
Please use bensz-rmd-rules for this R analysis. First inspect read-only whether the project is new or existing, then explain the choice between simple and targets-first complex/pipeline. Use renv and run a real lightweight synthetic_fixture or project_subset test from the formal entry point before the production run.
```

The Skill preserves existing projects: it does not automatically create targets/renv assets or migrate layouts; a project with `_targets.R` is maintained as complex, while an existing project without targets (including numbered scripts) is maintained with simple semantics.

## Workflow modes

| Mode | Use when | Required contract |
| --- | --- | --- |
| `simple` | Linear, inexpensive work where a full rerun is acceptable | `renv`, an explicit R/Rmd entry point, and a real lightweight test; no targets |
| `complex` (descriptive alias `pipeline`) | Non-linear dependencies, expensive steps, reuse, partial invalidation, recovery, or parallelism | `_targets.R` as the only DAG, compute functions in `R/`, Rmd consumes targets, and isolated-store recovery evidence |

`new`/`existing` describe project state, not a third mode: an existing `_targets.R` means complex; otherwise simple. Migration requires explicit human authorization.

The complex relationship is:

```text
renv.lock → _targets.R → R/ functions → target results → Rmd → reports/
                         ↘ optional products/
                         ↘ _targets/ (machine state)
```

`_targets/` stores machine computation state only. `products/` stores scientific objects that need review, reuse, or delivery; it is not a second cache, `SUCCESS` marker, identity-hash, or recovery runner.

## Recommended project layout

```text
project-root/
├── 00.Environment.R
├── R/                         # compute functions called by targets
├── _targets.R                 # the only complex DAG entry point
├── raw/                       # read-only
├── products/                  # optional scientific products
├── reports/                   # plots, tables, HTML, supplements
├── scripts/tests/             # versioned test code
├── tmp/tests/<run-id>/        # isolated test run
├── renv.lock
└── renv/activate.R
```

The [`_targets.R`](templates/_targets.R) template uses `tar_source("R")`; [`R_data_template.R`](templates/R_data_template.R) provides a data-preparation starting point; [`Rmd_template.Rmd`](templates/Rmd_template.Rmd) consumes `analysis_results` with `targets::tar_read()`; simple projects can start from [`Rmd_simple_template.Rmd`](templates/Rmd_simple_template.Rmd).

## Lightweight testing and recovery

Every new or materially changed flow must run one real test style:

- `synthetic_fixture`: when real data are unavailable, sensitive, or too large; preserve schema, types, keys, groups, missingness, and an edge case with a fixed seed.
- `project_subset`: when authorized data and existing code are available; use a representative subset covering key groups/outcomes/missingness/anomalies, not only `head(n)`.

Put test code in `scripts/tests/` and use a unique `tmp/tests/<run-id>/` per run. Simple invokes the formal entry point; complex runs the same DAG with a store under `<run-id>/_targets`, never the formal `_targets/`, `products/`, or `reports/`. Assert input contracts, key types/keys, important numeric invariants, product/report creation, and no writes to `raw/`. Record `full_data_execution=NOT_RUN` when the full dataset was not run.

For recovery evidence, first complete an expensive target, interrupt a later target, then rerun `tar_make()` with unchanged input, code, parameters, and renv identity. Use `tar_meta()`, the outdated set, and execution records to show valid upstream targets were skipped.

## Checks and script entry points

Inspect project state and mode first:

```bash
python3 <skill-root>/scripts/check_targets_renv.py <project> --project-state auto --workflow-mode auto
```

Common checks:

```bash
python3 <skill-root>/scripts/check_pipeline_contract.py <project>
python3 <skill-root>/scripts/check_interpretation_quality.py <project>/report.Rmd
python3 <skill-root>/scripts/check_figure_table_interpretation.py <project>/report.Rmd
python3 <skill-root>/scripts/check_htmlwidget_visibility.py <project>/report.Rmd
python3 <skill-root>/scripts/check_rmd_template_yaml.py <project>/report.Rmd
Rscript <project>/scripts/tests/smoke_test.R
```

Use [`check_plot_readability.R`](scripts/check_plot_readability.R) for plot readability and [`validate_paths.R`](scripts/validate_paths.R) for path safety. Initialize the Liquid Glass theme with [`bootstrap_liquid_glass.py`](scripts/bootstrap_liquid_glass.py); its desktop dynamic TOC expands the interactive area immediately so the pointer can enter the menu. Delegate HTML rendering to `knit-rmd-html`.

## Plot and interpretation rules

Plots default to English; switch with YAML `params.plot_language` for Chinese-journal contexts. Place an interpretation near every visible figure/table: current object, direction/comparison, traceable values, magnitude, uncertainty, and follow-up validation (method + input + criterion). See:

- [`four_tier_interpretation_framework.md`](references/four_tier_interpretation_framework.md): four-layer interpretation and the Fail Fast Gate.
- [`interpretation_templates.md`](references/interpretation_templates.md): univariate, multivariable, and model-validation skeletons.
- [`plot_quality_standards.md`](references/plot_quality_standards.md): publication-quality readability rules.
- [`liquid_glass_theme_guide.md`](references/liquid_glass_theme_guide.md): HTML theme and troubleshooting.

## Related templates and references

- Environment and dependencies: [`00.Environment.R`](templates/00.Environment.R), [`renv/activate.R`](templates/renv/activate.R).
- Testing: [`templates/tests/`](templates/tests/), [`lightweight_testing.md`](references/lightweight_testing.md).
- Modes and architecture: [`workflow_modes.md`](references/workflow_modes.md), [`hybrid_architecture_guide.md`](references/hybrid_architecture_guide.md).
- Delivery and review: [`delivery_verification.md`](references/delivery_verification.md), [`serial_review_protocol.md`](references/serial_review_protocol.md).

## FAQ and boundaries

**Can numbered scripts be migrated to targets automatically?** No. Existing projects without targets stay simple; migration needs explicit human authorization, mapping, result checks, and rollback.

**Can I add a custom checkpoint or `SUCCESS` file?** No. Complex uses targets metadata, invalidation, and incremental rebuilds; do not introduce a second cache/recovery protocol.

**Does a passing lightweight test mean the full dataset passed?** No. Report `preflight`, `lightweight_execution`, and `full_data_execution` separately; write `NOT_RUN` when the full run was skipped.

**What if I need a reusable R function?** Have `bensz-r-developer` implement it; this Skill owns analysis requirements, integration, and workflow evidence.

## License and contribution

See the repository-root `LICENSE` for licensing terms. When changing this Skill, keep `SKILL.md`, `config.yaml`, required references, and change records aligned, and run checks appropriate to the risk. Never put credentials, private data, or private prompts in `raw/` or the README.
