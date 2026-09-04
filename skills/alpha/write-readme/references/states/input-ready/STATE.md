---
id: bensz.write-readme.input-ready
version: 1.0.0
aliases: write-readme.input-ready
description: The README goal, audience, authorization scope, and output names are resolved.
entry_conditions: bensz.workspace.ready
transitions: bensz.write-readme.facts-collected, bensz.runtime.waiting, bensz.runtime.failed
---

# Input ready

Confirm the project path, writing goal, audience, authorized outputs, and the
two README filenames before reading project facts. Do not write a README yet.

## Evidence and exit criteria

Keep only sanitized relative references and the authorization summary. Enter
`facts-collected` when the declared inputs are readable; use `waiting` when
authorization or an external dependency is missing.
