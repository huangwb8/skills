---
id: bensz.document.readme-pair-alignment
version: 1.0.0
description: Deterministically checks structural and machine-token alignment of README.md and README_EN.md.
entrypoint: scripts/verify.py
tags: markdown, bilingual, readme, deterministic
aliases: document.readme-pair
assurance_tier: deterministic
mode: rule
---

# README pair alignment

The request `subject` must contain `zh_path` and `en_path`, each pointing to
an authorized README artifact. The verifier reuses the Skill's deterministic
checker and checks heading levels/order, balanced fences, relative link/image
targets, and command/environment/version token drift.

Structural errors return `fail`. Token drift is returned as `uncertain` with a
warning because equivalent prose and factual correctness require AI or human
review. The verifier never treats an unavailable file or malformed request as
a passing result.
