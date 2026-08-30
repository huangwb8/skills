---
id: bensz.prompt-programming.draft
version: 1.0.0
kind: skill
description: A source prompt and its intended output contract are captured as a draft.
entry_conditions: bensz.workspace.ready
invariants: input.read-only, no-secrets-in-workspace
transitions: bensz.prompt-programming.schema-valid, bensz.runtime.failed
---

# Draft

Select the original prompt without mutating it. Keep its intent, explicit format,
sequence constraints and domain terms available for translation.
