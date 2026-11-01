# humanization — Natural prose editing

[中文](README.md) · [Execution contract](SKILL.md) · [Configuration](config.yaml) · [Regression and evaluation](references/regression-cases.md)

Make existing prose natural, clear and coherent. Edit articles, emails, reports, everyday explanations, academic writing and technical documents: understand the content and intent, then improve progression, transitions, rhythm and tone while preserving facts, stance, necessary boundaries and formatting. Already effective prose may remain unchanged.

## Quick start

```text
Polish the following text so it reads naturally, clearly and coherently. Return only the prose.
Preserve the meaning, facts and tone. Add no new content.

[Paste source text]
```

A clear request to polish existing text can trigger the Skill; naming `humanization` also works. Defaults adapt to the source language, purpose and tone, with moderate editing, original line and paragraph structure, and two internal expression/safety reviews. No style selection is required. Use `output_mode=diagnosis_only` for diagnosis without rewriting.

To install, run from this repository with Python 3.11+:

```bash
python3 skills/alpha/install-bensz-skills/scripts/install.py --skill humanization
```

Natural language requests and installer arguments accept the legacy name `nsfc-humanization`; the installed directory is always `humanization`. The legacy name no longer restricts the subject area.

## Scope

Use it to polish existing prose, reduce formulaic wording, adjust tone or improve transitions in blog posts, emails, work reports, product explanations, academic papers and technical documents. Chinese, English and mixed text retain their language and follow its conventions. Without a specified audience, purpose or style, it follows the source rather than asking for parameters. An ordinary request such as “explain caching” does not trigger it automatically.

This Skill edits the expression of existing content. It does not write from scratch, supply facts, retrieve/verify evidence, perform translation alone or change layouts. Use `better-prompt` to design prompt behavior and `write-readme` to author a complete project README; this Skill can polish the natural language within those materials. Its rules apply within the current invocation without changing global conversation style or promising to reproduce a particular model's writing experience.

## Styles and parameters

Parameters are read by the Agent; they are not rewrite CLI flags. Defaults are defined in [config.yaml](config.yaml).

| Parameter | Values and purpose |
| --- | --- |
| `style_profile` | `auto` (default): adapt to purpose, audience and source; `general_prose`: general writing; `academic_general`: general academic prose; `natural_explanation`: clear, approachable explanation; `technical_prose`: precise, direct technical prose; `professional_communication`: courteous, direct workplace communication |
| `section_type` | Optional document role hint, such as `通用`, `文章`, `邮件`, `报告` or `说明`; legacy section values remain valid, as defined in the configuration, and apply only when supported by the source or explicitly requested |
| `field` | `general`, `cs`, `engineering`, `medicine`, `life_science`; adjusts the register of existing terminology only |
| `strength` | `minimal`, `moderate` (default), `aggressive`; controls expression changes without relaxing protection |
| `structure_mode` | `preserve` (default) keeps line and paragraph structure; `reflow_plain` explicitly permits reparagraphing continuous plain text, falling back to preservation for LaTeX/headings/lists/code/tables |
| `output_mode` | `text_only` (default), `text_with_change_summary`, `diagnosis_only`, `text_with_change_summary_and_style_card` |
| `self_eval_rounds` | `1` or `2` (default), capped by `max_self_eval_rounds`; one round still checks expression and safety |

Style selection follows user requirements first, then the source; without clear cues, it uses `general_prose`. Emails gain no unsolicited apologies or promises, academic prose gains no stronger evidence, and technical explanations retain interfaces and necessary steps. Existing parameters and values remain valid. The legacy `nsfc_academic` value maps to formal academic writing without imposing grant section templates. No style or editing strength changes meaning or formatting permissions.

## Advanced examples

### Email tone

```text
Use humanization to polish this email to a colleague.
Keep it natural, polite and direct. Preserve the request's force and schedule; add no apologies or promises.

[Paste source text]
```

### Technical and academic text

```text
Use humanization with style_profile=technical_prose and output_mode=text_with_change_summary to polish this technical explanation.
Preserve interface names, code, numbers, conditions and failure handling. Add no features or steps.

[Paste source text]
```

### Coherence across paragraphs

```text
Use humanization with structure_mode=reflow_plain to edit this continuous plain text.
You may reorder sentences, merge or split paragraphs. Resolve idea progression before polishing wording.
Use only the source information; output_mode=text_with_change_summary.

[Paste source text]
```

Use `academic_general` for academic prose or `natural_explanation` for explanations to nonspecialists. Provide adjacent paragraphs for cross-section deduplication. Structure is preserved by default, with relocation suggested separately. Definitions and boundaries may recur where sections need to stand alone. Technical procedures and genuinely parallel information may still use lists.

## Output and protection checks

The default returns clean prose without scores or diagnostic tables. Summary modes briefly describe substantive changes and unresolved issues; detailed audit tables are available on request. Uncertain sentences remain unchanged, with review notes outside the prose. A style card can carry the register, terminology and boundaries into later batches.

For Chinese text containing technical tokens, use the standard-library helper for a conservative comparison; both inputs are read only:

```bash
python3 skills/alpha/humanization/scripts/check_revision.py original.txt revised.txt --structure-mode preserve
```

Exit `0` means the covered lexical protection checks passed, `1` means differences were found, and `2` means the input or mode could not be checked reliably. The helper checks common LaTeX arguments, math, citations, comments, code, numbers, English tokens and line structure. Complex TeX macros require human review. Ordinary English edits also appear as differences, and percent or currency symbols in plain text may be treated as TeX syntax. Compare those cases manually instead of freezing English prose to pass the check. The helper cannot judge intent, promises, denominator changes or stronger causal claims; a lexical pass always requires semantic review. The script can run from any directory using its absolute path.

## FAQ

**Must every paragraph start with a claim?** No. Content determines paragraph shape; setup, comparison and inference are valid, and transitions can follow naturally through meaning.

**Does everything become academic prose?** No. The default adapts to purpose, audience and source, preserving the conventions of articles, emails and explanations.

**Does it remove all English terms or negative statements?** No. Ordinary English can be edited naturally, while names and technical tokens remain stable. Necessary distinctions, independent qualifications and useful technical structure remain. First-use explanations require source support.

**Why not always use maximum strength?** Naturalness is not the amount of editing. The default is moderate, with an explicit comparison of source and revision. Good source prose may remain untouched.

**Can it fill a missing argument?** It can reconnect information already in the source. Missing evidence or explanations remain for the author to supply.

## Evaluation and limits

[Regression cases](references/regression-cases.md) cover articles, emails, explanations, English editing, progression, false contrasts, excessive structure, missing explanation, professional boundaries, no-change cases, LaTeX and register differences, with an eight-dimension rubric and an anonymous review procedure. [Natural writing principles](references/natural-writing.md) explain positive organization; the [pattern reference](references/machine-patterns.md) helps locate specific obstacles.

Automated tests can detect lexical and formatting regressions, not prove better prose. Small comparisons judged by Agents using the same model provide preliminary evidence only. Real long-form texts, repeated blind reviews and user feedback remain necessary; self-assessment and illustrative revisions are not successful benchmark runs.

The sole version source is [config.yaml](config.yaml); see [CHANGELOG.md](CHANGELOG.md) for history.

Chinese README.md and English README_EN.md are kept aligned.
