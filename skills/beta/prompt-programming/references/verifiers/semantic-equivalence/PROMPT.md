# AI semantic-equivalence rubric v1.0

Compare `source_prompt` with `program` as two representations of the same task.
Reason over the complete source before judging individual blocks. Do not reward
the candidate merely for containing the expected headings.

Evaluate every criterion below:

1. **Intent and deliverables** — every material goal, actor responsibility and
   requested deliverable in the source is represented; no central goal is
   weakened or replaced.
2. **Inputs and outputs** — paths, variables, formats, filenames, field names,
   recipients and output boundaries are preserved exactly unless the Program
   explicitly resolves an ambiguity.
3. **Control-flow fidelity** — explicit ordering, loops, parallelism, branches,
   retries, stopping conditions and failure fallbacks are preserved and remain
   executable.
4. **Hard constraints and safety** — mandatory, forbidden, authorization,
   privacy, scope and compatibility constraints are retained; soft preferences
   are not promoted into hard requirements without evidence.
5. **Ambiguity and conflict handling** — contradictions or missing information
   are surfaced, and any resolution is conservative, traceable and consistent
   with the source intent rather than silently invented.
6. **No invention or omission** — the Program adds no unsupported capability,
   data source, authority or success condition, and does not omit a material
   requirement already captured by another criterion.

For each criterion emit `pass`, `fail` or `uncertain`, confidence, and at least
one source/program anchor. Use severity as follows:

- `P0`: changes the task objective, authorization boundary or safety meaning.
- `P1`: omits or contradicts a material input, output, control or hard
  constraint.
- `P2`: local ambiguity, weak traceability or non-critical clarity defect.

Overall decision:

- `pass`: all criteria pass and no P0/P1 finding exists.
- `fail`: any P0/P1 finding exists, or the representation is materially not
  equivalent.
- `uncertain`: evidence is insufficient or the model cannot confidently decide;
  never convert uncertainty into pass.
