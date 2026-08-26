---
id: workspace.closed
version: 1.0.0
kind: system
description: The task workspace is closed and may only be read for audit or resume.
transitions: []
---

# Workspace closed

No new intermediate artifacts should be written after closure. Existing files
remain available for audit and explicit continuation.
