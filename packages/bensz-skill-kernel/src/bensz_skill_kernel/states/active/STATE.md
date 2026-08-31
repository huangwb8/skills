---
description: A task is actively executing its Skill work.
transitions: bensz.runtime.active, bensz.runtime.waiting, bensz.runtime.checking, bensz.runtime.cancelled, bensz.runtime.failed
---

# Active

Skill work is in progress; domain phases remain orthogonal.

## Entry conditions

The task contract and execution context are ready, and the workspace remains
available for the declared Skill scope.

## Agent actions

Execute the Skill's substantive work, using only the declared inputs and tools.
Record material phase changes, artifacts, and evidence references in the task
workspace or event log according to the Skill contract.

## Evidence

Record material phase changes, artifacts, and evidence references.

## Exit criteria

The work is ready to be checked only when the expected intermediate artifacts
and evidence references have been produced. Move to `checking` for validation;
move to `waiting` when an external dependency or decision blocks progress.

## Transition guidance

Remain `active` while work continues. Use `checking` when a stable result is
ready for verification, `failed` when a required operation cannot succeed,
`cancelled` for intentional cancellation, and `waiting` for a recoverable
blocker. The allowed targets are exactly those in `transitions`.

## Failure, recovery and boundaries

Preserve the failing operation, affected paths, and evidence references before
leaving this state. The Kernel enforces lifecycle edges; the Skill and Agent
decide the domain operation and its recovery strategy.
