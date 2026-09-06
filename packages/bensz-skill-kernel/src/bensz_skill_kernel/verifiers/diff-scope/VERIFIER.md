# Diff scope

## Verification target

Confirm that every path reported in `subject.changed_paths` is explicitly listed
in `context.allowed_paths`. A pass means the submitted path set has no unexpected
member; it does not prove that the submitted diff inventory is complete.

## Inputs and evidence

`subject.changed_paths` supplies the changed-path collection and
`context.allowed_paths` supplies the exact allowlist. Both default to empty
collections. No filesystem scan or separate evidence object is performed.

## Execution

The deterministic script converts both collections to sets and computes changed
paths that are absent from the allowlist. Comparison is exact and does not expand
globs, normalize paths, resolve symlinks, or inspect file contents.

## Output and verdicts

It returns `pass` when the difference is empty. Otherwise it returns `fail`, puts
the sorted changed paths and violations in `facts`, and emits an
`unexpected-change` finding for every out-of-scope path.

## Failure and boundaries

Empty `changed_paths` passes, so the caller must obtain that inventory from a
trusted diff source. Use the path-scope verifier for filesystem containment and a
separate review when the semantic contents of a change matter.
