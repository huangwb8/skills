---
id: bensz.write-readme.reported
version: 1.0.0
aliases: write-readme.reported
description: The aligned README pair and its verification summary have been delivered.
entry_conditions: bensz.write-readme.delivery-ready
transitions: bensz.workspace.closed
---

# Reported

Present the two authorized README paths and the sanitized delivery summary.
This state does not authorize rewriting completion evidence.

## Recovery

Any correction after reporting starts a new `run_id`/`attempt_id`; it must not
mutate the historical event or snapshot in place.
