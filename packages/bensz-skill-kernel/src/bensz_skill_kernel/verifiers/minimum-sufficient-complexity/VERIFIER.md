# Minimum sufficient complexity

## Verification target

Confirm that, within the submitted objective, scope, constraints, required
capabilities, and invariants, no material part of the design is dominated by a
concrete, feasible, and simpler alternative. “Simpler” compares conceptual
entities, indirection, duplicate sources of truth, special cases, cognitive,
operational, and maintenance costs; it is not a fixed threshold for lines,
files, or sections.

This verifier does not judge personal taste, functional correctness, security,
factual truth, performance, or global optimality. It must not recommend removing
complexity whose required capability or risk protection has not been preserved.

## Inputs and evidence

`subject` must identify the reviewed `artifact_kind`, `scope`, and a bounded
`snapshot` or design summary. Optional `design_decisions` may enumerate notable
entities and their stated purposes, but missing author intent must not be
invented.

`context` should provide `objective`, `required_capabilities`, `invariants`,
`constraints`, `accepted_tradeoffs`, and evidence-backed
`known_change_scenarios`. The evidence set must anchor the objective and scope,
current constraints, and the reviewed artifact or design snapshot. Evidence
references must remain auditable and must not contain raw credentials or
unnecessary full documents.

Missing objective, constraints, required capabilities, or a reviewable snapshot
is insufficient for a reliable pass/fail judgment.

## Execution

The required `agent` component performs a two-pass review. First it maps each
material design entity to the current goal, constraint, invariant, or evidenced
near-term change. Then, for each apparently incidental entity, it proposes a
concrete simpler alternative and tests whether the same required capability,
correctness boundary, security boundary, compatibility, and auditability remain.

The agent may return `fail` only when an alternative is concrete and materially
dominates the current design on at least one relevant complexity dimension
without an unacknowledged regression. It must record genuine trade-offs rather
than collapse them into a score. The component has no write, filesystem, or
network side effects; the host controls any bounded snapshot preparation.

## Output and verdicts

Return `pass` when the reviewed evidence contains no material dominated design
entity. This means “none found in scope”, not “globally optimal”.

Return `fail` only with a finding that names the current entity and purpose, a
concrete simpler alternative, preserved constraints/capabilities, complexity
reduction, migration risk, and the evidence references supporting those claims.
Use finding IDs such as `unjustified-entity`, `avoidable-indirection`,
`duplicate-source-of-truth`, or `premature-generality` only as explanatory
categories.

Return `uncertain` when evidence is incomplete, a candidate simplification has
an unresolved capability or migration trade-off, or the conclusion requires
domain expertise. Return `unchecked` while no bound agent result is supplied.
Use `error` or `timed_out` for execution failures; neither may be rewritten as
`pass`.

Facts should summarize `scope_reviewed`, `essential_complexity`,
`incidental_complexity`, `alternatives_considered`, and `tradeoffs`. Always
return the evidence references actually used.

## Failure and boundaries

Do not fail a design merely because it is unfamiliar, verbose, abstract, or
different from the reviewer’s preferred style. Do not infer future requirements
from speculation, and do not treat shorter text or fewer files as proof of
simplicity. When no Pareto-dominating alternative exists, preserve the trade-off
and return `pass` or `uncertain` according to evidence quality.

Missing or unobservable evidence follows the declared uncertainty policy:
required callers wait for missing evidence and require human review for an
unresolved trade-off. The verifier never edits the subject, performs automatic
refactoring, schedules sub-agents, or stores complete private artifacts in the
event log.
