# Task completeness

## Verification target

Confirm that the task subject contains truthy values for every declared completion
field. This verifier checks a minimal completion shape; it does not independently
validate artifacts, verification results, delivery quality, or external effects.

## Inputs and evidence

`subject` contains the task summary. `context.required_fields` optionally selects
the fields to check and defaults to `artifacts`, `verifications`, and
`delivery_report`. No separate evidence objects are inspected.

## Execution

The deterministic script reads each required top-level field and treats Python
falsey values, including absent keys, `null`, empty strings, empty lists, and
empty objects, as missing.

## Output and verdicts

It returns `pass` when every required field is truthy. Otherwise it returns
`fail`, records missing fields in `facts`, and emits one `task-incomplete`
finding for each missing field.

## Failure and boundaries

An explicitly empty required-field list passes vacuously. A pass is not a
substitute for required Verifier results, Gate approval, event integrity, artifact
existence, or authorization checks; callers must apply those contracts separately.
