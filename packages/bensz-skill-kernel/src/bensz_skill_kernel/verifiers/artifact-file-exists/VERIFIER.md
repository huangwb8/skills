---
id: bensz.artifact.file-existence
version: 1.0.0
description: Confirm that a requested local artifact exists as a regular file.
entrypoint: scripts/verify.py
tags: common, filesystem, deterministic
aliases: artifact.file-exists
---

# Artifact file exists

The request subject must contain `path`. The verifier performs a read-only
filesystem check and emits `pass` when the path is a regular file.
