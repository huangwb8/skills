---
id: bensz.write-readme.delivery-ready
version: 1.0.0
aliases: write-readme.delivery-ready
description: Required checks, evidence references, uncertainty disclosures, and delivery metadata are complete.
entry_conditions: bensz.write-readme.bilingual-draft-ready
invariants: verifier-result-recorded, verifier-gate-allow, required-verifiers-pass
transitions: bensz.write-readme.reported
---

# Delivery ready

This is the fail-closed handoff barrier. Required Verifier results and the
Kernel Gate must cover the current `run_id`/`attempt_id`; an uncertain,
unchecked, timed-out, missing, or version-mismatched result cannot be silently
treated as a pass.

## Exit criteria

Only after the Gate allows delivery may the agent present `README.md`,
`README_EN.md`, their hashes, the selected template, executed commands, and
remaining uncertainties.
