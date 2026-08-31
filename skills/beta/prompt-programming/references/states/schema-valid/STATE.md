---
id: bensz.prompt-programming.schema-valid
version: 1.0.0
kind: skill
description: The Prompt Program has the required structural blocks and atom mapping.
entry_conditions: bensz.prompt-programming.draft
invariants: verifier-result-recorded, required-verifiers-pass
transitions: bensz.prompt-programming.reviewed, bensz.runtime.failed
---

# Schema valid

Render the six semantic atoms in configured order, then run both required
verifiers: `bensz.prompt.contract-conformance@1.0.0` and the AI rubric
`bensz.prompt.semantic-equivalence@1.0.0`. Record both results as one batch and
let the Kernel recompute the Gate for the same run identity.
