---
id: bensz.prompt.contract-conformance
version: 1.0.0
description: Checks that a Prompt Program contains the required non-empty blocks in configured order.
classification: atomic
assurance_tier: deterministic
tags: prompt,structure,deterministic
aliases: prompt-programming.contract-conformance
entrypoint: scripts/verify.py
---

# Prompt Program conformance

This verifier checks only the structural contract of the rendered Prompt
Program. It does not judge whether the source prompt's intent is correct,
whether domain facts are true, or whether a human would prefer the style.

## Evidence contract

- `subject.program` (required): the candidate Prompt Program as a UTF-8 string.
- `context.required_blocks` (optional): non-empty block labels to require; when
  omitted, the configured minimum is `目标`, `输入`, `输出`, `流程`, `校验`, `返回`.
- `context.control_required` (optional): when true, require at least one
  conditional/iteration marker in the `流程` block.
- `evidence` and `evidence_refs` are carried through for audit only; the
  verifier does not treat them as proof of semantic equivalence.

## Result contract

Return `pass` only when every required block occurs exactly once, has non-empty
content, and follows the canonical order. Return `fail` with structured
findings for missing, duplicate, empty or out-of-order blocks, or for a missing
required control marker. Oversized, malformed or non-object requests are
errors at the JSON-stdio boundary and must not be guessed by callers.
