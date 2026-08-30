---
id: bensz.prompt-programming.reviewed
version: 1.0.0
kind: skill
description: The Prompt Program passed the required conformance Gate and semantic review.
entry_conditions: bensz.prompt-programming.schema-valid
invariants: verifier-gate-allow, core-intent-preserved
transitions: bensz.prompt-programming.published
---

# Reviewed

Proceed only when the required Gate allows. Confirm compression retained the
core intent, hard constraints, output contract and explicit sequence.
