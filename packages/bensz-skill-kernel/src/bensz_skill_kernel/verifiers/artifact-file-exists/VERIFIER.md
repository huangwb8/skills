# Artifact file exists

## Verification target

Confirm that `subject.path` currently identifies a regular file. A passing result
does not validate the file's contents, readability, ownership, or suitability for
any later operation.

## Inputs and evidence

`subject.path` is required and is interpreted as a filesystem path. This verifier
does not require separate evidence objects and does not infer a path from context.

## Execution

The script performs a read-only `Path.is_file()` check. It does not open, modify,
create, or delete the target.

## Output and verdicts

It returns `pass` with `facts.path` and `facts.exists: true` when the target is a
regular file. A missing path, nonexistent target, or non-file target returns
`fail` with a `missing-file` finding and `facts.exists: false`.

## Failure and boundaries

This check reflects the filesystem at execution time and provides no guarantee
that the file will still exist later. Path authorization and containment are
separate checks; use a path-scope verifier when those properties are required.
