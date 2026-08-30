---
id: bensz.prompt-programming.schema-valid
version: 1.0.0
kind: skill
description: The Prompt Program has the required structural blocks and atom mapping.
entry_conditions: bensz.prompt-programming.draft
invariants: verifier-result-recorded
transitions: bensz.prompt-programming.reviewed, bensz.runtime.failed
---

# Schema valid

Render the six semantic atoms in configured order, then run
`bensz.prompt.contract-conformance@1.0.0`. Record its result and Gate for the
same run identity.
