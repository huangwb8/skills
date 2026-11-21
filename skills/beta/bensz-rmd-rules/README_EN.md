# bensz-rmd-rules

[简体中文](README.md) · [Skill instructions](SKILL.md)

Build an argument around a scientific question worth answering. Everyday examples build intuition, formulas and code define the comparison, and figures, tables, and prose explain what the evidence supports. Use Rmd directly for small analyses and targets for expensive computations, so report edits can reuse results that are still valid.

## Quick start

```text
Use bensz-rmd-rules to analyze these follow-up measurements and deliver Rmd and HTML.
Show the size of the change, who entered the comparison, and what the result can support.
```

To try a runnable synthetic example, you need Python 3.11+, R, Pandoc, and `renv` in the host R library. From the repository root:

```sh
python3 skills/beta/bensz-rmd-rules/scripts/new_project.py simple demo-rmd
cd demo-rmd
Rscript --vanilla run.R prepare
Rscript --vanilla run.R build
```

Open `report.html` to see how a commuting example introduces a formula for paired differences, then how a plot and a summary table explain synthetic results. Replace `simple` with `complex` to try targets, or add `--dt --theme flatly` for a searchable, horizontally scrollable table and an optional theme.

## When to use it

Use it to analyze data with R, deliver a scientific report readers can check, or rewrite a report around existing results. Use `knit-rmd-html` when you only need to render existing Rmd. Use `bensz-r-developer` when the main deliverable is a reusable R library or package.

## Inputs and outputs

Describe the reader, decision, data location, and any limits on analysis or access. The Skill chooses a computation path based on cost and delivers Rmd, HTML, the necessary analysis code, the environment lock, and verification notes. For an existing project, you can limit the work to the report and check the results through the project's current entry point.

## Examples

### Basic example

```text
Write a one-page briefing for the group. Start with an everyday example, then
define eligible pairs in a formula and in code. Plot the individual changes and
explain how missing follow-up affects the conclusion.
```

### Advanced example

```text
Rewrite the report using checked results from the existing targets pipeline.
Lead with the recommendation and exceptions. Show the code that defines the comparison,
put the wide table in a searchable appendix, and reuse the fit when only prose changes.
```

## Environment and scripts

`00.Environments/` holds the project environment, lockfile, and analysis settings. Use the [project generator](scripts/new_project.py) to start a new directory. Prepare the environment with `run.R prepare`, restore it from the lockfile with `run.R restore`, and use `run.R update-lock` when you intend to revise dependencies. See [computation, environment, and rebuild](references/workflow.md) for complete commands. This Skill is in the beta source and must be selected explicitly.

## FAQ

- **Can I edit the report on its own?** Yes. Run `Rscript --vanilla run.R report` in a starter project. In complex mode, a missing or stale result prompts you to run `Rscript --vanilla run.R build`.
- **Where does the HTML go?** By default it shares the Rmd's directory and basename. Use `reports/` for standalone figures and tables, and `products/` for reusable results, according to the project's layout.
- **Does every report need DT?** Static tables work well in the main text. Use DT for details that readers need to look up. All embedded data is sent with the HTML, so check permissions before publishing.

More: [inference and reporting](references/report.md) · [testing and delivery](references/delivery.md)
