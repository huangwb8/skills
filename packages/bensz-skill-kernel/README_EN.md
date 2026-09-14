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

Expected: the first command prints the current package version; the second lists built-in Verifiers. To install a published release, use `python3 -m pip install bensz-skill-kernel` instead. Version and dependencies are defined by `pyproject.toml`.

## Declarative State/Verifier sub-agent collaboration

The Kernel owns State, Verifier, evidence, and Gate contracts; it does not implement cross-Harness agent creation, parallelism, waiting, or cleanup. A Skill that needs collaboration should reference the [conditional collaboration template](../../docs/templates/state-verifier-agent-coordination.md) and describe its trigger phase, inputs, independence, output schema, and fallback in `SKILL.md`.

- `config.yaml` may declare intent such as `mode`, `count`, and `rounds` for the LLM and Harness to interpret and report; these fields are not Kernel scheduling APIs.
- The default Verifier recommendation is two independent sub-agents checking the same snapshot in parallel; serial review should be declared only when needed.
- Codex, Claude Code, or another Harness chooses how to create and isolate sub-agents; Skills must not assume platform APIs, host IDs, or sandbox parameters.
- Results still return through the existing Verifier/Gate contract; missing, uncertain, or failed evidence must not be represented as a pass.

## Python support and dependencies

