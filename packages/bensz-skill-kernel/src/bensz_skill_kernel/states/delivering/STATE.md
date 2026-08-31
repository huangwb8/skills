---
description: The validated result is being prepared for delivery.
transitions: bensz.runtime.active, bensz.runtime.waiting, bensz.runtime.checking, bensz.runtime.completed, bensz.runtime.failed, bensz.runtime.cancelled
---

# Delivering

Delivery reports and final completion checks are pending.

## Entry conditions

Required validation has completed and the result is eligible for delivery under
the Skill's Gate and output contract.

## Agent actions

Assemble the declared final artifacts and delivery report. Recheck filenames,
paths, content hashes, recipients, and any user-visible uncertainty. Keep
formal deliverables outside the intermediate task workspace when the contract
requires it.

## Evidence

The delivery report must identify the final result, its artifacts, and the
validation evidence.

## Exit criteria

Enter `completed` only after the completion contract and final checks pass;
return to `checking` when validation must be repeated.

## Transition guidance

Use `active` for a substantive correction, `checking` for a new or repeated
verification, `waiting` for a delivery dependency or approval, `failed` for an
unrecoverable delivery error, `cancelled` for intentional cancellation, and
`completed` only for an accepted final delivery.

## Failure, recovery and boundaries

Do not overwrite an existing formal deliverable without authorization. The
Kernel checks lifecycle completion evidence; the Agent owns presentation and
the Skill owns the domain delivery format.
