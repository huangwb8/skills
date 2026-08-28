---
description: The logical task root is locked and Skill-scoped directories are available.
transitions: [bensz.workspace.closed, "*"]
---

# Workspace ready

The runtime has selected one immutable `.bensz-api/task-*` root for this logical
task. Skills must resolve `input`, `output`, and `log` through the workspace API.
The project source and formal deliverables remain outside this intermediate root.
