---
id: bensz.validate-md-ref.checking
version: 1.0.0
kind: skill
description: Link facts are being collected and normalized by the selected verifier.
aliases: validate-md-ref.checking
entry_conditions: bensz.validate-md-ref.input-ready
invariants: source-read-only, verifier-result-recorded
transitions: bensz.validate-md-ref.reported
---

# Checking

Run the configured input adapter or `bensz.document.markdown-link-integrity`
verifier. Preserve the normalized result and any Gate decision in the Skill log
before proceeding.
