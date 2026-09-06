# Citation truth and fit

## Verification target

Assess whether a citation has the claimed source identity, whether the supplied
source excerpt entails the cited claim, and whether that source is appropriate
for the claim's use. A pass applies only to the submitted claim-and-source
snapshot; it does not certify an entire document or an unavailable full text.

## Inputs and evidence

Review normalized evidence references for `subject_context`, `source_metadata`,
and `source_excerpt`. The subject and context must identify the claim under review
and its intended use. Missing source identity, claim context, or supporting
excerpt is insufficient evidence and must not be inferred from citation metadata
alone.

## Execution

This is an instruction-only semantic verifier. Its required `agent` component—or
an explicitly authorized domain or human executor—compares source identity,
claim-to-excerpt entailment, and appropriateness, then returns a result bound to
the current contract, component, evidence, `run_id`, and `attempt_id`. The Kernel
does not perform the semantic judgment itself.

## Output and verdicts

Return `pass` only when the supplied evidence supports all three dimensions and
cite the evidence references used. Return `fail` with specific findings when the
evidence contradicts the claim or shows an identity or fit problem. Use
`uncertain` when the available evidence supports no reliable conclusion and
`unchecked` while no bound semantic result has been supplied.

## Failure and boundaries

Missing evidence, an unbound component result, unavailable source text, or an
unobservable external source cannot produce `pass`; unresolved cases require
additional evidence or manual review. Do not fabricate excerpts, infer support
from title similarity, or treat model confidence as a replacement for cited
evidence.
