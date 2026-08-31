---
description: The logical task root is locked and Skill-scoped directories are available.
transitions: [bensz.workspace.closed, "*"]
---

# Workspace ready

The runtime has selected one immutable `.bensz-api/task-*` root for this logical
task. Skills must resolve `input`, `output`, and `log` through the workspace API.
The project source and formal deliverables remain outside this intermediate root.

## Entry conditions

The task root is uniquely selected, its manifest is readable, and the shared and
Skill-scoped directory boundaries are available.

## Agent actions

Inspect the workspace manifest, select the Skill's declared initial state, and
place only intermediate inputs, outputs, and logs in the permitted directories.
Keep source files and formal deliverables at their project-defined paths.

## Evidence

Record the Skill scope, input references, and required directory boundaries.

## Exit criteria

The workspace is ready when those boundaries are known. A Skill may enter its
declared initial state or close the workspace when no work will be performed.

## Transition guidance

The explicit `workspace-closed` edge and the supported `*` strategy in the
frontmatter are authoritative. A wildcard transition is valid only when the
destination declares this state as an entry condition.

## Failure, recovery and boundaries

Do not create a second task root for the same logical task. The Kernel and
Workspace API enforce path and snapshot boundaries; the Agent selects the Skill
workflow and must keep sensitive material out of the workspace log.
