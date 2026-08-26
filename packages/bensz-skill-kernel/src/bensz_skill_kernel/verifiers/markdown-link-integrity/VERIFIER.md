---
id: markdown.link-integrity
version: 1.0.0
description: Validate Markdown links and local anchors for reachability and safety.
entrypoint: scripts/verify.py
tags: common, markdown, links, deterministic
---

# Markdown link integrity

Use this verifier for a Markdown file when link extraction, local anchor
resolution, and HTTP(S) reachability are required. The entrypoint accepts the
standard JSON request on stdin and returns one JSON result object on stdout.

The request subject must contain `path`. Optional `context` keys are
`timeout`, `blacklist`, and `whitelist`.
