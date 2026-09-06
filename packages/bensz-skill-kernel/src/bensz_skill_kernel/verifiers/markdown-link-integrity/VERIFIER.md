# Markdown link integrity

## Verification target

Confirm that links extracted from a Markdown file resolve as local anchors, local
files, or observable HTTP(S) targets. A pass covers structural resolution and
reachability only; it does not establish that a linked source is authoritative or
supports the surrounding claim.

## Inputs and evidence

`subject.path` is required and must identify the Markdown file. Optional context
keys are `timeout`, `blacklist`, and `whitelist`; they control remote probing and
host restrictions. The file content is read directly and summarized with a hash;
no separate evidence objects are required.

## Execution

The script extracts standard Markdown links and HTML anchor tags. It resolves
same-document anchors and relative files within the Markdown file's directory,
checks linked-document fragments, and probes allowed HTTP(S) URLs with bounded
redirects. Local, loopback, private, blocked, or non-whitelisted network targets
are skipped rather than contacted.

## Output and verdicts

The result places the collection report in `facts` and emits
`invalid-reference` findings for deterministically invalid targets. It returns
`fail` when any target is invalid, `pass` when no target is invalid or unresolved,
`timed_out` when every unresolved target timed out, and `unchecked` when one or
more remote targets remain unobservable without a deterministic invalid result.
Skipped targets are counted in `facts` but do not by themselves prevent `pass`.

## Failure and boundaries

A missing path returns `fail`; file-reading or collector exceptions return
`error`. Skipped targets and transient DNS or connection failures are not treated
as proof that a link is invalid. Network access is restricted to permitted public
HTTP(S) targets, and the verifier does not judge citation identity, entailment,
content quality, or future availability.
