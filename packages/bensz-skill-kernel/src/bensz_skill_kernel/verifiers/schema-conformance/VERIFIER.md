# Schema conformance

## Verification target

Confirm that the checked data object contains every key listed in
`context.schema.required`. This is a minimal required-key check, not a complete
JSON Schema implementation.

## Inputs and evidence

The checked value is `subject.data` when present, otherwise the whole `subject`.
Required keys come from `context.schema.required`; an absent or non-object schema
produces an empty requirement list. No separate evidence objects are used.

## Execution

The deterministic script verifies that the checked value is an object and that
each required key is present at its top level. It does not validate types,
formats, nested schemas, additional properties, or field semantics.

## Output and verdicts

It returns `pass` when no required key is missing. Otherwise it returns `fail`,
records missing keys in `facts`, and emits one `schema-required-field` finding per
missing key.

## Failure and boundaries

An empty requirement list passes vacuously. Callers needing full schema
validation must use a dedicated validator and must not interpret this result as
proof of type, value, or semantic conformance.
