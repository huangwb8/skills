# bensz-rmd-rules

[简体中文](README.md) · [Skill instructions](SKILL.md)

Use R to investigate a scientific question in depth. `targets` manages the analysis and incremental rebuilds, and `renv` locks the environment. Rmd brings the actual code, figures, tables, and inline results into a complete research report.

## Quick start

```text
Use bensz-rmd-rules to analyze these follow-up measurements and deliver Rmd and HTML.
Show the size of the change, who entered the comparison, and what the result can support.
```

To try a runnable synthetic example, you need Python 3.11+, R, Pandoc, and `renv` in the host R library. From the repository root:

```sh
python3 skills/beta/bensz-rmd-rules/scripts/new_project.py demo-rmd
cd demo-rmd
Rscript --vanilla run.R prepare
Rscript --vanilla run.R build
```

Open `01.01.01-paired-change.html` for a paper-style report based on synthetic data, from the abstract, introduction, and paired analysis methods through the results, an influence check, quality control, and discussion. The default Liquid Glass theme provides a floating desktop table of contents, a collapsible mobile table of contents, image zoom, and code copying. Add `--detail` for a searchable table of individual records from the same analysis (`--dt` remains an alias). To change the appearance, use `--theme plain` or `--theme flatly`. All three themes number body headings by default.

The report explains why it uses complete pairs before showing the actual pipeline code, expanded by default. Inline R supplies the denominator, estimate, and interval from the same values as the DT summary table. The demo CSV has one row per unit and requires the `unit`, `before`, and `after` columns. When an interval cannot be estimated, the report explains why and retains the mean change if available. If you replace the sample data, revise the title, interpretation, and conclusions to fit your study and results.

## When to use it

Use it to analyze data with R, deliver a scientific report readers can check, or rewrite a report around existing results. Use `knit-rmd-html` when you only need to render existing Rmd. Use `bensz-r-developer` when the main deliverable is a reusable R library or package.

## Inputs and outputs

Describe the reader, decision, data location, and any limits on analysis or access. The Skill uses targets and renv and delivers Rmd, HTML, analysis code, the environment lock, and verification notes. For an existing project, you can limit the work to the report and check and reuse results through the formal entry point.

Every new analysis delivers a paper-style report that readers can check. The title states the subject and scope. The abstract labels Background, Methods, Results, and Conclusions in that order. Present each major effect with its interval, applicable threshold, and decision. Use inline R for computed values and show the actual code that best explains how to read the figure or table. Read the final report, restate the main judgments, and trace the supporting evidence. See [the full report guide](references/report.md#把完整研究写成论文式报告).

When a delivery includes several standalone reports, start with the reading guide at the top of the project README. New Rmd and HTML pairs share a three-level prefix such as `01.01.01-`. Read lower numbers first. Longer common prefixes indicate more closely related questions. The main report gives the evidence needed for major decisions and links to the sections that provide supporting analyses. A single report can omit its prefix. Body section numbers follow the heading hierarchy. Set `number_sections: false` when numbering must be disabled. See [reading order for multiple reports](references/delivery.md#多报告的阅读顺序) and [HTML section numbering](references/visuals.md#html-章节编号).

## Examples

### Basic example

```text
Analyze paired measurements from baseline and follow-up and deliver a complete report.
Start with an everyday example, then define eligible pairs in a formula and in code.
Show individual changes, check how much single observations affect the mean,
and explain how missing follow-up affects the conclusion.
```

### Advanced example

```text
Rewrite the report using checked results from the existing targets pipeline.
Lead with the recommendation and exceptions. Put effects, intervals, and prespecified thresholds
together and explain failed or inestimable comparisons. Show how the code produces the key figure
or table values, put the wide table in a searchable appendix, and reuse the fit when only prose changes.
```

## Environment and scripts

The example keeps its environment, lockfile, and analysis settings in `00.Environments/`. Use the [project generator](scripts/new_project.py), set up your own project, or keep an existing entry point as appropriate for the study. In the example, prepare the environment with `run.R prepare`, restore it from the lockfile with `run.R restore`, and use `run.R update-lock` when you intend to revise dependencies. See [computation, environment, and rebuild](references/workflow.md) for complete commands. This Skill is in the beta source and must be selected explicitly.

To adapt the starter example, find the main report and analysis entry point in the Skill's [project scaffold](templates/project/). Use `--detail` to add the [detail appendix](templates/detail/). The [assets directory](assets/) holds the Liquid Glass theme, which the generator copies when selected, and plotting code you can use as needed.

## FAQ

- **Can I edit the report on its own?** Yes. Run `Rscript --vanilla run.R report` in a starter project. Missing or stale targets results prompt you to run `Rscript --vanilla run.R build`.
- **Where does the HTML go?** By default it shares the Rmd's directory and basename. Use `reports/` for standalone figures and tables, and `products/` for reusable results, according to the project's layout.
- **How should I display tables?** Use `DT::datatable()` for every table in the main text or appendix. Hide controls on compact summaries and enable them as needed on detail tables. All embedded data is sent with the HTML, so check permissions before publishing.
- **What language do reports, figures, and tables use?** Figures and tables default to English for reuse in manuscripts. Report prose follows your requested language or, if unspecified, the language of your request. You can specify a different language for figures and tables. In the paired example, set `params.plot_language` or `params.table_language` to `zh` in the Rmd to switch figures or tables to Chinese independently.
- **What is the default figure style?** Use readable type, a publication-ready palette, and a white background. Put the figure title in the caption and the interpretation in the report prose. Prefer vector PDF for standalone static figures.

More: [inference and reporting](references/report.md) · [themes and figures](references/visuals.md) · [testing and delivery](references/delivery.md)
