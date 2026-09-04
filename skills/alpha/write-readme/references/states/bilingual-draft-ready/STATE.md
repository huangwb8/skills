---
id: bensz.write-readme.bilingual-draft-ready
version: 1.0.0
aliases: write-readme.bilingual-draft-ready
description: Chinese and English README artifacts exist and are ready for required checks.
entry_conditions: bensz.write-readme.facts-collected
transitions: bensz.write-readme.delivery-ready, bensz.write-readme.facts-collected, bensz.runtime.waiting, bensz.runtime.failed
---

# Bilingual draft ready

Write the Chinese README first, then produce natural English with equivalent
facts and structure. Keep commands, paths, URLs, versions, code fences, and
relative targets synchronized. The project source remains untouched.

## Exit criteria

Both authorized artifacts exist and the delivery report can identify their
hashes. Structural or factual corrections stay in this state; fact changes
return to `facts-collected`.
