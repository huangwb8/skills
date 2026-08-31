---
description: Execution stopped because a required operation or check failed.
---

# Failed

This terminal state preserves failure evidence for recovery or audit.

## Entry conditions

A required operation, validation, or delivery check cannot safely complete.

## Agent actions

Preserve the structured failure reason, affected operation, relevant artifacts,
and evidence references. Explain whether the failure is retryable without
silently claiming that the task succeeded.

## Evidence and exit criteria

Failure evidence is sufficient when the reason, affected operation, and
available recovery context can be reconstructed from the event log. This state
is terminal for the current run.

## Transition guidance

There are no next states. Recovery starts a new run or attempt under the Skill's
retry policy and must not rewrite this terminal event history.

## Boundaries

The Kernel records the terminal lifecycle state; the Agent/Skill supplies the
domain diagnosis and any user-facing recovery instructions.
