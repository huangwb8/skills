---
id: bensz.prompt-programming.reviewed
version: 1.0.0
kind: skill
description: The Prompt Program passed the required conformance Gate and semantic review.
entry_conditions: bensz.prompt-programming.schema-valid
invariants: verifier-gate-allow, required-verifiers-pass, core-intent-preserved
transitions: bensz.prompt-programming.published
---

# Reviewed

Proceed only when the required structural and AI semantic Verifiers both return
`completed + pass` and the Kernel-computed Gate allows. Confirm the semantic
review retained core intent, hard constraints, output contract and explicit
sequence; preserve findings and anchors for audit.
