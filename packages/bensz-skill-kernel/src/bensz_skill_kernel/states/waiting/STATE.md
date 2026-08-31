---
description: Execution is paused pending input, authorization, approval or another dependency.
transitions: bensz.runtime.active, bensz.runtime.cancelled, bensz.runtime.failed
---

# Waiting

The reason is recorded in the orthogonal `wait_reason` field.

## Entry conditions

Progress cannot safely continue because an input, authorization, approval,
dependency, quota, schedule, or operator decision is unavailable.

## Agent actions

Record a concise, non-sensitive `wait_reason` and the dependency that must be
resolved. Ask for missing user input or approval when appropriate; do not repeat
the blocked operation or claim completion while waiting.

## Evidence

Keep the blocked request, prior results, and any pending decision reference
available for resume.

## Exit criteria

Return to `active` only after the dependency is resolved and the execution
context has been rechecked.

## Transition guidance

Use `active` after recovery, `cancelled` when the task is intentionally stopped,
and `failed` when the dependency has become an unrecoverable failure. The
`wait_reason` must explain why the selected branch is safe.

## Failure, recovery and boundaries

Waiting is not a pass result and does not authorize side effects. The Kernel
validates the reason enum and transition edge; the Agent or operator owns the
conversation or dependency resolution.
