---
description: Required work and delivery have completed successfully.
---

# Completed

This terminal state cannot transition further.

## Entry conditions

Required work, validation, delivery evidence, and any declared completion Gate
have passed the applicable contract.

## Agent actions

Present the accepted result and its delivery location. Do not silently create a
second result or rewrite the completion evidence.

## Exit criteria

The final delivery has been accepted and the completion evidence is immutable.

## Completion record

The event log and delivery report must remain available for audit.

## Transition guidance

There are no next states. A correction after completion is a new run or attempt,
not an implicit transition out of this terminal state.

## Boundaries

The Kernel owns the terminal transition and replay semantics; the Agent and
Skill own the content of the delivered result.
