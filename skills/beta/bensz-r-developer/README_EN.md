<div align="center">
  <h1>bensz-r-developer</h1>
  <p><strong>Build maintainable R functions and packages with class-driven APIs, explicit output/cache boundaries, and controlled performance strategies.</strong></p>
  <p>Beta Skill · R functions and packages · S3/S4/R6 · devtools/roxygen2/testthat</p>
  <p><a href="README.md">中文 README.md</a> · English README_EN.md · <a href="#quick-start">Quick Start</a> · <a href="templates/demo-package/">Demo Package</a> · <a href="references/">Design references</a></p>
</div>

`bensz-r-developer` turns a set of R development preferences into a reusable engineering contract: model the domain first, separate final outputs from rebuildable caches, keep an `if (FALSE)` manual-test block near the function, and set explicit gates for parallelism, performance work, and C++ escalation. It supports both standalone code and complete R packages.

## Scope

Use it to:

- create or refactor R functions, S3/S4/R6 classes, and methods;
- develop, maintain, or review R packages;
- define `output.dir`, `cache.dir`, overwrite, and recovery semantics;
- implement reproducible parallelism or evaluate `cpp11`/`Rcpp` acceleration.

Do not use it merely to run existing code or when the main deliverable is an R Markdown report, research-analysis workflow, or publication figure; use `bensz-rmd-rules` for those tasks.

## Quick Start

### Minimal prompt

```text
Use bensz-r-developer to build an R function.
Input: a data.frame.
Requirements: define an appropriate class first; write final files to output.dir and rebuildable intermediates to cache.dir; keep an if (FALSE) manual-test block near the top; add testthat coverage.
```

### Advanced prompt

```text
Use bensz-r-developer to maintain this R package.
Inspect the existing classes, DESCRIPTION, NAMESPACE, R/, tests/, and src/ first, and preserve public API compatibility.
Add reproducible parallel batch computation without leaking changes to the caller's future plan; profile before deciding whether cpp11/Rcpp is justified.
Then run devtools::document(), devtools::test(), and devtools::check(cran = FALSE), and report sequential/parallel equivalence, cache recovery, and remaining risks.
```

## Inputs and outputs

| Item | Content |
|---|---|
| Inputs | Requirements, existing R files or package, data contract, R/platform/dependency constraints, and hardware limits |
| Main outputs | R source, classes/generics/methods, roxygen2 docs, testthat tests, and a manual-test block |
| Package outputs | Synchronized `DESCRIPTION`, `NAMESPACE`, README/CHANGELOG, and check results |
| Performance outputs | Profile/benchmark, sequential/parallel or R/C++ equivalence evidence, and rollback path |
| Process artifacts | The current project's single `.bensz-api/task-*/bensz-r-developer/` workspace |

## Recommended workflow

### Function development

Define input, return, error, and side-effect contracts first. Introduce a class only when the data has meaningful invariants or a lifecycle: prefer S3 for lightweight value objects, S4 for formal schemas or multiple dispatch, and R6 for mutable-resource lifecycles. Use separate parameters for final outputs and cache; `NULL` means no persistence, and overwrite is denied by default.

### Package development

Use `usethis` for structure, roxygen2 for documentation and NAMESPACE, testthat for automated tests, and devtools for the development loop. The `if (FALSE)` block supports line-by-line debugging and does not replace automated tests; `DESCRIPTION` remains the dependency contract.

### Parallel and high-performance work

Profile first, then improve algorithms, vectorization, copies/I/O, and chunking before parallelism or native code. Package code respects the caller's future plan and reserves one logical core by default; full-device aggressive mode requires an explicit request plus memory, threading, and recovery review. C++ work keeps an R reference implementation and equivalence tests.

## Demo Package

[templates/demo-package/](templates/demo-package/) is a runnable minimal package with an S3 constructor/validator/print/execution method, `output.dir`/`cache.dir`, rollback-capable transactional outputs and a manifest, `filelock` cache locking, future-based parallelism, and testthat. It builds manual test data from `iris` and contains no private paths or real business data.

```r
devtools::document("templates/demo-package")
devtools::test("templates/demo-package")
devtools::check("templates/demo-package", cran = FALSE)
```

The demo passes testthat and `R CMD check --no-manual`. After copying it, replace the package name, author, license, domain object, and demonstration statistics.

## Choosing adjacent skills

| Need | Use |
|---|---|
| R functions, classes, packages, parallelism, native performance | `bensz-r-developer` |
| R Markdown, research orchestration, cache recovery, publication figures, interpretation | `bensz-rmd-rules` |
| Only render an `.Rmd` file to HTML | `knit-rmd-html` |
| Explicitly test an Agent Skill | `auto-test-skill` |

## Configuration and references

- [SKILL.md](SKILL.md): AI execution contract and safety boundaries.
- [config.yaml](config.yaml): stable defaults for class selection, parallelism, native acceleration, and package tooling.
- [Classes and APIs](references/class-api-design.md): S3/S4/R6 selection and minimal object contracts.
- [Outputs and cache](references/io-cache-contract.md): persistence, cache identity, atomic writes, and manifests.
- [Parallelism and performance](references/parallel-performance.md): future, RNG, resource budgets, and C++ gates.
- [Package workflow](references/package-workflow.md): the usethis/roxygen2/testthat/devtools loop.

## WHICHMODEL: model selection

> Last researched: 2026-09-19. These are task-tier recommendations, not a permanent leaderboard.

| Scenario | OpenAI | Anthropic | Suggested reasoning tier |
|---|---|---|---|
| Architecture, parallelism, cache, and C++ boundaries | GPT-6 Astra | Claude Opus 5 | Start at medium/high; increase only when evidence warrants it |
| Everyday functions, roxygen2, testthat, and package maintenance | GPT-5.6 Terra | Claude Sonnet 5 | Default |
| Formatting, naming, and local fixes with explicit assertions | GPT-5.6 Luna | Claude Haiku 4.5 | low/default |

Selection order: first meet the correctness target with a capable model and establish tests, then try faster and cheaper tiers against the same acceptance set. Higher reasoning effort can improve complex work but costs more time and tokens; general leaderboards do not replace project-specific regression tests.

Sources: [OpenAI Codex models](https://developers.openai.com/codex/models), [OpenAI model selection](https://developers.openai.com/api/docs/guides/model-selection), [Claude models overview](https://platform.claude.com/docs/en/models/overview), and [SWE-bench](https://www.swebench.com/). No cross-model evaluation was run for this Skill, and model availability may change.

## FAQ

### Must every task start with a class?

No. A plain function is clearer when the object has no stable invariants, identity, or lifecycle. Avoid class wrappers that add ceremony without protecting a real contract.

### Why keep both a manual block and testthat?

`if (FALSE)` lets maintainers load data, change parameters, and debug line by line in an IDE. testthat provides automated regression and CI coverage. They solve different problems.

### Does the Skill install R packages or change global parallel settings?

No. Missing dependencies should be reported with package names and reproducible commands. Package functions must not silently change the working directory, RNG, options, or future plan.

### When is C++ justified?

Only when profiling locates a suitable hot kernel, mature R packages cannot solve it, cross-language copying is acceptable, and an R reference implementation plus equivalence tests already exist.
