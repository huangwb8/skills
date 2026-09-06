# Contract conformance

## Verification target

Confirm that every field named by `context.required_fields` exists at the top
level of the request subject. This verifier checks presence only; it does not
interpret field values or enforce a domain schema.

## Inputs and evidence

`subject` is the object being checked. `context.required_fields` is the list of
required top-level keys; when omitted, the list is empty. No separate evidence
objects are consumed.

## Execution

The deterministic script compares the declared key names with the subject's
top-level keys. Extra fields are allowed, and present values are not checked for
type, emptiness, or semantic correctness.

## Output and verdicts

It returns `pass` when no required key is missing. Otherwise it returns `fail`,
records the required and missing fields in `facts`, and emits one `missing-field`
finding for each missing key.

## Failure and boundaries

An empty or omitted requirement list passes vacuously. Callers that need nested
structure, value types, or content constraints must use a schema or domain
verifier instead of treating this presence check as full contract validation.
