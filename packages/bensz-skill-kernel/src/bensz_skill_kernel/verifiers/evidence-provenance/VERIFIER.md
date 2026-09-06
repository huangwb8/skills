# Evidence provenance

## Verification target

Confirm that every supplied evidence object carries the minimum provenance fields
needed for audit: `source_type`, `content_hash`, and `collected_at`. This verifier
checks field presence only, not source truthfulness or evidentiary fit.

## Inputs and evidence

The request's `evidence` collection is indexed by each item's `ref`. Each item is
expected to provide non-empty `source_type`, `content_hash`, and `collected_at`
values. `subject` and `context` are not used for this check.

## Execution

The deterministic script examines those three fields on every normalized evidence
item. It does not retrieve the source, recompute the hash, assess freshness, or
inspect the evidence content.

## Output and verdicts

It returns `pass` with `facts.evidence_count` when all supplied items meet the
minimum shape. Otherwise it returns `fail` and emits a `missing-provenance`
finding containing each invalid evidence reference.

## Failure and boundaries

An empty evidence collection passes vacuously; callers that require evidence must
enforce its presence separately. A pass does not establish source authenticity,
claim support, recency, or successful redaction.
