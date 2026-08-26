---
id: validate-md-ref.checking
version: 1.0.0
kind: skill
description: Link facts are being collected and normalized by the selected verifier.
entry_conditions: validate-md-ref.input-ready
invariants: source-read-only, verifier-result-recorded
transitions: validate-md-ref.reported
---

# Checking

Run the configured input adapter or `markdown.link-integrity` verifier. Preserve
the normalized result and any Gate decision in the Skill log before proceeding.
