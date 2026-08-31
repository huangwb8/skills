---
description: This Skill's use of the task workspace is closed and may only be read for audit or resume.
transitions: []
---

# Skill workspace use closed

This Skill must not write new intermediate artifacts after closure. Other Skills
sharing the task root may continue independently; existing files remain available
for audit and explicit continuation.

## Entry conditions

This Skill has completed, failed, or intentionally stopped its work, and its
remaining workspace material is sufficient for audit or an explicitly authorized
resume.

## Agent actions

Perform read-only audit or report the final workspace status. Do not append new
Skill artifacts, replace snapshots, or treat an audit read as a new execution.

## Evidence and exit criteria

The closed snapshot, event history, and any final report remain available for
audit. This Skill has no further in-place work to complete.

## Completion and transition guidance

This is a terminal state with no successor. A later continuation must open a new
explicit run or attempt under the applicable workspace policy; it must not mutate
the closed history in place.

## Boundaries

The Kernel enforces the terminal edge and workspace snapshot integrity. Other
Skills sharing the task root remain governed by their own states and boundaries.
