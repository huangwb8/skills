---
id: bensz.prompt-programming.published
version: 1.0.0
kind: skill
description: The reviewed Prompt Program is ready to be returned to the user.
entry_conditions: bensz.prompt-programming.reviewed
invariants: output-contract-preserved, source-unchanged
transitions: bensz.workspace.closed
---

# Published

Return the validated Prompt Program without mutating the original prompt or
silently introducing another output artifact.
