---
id: workspace.ready
version: 1.0.0
kind: system
description: The logical task root is locked and Skill-scoped directories are available.
transitions: workspace.closed
---

# Workspace ready

The runtime has selected one immutable `.bensz-api/task-*` root for this logical
task. Skills must resolve `input`, `output`, and `log` through the workspace API.
The project source and formal deliverables remain outside this intermediate root.
