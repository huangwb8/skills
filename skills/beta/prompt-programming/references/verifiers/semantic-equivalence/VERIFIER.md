---
id: bensz.prompt.semantic-equivalence
version: 1.0.0
description: AI semantic judge for checking whether a Prompt Program faithfully preserves the source prompt.
classification: semantic
mode: prompt
assurance_tier: llm_judge
tags: prompt,semantic,ai,equivalence
aliases: prompt-programming.semantic-equivalence
prompt_pack_ref: PROMPT.md
---

# Prompt semantic equivalence

This verifier is an AI-assisted semantic judge. It is not a file-shape checker
and it must not infer correctness from the presence of headings alone. The host
Agent executes the rubric in `PROMPT.md`, then emits the standard verifier result
JSON. The Kernel records, normalizes and gates that result; it does not invoke a
model or treat an unavailable model as a pass.

## Evidence contract

The request must provide:

- `subject.source_prompt`: the original prompt as a UTF-8 string.
- `subject.program`: the candidate Prompt Program as a UTF-8 string.
- `context.rubric_version`: `1.0`.
- Optional `evidence`: stable references to extracted source/program spans. Do
  not copy secrets or unnecessary personal data into evidence.

The judge must assess all six criteria in `PROMPT.md` and cite stable anchors
such as `source:goal`, `program:流程[3]`, or a short redacted phrase. It must not
use external facts to manufacture missing requirements.

## Result contract

Return one standard result object:

- `verdict`: `pass` only when every required criterion passes; `fail` when a
  material omission, contradiction or invented capability is found; `uncertain`
  when evidence or model confidence is insufficient.
- `execution_status`: `completed` only when the rubric was actually evaluated;
  otherwise `unchecked`, `timed_out` or `error` as appropriate.
- `confidence`: number in `[0,1]`, reflecting semantic judgment confidence.
- `model_or_engine`: the model or judging engine identifier, without credentials.
- `findings`: structured entries with `criterion`, `severity` (`P0`–`P2`),
  `source_anchor`, `program_anchor`, `explanation`, and `recommendation`.
- `facts.criteria`: one entry for each rubric criterion with `status`,
  `confidence`, and evidence anchors.

The judge recommends corrections; it does not mutate the Prompt Program. Any
`uncertain` result or unavailable model must remain a Gate-visible review gap.
