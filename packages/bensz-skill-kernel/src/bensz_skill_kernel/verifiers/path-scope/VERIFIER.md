# Path scope

## Verification target

Confirm that each submitted subject path resolves to an allowed path or one of its
descendants. A pass establishes lexical containment after path resolution; it
does not authorize an operation or validate the target's contents.

## Inputs and evidence

Paths come from `subject.paths`, or from the single `subject.path` fallback.
`context.allowed_paths` supplies the allowed roots. No separate evidence objects
are consumed, and allowed roots need not already exist.

## Execution

The deterministic script expands user markers, resolves each target and allowed
root, then checks equality or ancestor containment. It performs no file write and
does not require the target path to exist.

## Output and verdicts

It returns `pass` when all submitted targets are within at least one allowed root.
Otherwise it returns `fail`, records submitted paths and resolved violations in
`facts`, and emits a `path-out-of-scope` finding for each violation.

## Failure and boundaries

An empty target list passes vacuously; a non-empty target list with no allowed
roots fails. This check does not grant permission, protect against a later
symlink swap, or inspect side effects, so callers must still apply authorization
and operation-specific safeguards at execution time.
