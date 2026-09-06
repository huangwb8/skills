# Secret redaction

## Verification target

Check the serialized request subject for a small set of token, password, cookie,
API-key, and `sk-`-style secret patterns. A pass means none of the configured
patterns matched; it does not prove that the subject contains no sensitive data.

## Inputs and evidence

The complete `subject` object is serialized for inspection. `context` and
separate evidence objects are not used by this deterministic pattern check.

## Execution

The script performs case-insensitive regular-expression searches over the
serialized subject. It counts matched pattern classes but does not copy matched
values into facts or findings and has no side effects.

## Output and verdicts

It returns `fail` with a single `secret-detected` finding when any pattern class
matches; the finding contains no secret value. Otherwise it returns `pass`.
`facts.matched_patterns` contains only the number of matching patterns.

## Failure and boundaries

Pattern matching can produce false positives and false negatives, and it does
not replace source-specific redaction or access control. Callers must avoid
placing raw credentials in requests or logs even when this verifier is enabled.
