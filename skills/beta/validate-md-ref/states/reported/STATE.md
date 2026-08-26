---
id: validate-md-ref.reported
version: 1.0.0
kind: skill
description: The validation result and its uncertainty were reported to the user.
entry_conditions: validate-md-ref.checking
invariants: result-standardized, uncertainty-disclosed
transitions: workspace.closed
---

# Reported

Present the standardized result without treating a link-reachability fact as a
semantic citation conclusion. Keep the original Markdown unchanged.
