---
id: bensz.write-readme.facts-collected
version: 1.0.0
aliases: write-readme.facts-collected
description: Project facts are inventoried with provenance and uncertainty labels.
entry_conditions: bensz.write-readme.input-ready
transitions: bensz.write-readme.bilingual-draft-ready, bensz.write-readme.input-ready, bensz.runtime.waiting, bensz.runtime.failed
---

# Facts collected

Read public project metadata, entrypoints, tests, examples, configuration, and
licenses. Separate verified facts, user-provided facts, inferences, and open
questions. Every material claim keeps a relative source reference and content
hash; never fill a gap by guessing.

## Exit criteria

Proceed only when enough facts exist to choose one primary template and write a
minimal Quick Start. Conflicts or missing authorization return to input review
or `waiting`.
