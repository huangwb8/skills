# bensz-skill-kernel

Lightweight lifecycle kernel for Agent Skill states, workspaces, and Verifier execution.

[中文](README.md) · English: `README_EN.md`

## Who it is for

- **Skill users**: discover states, Verifiers, and workspace boundaries with `bsk`.
- **Skill/Pack authors**: declare `config.yaml.runtime`, State/Verifier Contract Packs, and JSON-stdio components.
- **Kernel developers**: maintain replayable event ledgers, Gates, evidence, and safety boundaries.

## Quick Start

Python 3.11+ is required. From the repository root:

```bash
# Install the current package in an isolated environment
python3 -m venv .bensz-api/.venv
.bensz-api/.venv/bin/python -m pip install -e packages/bensz-skill-kernel

# Confirm the CLI and built-in Packs are discoverable
.bensz-api/.venv/bin/bsk --version
.bensz-api/.venv/bin/bsk verifier list
```

Expected: the first command prints `0.14.1`; the second lists built-in Verifiers. To install a published release, use `python3 -m pip install bensz-skill-kernel` instead. Version and dependencies are defined by `pyproject.toml`.

## Python support and dependencies

- Minimum Python version: 3.11; verified on 3.11, 3.12, and 3.13; 3.12 is recommended.
- Runtime uses PyYAML (to read a Skill's `config.yaml`) and otherwise only the Python standard library.
- A new Python version enters the support range after it passes the test matrix.

## Directory-based Contract Packs

State and Verifier both use directory Packs made of a Markdown contract, index metadata, and zero or more components. `contract_packs.py` builds on discovery and JSON-stdio boundaries from `packs.py` to orchestrate `script`, `agent`, and `human` components, binding contract/plan/component hashes, evidence, dependency order, `run_id`/`attempt_id`, and executor identity. The shared execution layer does not conflate State transition semantics with Verifier verdict/Gate semantics.

Canonical IDs, versions, and alias migrations are documented in [`docs/verifier-id-naming.md`](../../docs/verifier-id-naming.md) and [`docs/state-id-naming.md`](../../docs/state-id-naming.md).

## State: stages and transitions

`states/index.json` is the State catalog; each state directory contains a `STATE.md` and may include a JSON-stdio helper. Built-in lifecycle states are `planned`, `active`, `waiting`, `checking`, `delivering`, `completed`, `failed`, and `cancelled`; `workspace-ready` and `workspace-closed` are workspace system states. Domain Skill stages remain in each Skill's `references/states/`.

```bash
bsk state list
bsk state describe bensz.workspace.ready
bsk state list --root path/to/skill/states
```

`--root` overlays Skill states on built-ins. A Skill declares its initial state, allowed states, state roots, and Verifier subset in root `config.yaml.runtime`; the legacy `state-machine.json` is read-only compatible. Required components must all complete and pass before a state condition can hold.

Initialize the task workspace and Skill declaration before checking or persisting a transition:

```bash
bsk workspace init . --description citation-review
bsk state check bensz.workspace.ready org.example.skill.collecting --skill-root path/to/skill
bsk state transition .bensz-api/task-YYYYMMDD-HHMM-citation-review skill-name org.example.skill.collecting \
  --skill-root path/to/skill --context-json '{"input":"report.md"}'
```

State operations return `bensz-meta-state-v1` JSON with the operation, state, result, optional helper receipt, and snapshot. Skill metadata state is written to `log/meta-state.json`; task `events.ndjson`/`state.json` remain a separate lifecycle/evidence layer. A successful transition appends a `state.transition` (`state_domain: skill`) event; `bsk rebuild` projects it to `skill_states`/`skill_state_transitions` and checks the stable-field hash. A missing snapshot can be recovered from events; hash drift returns structured `integrity_error`.

The kernel executes only protocol-defined invariants. The current `verifier-result-recorded` invariant requires both `verification.result` and `verification.gate` before leaving the state; otherwise it returns `rejected` without writing a new snapshot. Domain invariants remain the responsibility of a Skill helper or human review. When run identity is present, `run_id` and `attempt_id` must be supplied together.

## Verifier: evidence and Gates

`verifiers/index.json` is the single source of truth for the Verifier catalog and execution plans. Every Pack has a `VERIFIER.md` and optional components. Script components receive one JSON request on stdin and emit one result JSON on stdout; `verdict` supports `pass`, `fail`, `uncertain`, `unchecked`, `error`, `timed_out`, and `skipped`. The kernel normalizes timeouts, exceptions, invalid JSON, and result fields.

```bash
bsk verifier list --tag citation
bsk verifier describe bensz.evidence.citation-truth-fit --version 1.0.0
bsk verifier run bensz.document.markdown-link-integrity --input README.md
```

Built-in examples cover file existence, Markdown link integrity, and citation truth/fit; legacy IDs remain resolvable as aliases. The citation Verifier is explicitly an `agent` component and stays `unchecked`/`wait` until a bound result arrives. Legacy single-entry Packs, compatibility directories without `index.json`, and instruction-only states remain discoverable but report missing explicit component metadata. Atomic Packs also cover contract conformance, path scope, Schema, diff scope, secret redaction, evidence provenance, event integrity, state transition, and task completeness; domain rules stay out of the Kernel.

For an audit run, add `--events EVENTS --run-id RUN_ID` to receive unified `results`, `gate`, and compatibility `verification` fields. Agent/human handoffs are returned at the top level but contract text and raw context are not written to the ledger. Python API `trusted=False` is the process-level fail-closed option for an untrusted Pack; it is not a `bsk verifier run` CLI flag.

## Workspace: immutable task boundaries

Initialize one immutable BenszAPI workspace for each logical task; Skills should not construct paths themselves:

```bash
bsk workspace init . --description citation-review
bsk workspace path .bensz-api/task-YYYYMMDD-HHMM-citation-review validate-md-ref input
bsk workspace status .bensz-api/task-YYYYMMDD-HHMM-citation-review
```

Initialization creates `bensz.workspace.ready` (legacy alias: `workspace.ready`) and `shared/input|output|log` boundaries. The workspace manifest, lifecycle event ledger, and Skill metadata snapshot are separate and replayable.

## Runtime boundaries and audit

Pack helpers run as trusted local processes by default. The kernel limits input, stdout/stderr size, environment variables, and execution time, and terminates the full process group on timeout. Passing `trusted=False` for an untrusted Pack fails closed; this is a process-level resource boundary, not a container or OS sandbox.

The append-only ledger retains optional contract snapshots, authorization chains, and execution audit trails. `reduce_events()` performs offline projection replay and never calls a model or tool. `verification-v2` rechecks component uniqueness, hashes, evidence references, run identity, executor/model, and human confirmation at recording and completion gates; a caller-reported aggregate pass cannot override a required failure or missing run. `summarize_metrics()` also reports component binding and executor identity coverage.

## Development, testing, and release

```bash
# Package tests (requires pytest)
python3 -m pytest packages/bensz-skill-kernel/tests

# Build and check release artifacts; no upload by default
python3 tests/publish_bsk_pypi.py
# Upload to PyPI only with explicit authorization
python3 tests/publish_bsk_pypi.py --upload
```

The publishing helper writes build artifacts to `tmp/bsk-pypi/` and does not read, copy, or log PyPI credentials. For the full API, State/Verifier contracts, and change history, see the repository `docs/`, source code, and `CHANGELOG.md`.

## License

This package is licensed under the MIT License; see [`LICENSE`](LICENSE).
