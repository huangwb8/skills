---
id: bensz.workspace.closed
version: 1.0.0
kind: system
description: This Skill's use of the task workspace is closed and may only be read for audit or resume.
aliases: workspace.closed
transitions: []
---

# Skill workspace use closed

This Skill must not write new intermediate artifacts after closure. Other Skills
sharing the task root may continue independently; existing files remain available
for audit and explicit continuation.