- Minimum Python version: 3.11; verified on 3.11, 3.12, and 3.13; 3.12 is recommended.
- Runtime uses PyYAML (to read a Skill's `config.yaml`) and otherwise only the Python standard library.
- A new Python version enters the support range after it passes the test matrix.

New and modified Skills declare only that they depend on BSK. Before execution, the Bensz-managed runtime updates BSK to the latest production release; individual Skills do not select a minimum, exact version, or capability gate:

```yaml
runtime:
  kernel:
    name: bensz-skill-kernel
```

The Kernel still reads legacy `runtime.kernel.version` and `required_capabilities` fields for migration compatibility, but they are not templates for new declarations. Production CLI calls use `~/.bensz-skills/bin/bsk`; `install-bensz-skills --force-runtime-update` performs the latest-version check and update.

## Directory-based Contract Packs

State and Verifier both use directory Packs made of a Markdown contract, index metadata, and zero or more components. `contract_packs.py` builds on discovery and JSON-stdio boundaries from `packs.py` to orchestrate `script`, `agent`, and `human` components, binding contract/plan/component hashes, evidence, dependency order, `run_id`/`state_visit_id`/`attempt_id`, and executor identity. The shared execution layer does not conflate State transition semantics with Verifier verdict/Gate semantics.

Canonical IDs, versions, and alias migrations are documented in [`docs/verifier-id-naming.md`](../../docs/verifier-id-naming.md) and [`docs/state-id-naming.md`](../../docs/state-id-naming.md).

## State: stages and transitions

`states/index.json` is the State catalog; each state directory contains a `STATE.md` and may include a JSON-stdio helper. Built-in lifecycle states are `planned`, `active`, `waiting`, `checking`, `delivering`, `completed`, `failed`, and `cancelled`; `workspace-ready` and `workspace-closed` are workspace system states. Domain Skill stages remain in each Skill's `references/states/`.

A State Pack's modular boundary is the individual state directory: `states/<state>/` or a Skill-owned `references/states/<state>/` holds that state's semantic contract, script helpers, agent/human components, and evidence requirements. The built-in `states/` directory deliberately stays flat; differences such as `runtime`, `workspace`, and domain states are expressed through the canonical ID, `kind`, `classification`, and `tags` instead of extra subdirectories.

BSK hosts only infrastructure reused across states: Pack discovery, ID/alias validation, contract loading and hashing, component execution boundaries, generic transition legality, events and snapshots, resource limits, error normalization, and secret redaction. Adding a normal State should be done by adding a state directory, updating `index.json`, or declaring it in the target Skill's `config.yaml.runtime`; only capabilities genuinely reused across multiple States/Skills belong in Kernel system code. The lifecycle reducer in `runtime.py` is the stable-projection exception: changing its states or transitions must stay consistent with the built-in State Pack contracts.

```bash
bsk state list
bsk state describe bensz.workspace.ready
bsk state list --root path/to/skill/states
```

`--root` overlays Skill states on built-ins. A Skill declares its initial state, allowed states, state roots, and Verifier subset in root `config.yaml.runtime`; the legacy `state-machine.json` is read-only compatible. Required components must all complete and pass before a state condition can hold.

A new Skill that requires strong identity adds `identity_policy: state-identity-v2` to the same runtime declaration. This policy tightens new writes only: a first transition without `run_id`, without an explicit initial attempt, or with the legacy `default` attempt is rejected with a stable `reason_code` before the first event. Legacy v1 logs remain readable and replayable but cannot be upgraded in place by a strict Skill.

Initialize the task workspace and Skill declaration before checking or persisting a transition:

```bash
bsk workspace init . --description citation-review
bsk state check bensz.workspace.ready org.example.skill.collecting --skill-root path/to/skill
bsk state transition .bensz-api/task-YYYYMMDD-HHMM-citation-review skill-name org.example.skill.collecting \
  --skill-root path/to/skill --run-id run-1 --target-attempt-id collecting-1 \
  --context-json '{"input":"report.md"}'
```

The new identity protocol separates `run_id` (the whole run), `state_visit_id` (one entry into a State), and `attempt_id` (one verification attempt inside that visit). A transition validates the current State with `source_identity` and atomically creates `target_identity`; the CLI returns the target identity for the next stage. Use `bsk attempt start` for a retry inside the same State. Once the new attempt is active, old Gates, handoffs, and authorizations cannot satisfy the current window. See the [identity protocol](../../docs/state-identity-protocol.md) for the state graph, stable reason codes, and legacy rules.

```bash
bsk capabilities
bsk diagnostics
bsk attempt start .bensz-api/task-YYYYMMDD-HHMM-citation-review skill-name \
  --run-id run-1 --state-visit-id STATE_VISIT_ID --attempt-id collecting-2 \
  --reason retry --idempotency-key collecting-2
```

New State operations return `bensz-meta-state-v2` JSON. Legacy `bensz-meta-state-v1`/`bensz-event-v1` logs remain read-only and replayable, are marked as legacy, and do not acquire v2 completion eligibility by inference. Skill metadata state is written to `log/meta-state.json`; task `events.ndjson`/`state.json` remain a separate lifecycle/evidence layer. A successful transition appends a `state.transition` (`state_domain: skill`) event, and `bsk rebuild` projects the State, visit, and active attempt while checking the stable-field hash.

The kernel executes only protocol-defined invariants. The current `verifier-result-recorded` invariant requires both `verification.result` and `verification.gate` before leaving the state. V2 events must belong to the active `run_id/state_visit_id/attempt_id` and occur after the current attempt window begins, so a passing result from an earlier stage or superseded attempt cannot be reused. Otherwise the transition returns `rejected` without writing a new snapshot. Domain invariants remain the responsibility of a Skill helper or human review.

## Action: in-state authorization

A State transition guards only a transition submitted to the Kernel; it cannot automatically intercept a host that writes a file or invokes business logic around the Kernel. A Skill host that protects an in-state action should call the generic preflight first, obtain a single-use capability bound to the current State snapshot and version, `run_id/attempt_id`, handoff, and evidence window, then atomically consume it immediately before the action:

```bash
bsk action preflight .bensz-api/task-YYYYMMDD-HHMM-demo/log/events.ndjson \
  demo-skill publish-report --state org.example.workflow.ready --state-version 1.0.0 \
  --run-id run-1 --state-visit-id visit-1 --attempt-id attempt-1 --idempotency-key authorize-publish

bsk action consume .bensz-api/task-YYYYMMDD-HHMM-demo/log/events.ndjson \
  action-auth-... demo-skill publish-report --run-id run-1 --state-visit-id visit-1 --attempt-id attempt-1 \
  --idempotency-key consume-publish
```

Python callers use `EventLog.preflight_action()` and `EventLog.consume_action_authorization()`. V2 preflight accepts only the active run/visit/attempt bound to the current State snapshot. An optional `handoff_id` must come from the current attempt window. Re-entering the State or superseding the attempt expires prior grants, and each grant can be consumed once. `expected_last_seq` rejects a concurrent observation conflict. Rejections are also appended as `action.authorization.denied` events with stable reason codes and recovery advice. `status/rebuild` only projects existing events; it never fabricates an authorization or business action.

The protocol identifier is `bensz-action-authorization-v1` (public constant `ACTION_AUTHORIZATION_PROTOCOL`). Preflight rejection codes include `concurrent_event_conflict`, `skill_state_unavailable`, `state_mismatch`, `state_version_mismatch`, `state_snapshot_unbound`, `state_identity_mismatch`, `handoff_outside_state_window`, `handoff_outside_attempt_window`, and `evidence_outside_handoff`. Consumption codes include `authorization_not_found`, `authorization_already_consumed`, `authorization_expired`, `authorization_binding_mismatch`, and the concurrent-conflict code. Callers should branch on the reason code and follow `recovery`, not parse prose messages.

The Skill/host contract still defines action names and which actions are protected. The Kernel neither knows domain fields nor scans project files. A host that never invokes preflight cannot be stopped by the Kernel itself; this capability is an auditable protocol guard, not an operating-system permission sandbox. An idempotency key remains bound to its first result, so a recovered retry uses a new action attempt/key.

## Verifier: evidence and Gates

`verifiers/index.json` is the single source of truth for the Verifier catalog and execution plans. Every Pack has a `VERIFIER.md` and optional components. Script components receive one JSON request on stdin and emit one result JSON on stdout; `verdict` supports `pass`, `fail`, `uncertain`, `unchecked`, `error`, `timed_out`, and `skipped`. The kernel normalizes timeouts, exceptions, invalid JSON, and result fields.

Verifier Packs use the same modular boundary as State Packs: built-in `verifiers/<verifier>/` or Skill-owned `references/verifiers/<verifier>/` directories contain the contract, scripts, and verifier-specific evidence interpretation. BSK discovers Packs from their index and does not duplicate IDs or directories in a central registry; adding a normal Verifier does not require a Kernel dispatch change.

New or modified `VERIFIER.md` files follow the lightweight skeleton in [`docs/templates/verifier-body.md`](../../docs/templates/verifier-body.md): verification target, inputs and evidence, execution, output and verdicts, then failure and boundaries. Indexed Packs do not duplicate machine metadata in the body; package tests enforce the section order and non-empty content for every built-in contract.

```bash
bsk verifier list --tag citation
bsk verifier describe bensz.evidence.citation-truth-fit --version 1.0.0
bsk verifier run bensz.document.markdown-link-integrity --input README.md
bsk verifier list --skill-root path/to/skill
bsk verifier run org.example.contract.check --skill-root path/to/skill \
  --request-json '{"subject":{"data":{"id":1}},"context":{"schema":{"required":["id"]}}}'
```

`--root` explicitly overlays one or more Verifier collections. `--skill-root` loads Packs from `config.yaml.runtime.verifier_roots` (default: `references/verifiers`) and exposes only the IDs and versions selected by `runtime.verifiers`. The options are mutually exclusive and never scan global directories. `run` keeps the file-oriented `--input` compatibility form and also accepts a complete `--request-json` or `--request-file`; non-file Verifiers should use a complete request so their subject/context/evidence contract is not omitted. `run_id` and `attempt_id` from a JSON request are preserved unless explicitly overridden by CLI options.

Built-in examples cover file existence, Markdown link integrity, citation truth/fit, and `bensz.design.minimum-sufficient-complexity` (reviewing whether complexity is justified by a current goal, constraint, or risk); legacy IDs remain resolvable as aliases. The citation and design-complexity Verifiers are explicitly `agent` components and stay `unchecked`/`wait` until a bound result arrives. Legacy single-entry Packs, compatibility directories without `index.json`, and instruction-only states remain discoverable but report missing explicit component metadata. Atomic Packs also cover contract conformance, path scope, Schema, diff scope, secret redaction, evidence provenance, event integrity, state transition, and task completeness; domain rules stay out of the Kernel.

For an audit run, add `--events EVENTS --run-id RUN_ID` to receive unified `results`, `gate`, and compatibility `verification` fields. A required Skill Verifier rejects on failure and waits or enters manual review while unresolved; a non-passing advisory Verifier produces warnings only. Verifier-level and component-level Gates are merged conservatively by severity: advisory status affects only that Verifier's components and cannot hide another required Verifier's binding error or missing result. Agent/human handoffs are returned at the top level but contract text and raw context are not written to the ledger. Python API `trusted=False` is the process-level fail-closed option for an untrusted Pack; it is not a `bsk verifier run` CLI flag. The CLI executes only built-in Packs or roots explicitly selected with `--root`/`--skill-root`.

## Workspace: immutable task boundaries

Initialize one immutable BenszAPI workspace for each logical task; Skills should not construct paths themselves:

```bash
bsk workspace init . --description citation-review
bsk workspace path .bensz-api/task-YYYYMMDD-HHMM-citation-review validate-md-ref input
bsk workspace status .bensz-api/task-YYYYMMDD-HHMM-citation-review
```

Initialization creates `bensz.workspace.ready` (legacy alias: `workspace.ready`) and `shared/input|output|log` boundaries. The workspace manifest, lifecycle event ledger, and Skill metadata snapshot are separate and replayable.

A strict-v2 Skill can initialize the workspace, immutable runtime snapshot, and first State identity through one entry point. The command accepts only a new task root. An explicit task root is created exclusively, while concurrent automatic naming atomically selects suffixes such as `-a` and `-b`. If any step fails, the command removes the newly created root only while its ownership token still matches:

```bash
bsk workspace initialize . skill-name org.example.skill.collecting \
  --skill-root path/to/skill --run-id run-1 --attempt-id collecting-1 \
  --description citation-review
```

The run snapshot stores Skill/Kernel versions, the identity policy, State contracts, Verifier Markdown contracts/component plans/helper asset hashes, plus a minimal Python fingerprint without the interpreter's absolute path. Once written, the snapshot cannot be overwritten; reads recompute and validate its payload, hash, and derived ID. State events, projections, and action authorizations reference the same snapshot ID/hash; contract drift or a run mismatch requires a new workspace/task root. `bsk diagnostics` separately reports the CLI's actual interpreter path, Python version, and Kernel version so callers can detect split Python environments.

## Runtime boundaries and audit

Pack helpers run as trusted local processes by default. The kernel limits input, stdout/stderr size, environment variables, and execution time, and terminates the full process group on timeout. Passing `trusted=False` for an untrusted Pack fails closed; this is a process-level resource boundary, not a container or OS sandbox. stdio subprocesses set `PYTHONDONTWRITEBYTECODE=1` by default so no `__pycache__` is written into Pack directories; an explicit `PYTHONPYCACHEPREFIX` is still passed through so caches can be archived elsewhere.

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
