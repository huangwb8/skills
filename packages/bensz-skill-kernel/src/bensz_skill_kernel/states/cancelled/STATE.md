---
description: Execution was intentionally cancelled.
---

# Cancelled

This terminal state cannot transition further.

## Entry conditions

The task was intentionally stopped by the authorized Agent, user, or operator
before successful completion.

## Agent actions

Record the cancellation reason without discarding already-created evidence or
claiming that the requested work was delivered.

## Evidence and exit criteria

The cancellation event and prior work evidence remain available for audit. The
current run is complete without a successful delivery.

## Transition guidance

There are no next states. Any later continuation is a new explicitly authorized
run or attempt and must preserve this cancellation history.

## Boundaries

The Kernel prevents further lifecycle transitions; the Agent/Skill controls the
user-facing explanation and cleanup permitted by the task contract.
