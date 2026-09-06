# Event integrity

## Verification target

Confirm that the event log referenced by `subject.path` can be read by the Kernel
event-log parser without an integrity or format error. A pass does not assert that
the recorded workflow is complete or that its business outcome is correct.

## Inputs and evidence

`subject.path` is required and identifies the event log to read. The verifier does
not consume separate evidence objects; the log at that path is the checked source.

## Execution

The deterministic script opens the log through `EventLog.read()`, which applies
the Kernel's replay validation, and counts the accepted events. It is read-only
with respect to the event log.

## Output and verdicts

A successful read returns `pass` with `facts.event_count`. A missing path returns
`fail` with `missing-events-path`; a read or integrity exception returns `fail`
with an `event-integrity` finding and a diagnostic `uncertainty_reason`.

## Failure and boundaries

This verifier intentionally reports log read/integrity exceptions as `fail`, not
as a semantic judgment about the task. It does not check required event types,
Gate coverage, state correctness, or whether events describe truthful external
facts; those require dedicated verifiers or review.
