---
description: A task has been accepted but has not started execution.
transitions: bensz.runtime.active, bensz.runtime.waiting, bensz.runtime.cancelled
---

# Planned

The task contract is known and execution has not begun.

## Entry conditions

The task has been accepted and the workspace is available. Required inputs,
scope, and any authorization needed to start must be identifiable.

## Agent actions

Read the task contract, confirm the input and output boundaries, and prepare the
minimum execution context. Do not perform the substantive Skill work or create
the formal deliverable while remaining in this state.

## Evidence

Record the input references and the accepted task scope. Enter `active` only
when the execution context is ready.

## Exit criteria

Enter `waiting` when input, authorization, approval, or another dependency is
missing; enter `cancelled` only when the task is intentionally abandoned.

## Transition guidance

The machine-readable `transitions` field is authoritative. The Agent must not
request a target outside that list. This state has no direct failure edge;
unresolved preparation problems remain waiting or are explicitly cancelled.

## Failure, recovery and boundaries

The Kernel checks the transition graph and persists the state. The Agent owns
task interpretation and preparation; domain-specific planning belongs to the
Skill that owns the task.
