---
id: validate-md-ref.input-ready
version: 1.0.0
kind: skill
description: A readable Markdown input was selected for this validation run.
entry_conditions: workspace.ready
invariants: input.read-only, no-secrets-in-workspace
transitions: validate-md-ref.checking
entrypoint: scripts/check_input.py
---

# Input ready

The Agent selected one existing Markdown input and will only read it. The helper
requires `context.document` to point to a readable `.md` file; it does not copy
the document into the task workspace.
