---
description: Required verification and evidence checks are running.
transitions: bensz.runtime.active, bensz.runtime.waiting, bensz.runtime.delivering, bensz.runtime.failed, bensz.runtime.cancelled
---

# Checking

Verification results and Gate decisions are recorded as events.

## Entry conditions

A stable work result or intermediate artifact is available for the required
validation and its evidence references are known.

## Agent actions

Run every required Verifier declared by the Skill, perform any instruction-only
or semantic review assigned to the Agent, and record normalized results and the
Kernel-computed Gate. Preserve uncertainty and execution failures instead of
turning them into a pass.

## Evidence

Record the required verification results, their Gate, and all evidence
references in the current run's event log.

## Exit criteria

Before leaving, the current run must have the required verification results and
their Gate in the event log. A successful validation path has an allowing Gate;
an unresolved or uncertain result requires waiting or review, and a required
failure follows the failure branch.

## Transition guidance

Use `delivering` after the required checks and Gate allow continuation, `active`
for a correction/retry, `waiting` for external or human review, `failed` for an
unrecoverable required failure, and `cancelled` for intentional cancellation.
The frontmatter `transitions` list is authoritative.

## Failure, recovery and boundaries

The Kernel enforces only its registered invariants and result protocol. The
Agent/Adapter owns domain-specific interpretation; every result must retain its
Verifier identity, version, execution status, verdict, and evidence references.
