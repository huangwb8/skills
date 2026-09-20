"""Public ``bsk`` command line interface.

The CLI is intentionally domain-neutral.  Skills collect their own facts and
use these small commands to append lifecycle, evidence, verification and
delivery events without reimplementing the kernel protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import uuid
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .runtime import EventLog, IntegrityError, KernelError
from .identity import STRICT_IDENTITY_POLICY, STATE_IDENTITY_PROTOCOL, kernel_capabilities, kernel_diagnostics, normalize_state_identity
from .states import META_STATE_PROTOCOL_VERSION, SkillStateDeclaration, StateMachine, build_state_registry, check_state_invariants, execute_state, state_requires_gate_binding
from .workspace import TaskWorkspace, WORKSPACE_KINDS, state_snapshot_hash
from .verifiers import GateDecision, SkillVerifierDeclaration, apply_gate, build_verifier_registry, normalize_result, summarize_metrics
from . import __version__


def _json_value(raw: str, *, label: str) -> Any:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON: {exc.msg}") from exc
    return value


def _json_object(raw: str, *, label: str) -> dict[str, Any]:
    value = _json_value(raw, label=label)
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a JSON object")
    return dict(value)


def _read_json_file(path: str, *, label: str) -> dict[str, Any]:
    content = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    return _json_object(content, label=label)


def _read_json_value(path: str | None, inline: str | None, *, label: str) -> Any:
    if path and inline:
        raise ValueError(f"{label} cannot use both file and inline JSON")
    if path:
        content = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
        return _json_value(content, label=label)
    if inline is not None:
        return _json_value(inline, label=label)
    raise ValueError(f"{label} is required")


def _contract(args: argparse.Namespace) -> dict[str, Any] | None:
    path = getattr(args, "contract_file", None)
    if not path:
        return None
    return _read_json_file(path, label="contract file")


def _log(args: argparse.Namespace) -> EventLog:
    return EventLog(args.events, contract=_contract(args))


def _add_contract(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--contract-file", help="JSON completion contract")


def _add_event_context(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--actor", default="runtime")
    parser.add_argument("--scope", default="task")
    parser.add_argument("--attempt-id", default="default")


def _add_verifier_source(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", action="append", default=[], help="additional Verifier Pack collection root; repeatable")
    parser.add_argument("--skill-root", help="Skill root containing runtime.verifiers and optional verifier_roots")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bsk",
        description="Bensz Skill lifecycle and verification kernel",
        epilog="Skills normally use subcommands; legacy --status/--rebuild/--append-event remain supported.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")

    commands.add_parser("capabilities", help="show supported Kernel protocols and operations")
    commands.add_parser("diagnostics", help="show the active Python and Kernel protocol environment")

    status = commands.add_parser("status", help="show the current projection")
    status.add_argument("events", metavar="EVENTS")

    rebuild = commands.add_parser("rebuild", help="rebuild state.json from events.ndjson")
    rebuild.add_argument("events", metavar="EVENTS")
    rebuild.add_argument("--state-file", help="optional output state path")

    append = commands.add_parser("append", help="append a generic event")
    append.add_argument("events", metavar="EVENTS")
    append.add_argument("event_type", metavar="TYPE")
    append.add_argument("--payload", default="{}", help="event payload as JSON")
    append.add_argument("--payload-file", help="read payload JSON from a file, or - for stdin")
    append.add_argument("--summary", default="")
    append.add_argument("--path")
    append.add_argument("--evidence-ref", action="append", default=[])
    append.add_argument("--idempotency-key")
    append.add_argument("--run-id", help="optional run identity for a bound audit event")
    append.add_argument("--state-visit-id", help="optional active State visit identity")
    _add_event_context(append)
    _add_contract(append)

    transition = commands.add_parser("transition", help="move the lifecycle state")
    transition.add_argument("events", metavar="EVENTS")
    transition.add_argument("to", choices=("planned", "active", "waiting", "checking", "delivering", "completed", "failed", "cancelled"))
    transition.add_argument("--wait-reason", choices=("input", "authorization", "approval", "choice", "dependency", "quota", "children", "schedule", "operator_pause"))
    transition.add_argument("--phase")
    _add_event_context(transition)
    _add_contract(transition)

    artifact = commands.add_parser("artifact", help="register an artifact")
    artifact.add_argument("events", metavar="EVENTS")
    artifact.add_argument("artifact_id", metavar="ARTIFACT_ID")
    artifact.add_argument("--required", action="store_true")
    artifact.add_argument("--metadata", default="{}")
    _add_contract(artifact)

    validation = commands.add_parser("validation", help="record a validation result")
    validation.add_argument("events", metavar="EVENTS")
    validation.add_argument("verdict", choices=("pass", "passed", "success", "fail", "failed", "uncertain", "unchecked"))
    validation.add_argument("--evidence-ref", action="append", default=[])
    validation.add_argument("--metadata", default="{}")
    _add_contract(validation)

    verification = commands.add_parser("verification", help="record verifier result and optional gate")
    verification.add_argument("events", metavar="EVENTS")
    verification.add_argument("--result-file", help="JSON result object/list file, or - for stdin")
    verification.add_argument("--result-json", help="JSON result object/list")
    verification.add_argument("--gate-file", help="JSON gate file; omit when no gate is available")
    verification.add_argument("--gate-json", help="JSON gate object")
    _add_event_context(verification)
    verification.add_argument("--idempotency-key")
    verification.add_argument("--run-id")
    verification.add_argument("--state-visit-id")
    _add_contract(verification)

    delivery = commands.add_parser("delivery", help="record a delivery report")
    delivery.add_argument("events", metavar="EVENTS")
    delivery.add_argument("report", metavar="REPORT")
    delivery.add_argument("--metadata", default="{}")
    _add_contract(delivery)

    action = commands.add_parser("action", help="authorize and consume protected Skill actions")
    action_commands = action.add_subparsers(dest="action_command", metavar="ACTION")
    action_preflight = action_commands.add_parser("preflight", help="authorize one action in the current Skill state")
    action_preflight.add_argument("events", metavar="EVENTS")
    action_preflight.add_argument("skill")
    action_preflight.add_argument("action")
    action_preflight.add_argument("--state", required=True)
    action_preflight.add_argument("--state-version", required=True)
    action_preflight.add_argument("--run-id", required=True)
    action_preflight.add_argument("--attempt-id", required=True)
    action_preflight.add_argument("--state-visit-id")
    action_preflight.add_argument("--handoff-id")
    action_preflight.add_argument("--evidence-ref", action="append", default=[])
    action_preflight.add_argument("--idempotency-key")
    action_preflight.add_argument("--expected-last-seq", type=int)
    action_consume = action_commands.add_parser("consume", help="consume a current action authorization once")
    action_consume.add_argument("events", metavar="EVENTS")
    action_consume.add_argument("authorization_id")
    action_consume.add_argument("skill")
    action_consume.add_argument("action")
    action_consume.add_argument("--run-id", required=True)
    action_consume.add_argument("--attempt-id", required=True)
    action_consume.add_argument("--state-visit-id")
    action_consume.add_argument("--idempotency-key")
    action_consume.add_argument("--expected-last-seq", type=int)

    verifier = commands.add_parser("verifier", help="discover and run built-in verifier packs")
    verifier_commands = verifier.add_subparsers(dest="verifier_command", metavar="ACTION")
    verifier_list = verifier_commands.add_parser("list", help="list available verifier ids")
    verifier_list.add_argument("--tag")
    _add_verifier_source(verifier_list)
    verifier_describe = verifier_commands.add_parser("describe", help="show one verifier contract")
    verifier_describe.add_argument("verifier_id")
    verifier_describe.add_argument("--version")
    _add_verifier_source(verifier_describe)
    verifier_run = verifier_commands.add_parser("run", help="run a selected verifier")
    verifier_run.add_argument("verifier_id")
    verifier_run.add_argument("--version")
    verifier_input = verifier_run.add_mutually_exclusive_group(required=True)
    verifier_input.add_argument("--input", help="legacy file subject path")
    verifier_input.add_argument("--request-json", help="complete Verifier request JSON object")
    verifier_input.add_argument("--request-file", help="complete Verifier request JSON file, or - for stdin")
    verifier_run.add_argument("--timeout", type=int, default=10)
    verifier_run.add_argument("--blacklist", action="append", default=[])
    verifier_run.add_argument("--whitelist", action="append", default=[])
    verifier_run.add_argument("--events", help="append verifier results and Gate to an event log")
    verifier_run.add_argument("--run-id")
    verifier_run.add_argument("--attempt-id", help="attempt identity; defaults to request JSON value or 'default'")
    verifier_run.add_argument("--state-visit-id", help="active State visit identity")
    verifier_run.add_argument("--actor", default="bsk:verifier")
    verifier_run.add_argument("--scope", default="skill")
    verifier_run.add_argument("--idempotency-key")
    _add_verifier_source(verifier_run)

    state = commands.add_parser("state", help="inspect declarative meta-state definitions")
    state_commands = state.add_subparsers(dest="state_command", metavar="ACTION")
    state_list = state_commands.add_parser("list", help="list available states")
    _add_state_source(state_list)
    state_list.add_argument("--kind")
    state_describe = state_commands.add_parser("describe", help="show one state definition")
    state_describe.add_argument("state_id")
    _add_state_source(state_describe)
    state_check = state_commands.add_parser("check", help="check whether a meta-state transition is allowed")
    state_check.add_argument("current_state")
    state_check.add_argument("target_state")
    _add_state_source(state_check)
    state_execute = state_commands.add_parser("execute", help="run one state helper without changing a workspace snapshot")
    state_execute.add_argument("state_id")
    state_execute.add_argument("--context-json", default="{}", help="JSON object passed to the state helper")
    state_execute.add_argument("--timeout", type=int, default=10)
    _add_state_source(state_execute)
    state_transition = state_commands.add_parser("transition", help="run a state helper and persist an allowed Skill transition")
    state_transition.add_argument("task_root")
    state_transition.add_argument("skill")
    state_transition.add_argument("target_state")
    state_transition.add_argument("--context-json", default="{}", help="JSON object passed to the state helper")
    state_transition.add_argument("--run-id", help="run identity used when checking event-bound invariants")
    state_transition.add_argument("--attempt-id", default="default", help="attempt identity used when checking event-bound invariants")
    state_transition.add_argument("--state-visit-id", help="source State visit identity used when checking invariants")
    state_transition.add_argument("--target-state-visit-id", help="target State visit identity; generated when target attempt is supplied")
    state_transition.add_argument("--target-attempt-id", help="initial attempt identity for the target State visit")
    state_transition.add_argument("--gate-event-id", help="allowing source Gate event consumed by this transition")
    state_transition.add_argument("--evidence-hash", help="sha256 digest bound by the source Gate")
    state_transition.add_argument("--evidence-ref", action="append", default=[], help="canonical evidence reference bound by the source Gate; repeatable")
    state_transition.add_argument("--idempotency-key", help="stable key for replaying the same transition request")
    state_transition.add_argument("--timeout", type=int, default=10)
    _add_state_source(state_transition)

    attempt = commands.add_parser("attempt", help="start or supersede an attempt in the active State visit")
    attempt_commands = attempt.add_subparsers(dest="attempt_command", metavar="ACTION")
    attempt_start = attempt_commands.add_parser("start", help="start a new attempt and supersede the active attempt")
    attempt_start.add_argument("task_root")
    attempt_start.add_argument("skill")
    attempt_start.add_argument("--run-id", required=True)
    attempt_start.add_argument("--state-visit-id", required=True)
    attempt_start.add_argument("--attempt-id", required=True)
    attempt_start.add_argument("--reason", required=True)
    attempt_start.add_argument("--idempotency-key", required=True)
    attempt_start.add_argument("--expected-last-seq", type=int)

    workspace = commands.add_parser("workspace", help="initialize and resolve BenszAPI task workspaces")
    workspace_commands = workspace.add_subparsers(dest="workspace_command", metavar="ACTION")
    workspace_init = workspace_commands.add_parser("init", help="create or reopen a task workspace")
    workspace_init.add_argument("project_root", nargs="?", default=".")
    workspace_init.add_argument("--task-root")
    workspace_init.add_argument("--description", default="task")
    workspace_initialize = workspace_commands.add_parser(
        "initialize",
        help="atomically create a workspace, bind a run snapshot, and enter the first v2 Skill State",
    )
    workspace_initialize.add_argument("project_root", nargs="?", default=".")
    workspace_initialize.add_argument("skill")
    workspace_initialize.add_argument("target_state")
    workspace_initialize.add_argument("--task-root")
    workspace_initialize.add_argument("--description", default="task")
    workspace_initialize.add_argument("--skill-root", required=True)
    workspace_initialize.add_argument("--run-id", required=True)
    workspace_initialize.add_argument("--attempt-id", required=True)
    workspace_initialize.add_argument("--state-visit-id")
    workspace_initialize.add_argument("--idempotency-key")
    workspace_initialize.add_argument("--context-json", default="{}")
    workspace_initialize.add_argument("--timeout", type=int, default=10)
    workspace_path = workspace_commands.add_parser("path", help="resolve a Skill-scoped workspace directory")
    workspace_path.add_argument("task_root")
    workspace_path.add_argument("skill")
    workspace_path.add_argument("kind", choices=tuple(sorted(WORKSPACE_KINDS)))
    workspace_status = workspace_commands.add_parser("status", help="show workspace manifest and boundaries")
    workspace_status.add_argument("task_root")
    return parser


def _legacy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bsk", description="Bensz Skill lifecycle kernel")
    parser.add_argument("--status", metavar="EVENTS")
    parser.add_argument("--rebuild", metavar="EVENTS")
    parser.add_argument("--append-event", metavar="EVENTS")
    parser.add_argument("--type", dest="event_type")
    parser.add_argument("--payload", default="{}")
    parser.add_argument("--summary", default="")
    return parser


def _print(value: Any, *, pretty: bool = False) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2 if pretty else None))


def _spec_dict(spec: Any) -> dict[str, Any]:
    return {
        "verifier_id": spec.verifier_id,
        "version": spec.version,
        "mode": spec.mode,
        "tags": list(spec.tags),
        "capabilities": list(spec.capabilities),
        "evidence_requirements": list(spec.evidence_requirements),
        "uncertainty_policy": dict(spec.uncertainty_policy),
        "aliases": list(getattr(spec, "aliases", ())),
        "subject_kinds": list(getattr(spec, "subject_kinds", ())),
        "prompt_pack_ref": getattr(spec, "prompt_pack_ref", None),
        "rule_pack_ref": getattr(spec, "rule_pack_ref", None),
        "calibration_set_ref": getattr(spec, "calibration_set_ref", None),
        "classification": getattr(spec, "classification", "domain"),
        "assurance_tier": getattr(spec, "assurance_tier", "deterministic"),
        "metadata": dict(spec.metadata),
    }


def _verifier_registry(args: argparse.Namespace):
    skill_root = getattr(args, "skill_root", None)
    roots = getattr(args, "root", ())
    if skill_root and roots:
        raise ValueError("--skill-root and --root cannot be combined")
    if skill_root:
        declaration = SkillVerifierDeclaration.from_skill_root(skill_root)
        return declaration.registry(), declaration
    return build_verifier_registry(*roots), None


def _declared_verifier_requirement(declaration: SkillVerifierDeclaration | None, verifier_id: str, version: str) -> Mapping[str, Any] | None:
    if declaration is None:
        return None
    for item in declaration.verifier_requirements():
        if item["id"] == verifier_id and item["version"] == version:
            return item
    raise ValueError(f"verifier is not declared by the Skill runtime: {verifier_id}@{version}")


def _add_state_source(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", action="append", default=[], help="additional directory containing STATE.md packages; repeatable")
    parser.add_argument("--skill-root", help="Skill root containing config.yaml runtime declaration (state-machine.json is legacy-compatible)")


def _state_registry(args: argparse.Namespace):
    roots = tuple(getattr(args, "root", ()) or ())
    skill_root = getattr(args, "skill_root", None)
    if roots and skill_root:
        raise ValueError("--root and --skill-root cannot be combined")
    if skill_root:
        declaration = SkillStateDeclaration.from_skill_root(skill_root)
        return declaration.registry(), declaration
    return build_state_registry(*roots), None


def _state_response(operation: str, status: str, *, current_state: str | None = None, target_state: str | None = None, definition: Any = None, execution: Any = None, snapshot: Any = None, reason: str | None = None, reason_code: str | None = None, source_identity: Mapping[str, Any] | None = None, target_identity: Mapping[str, Any] | None = None, identity_mode: str | None = None, downgrade_policy: str | None = None, warnings: list[str] | None = None, gate_binding: Mapping[str, Any] | None = None) -> dict[str, Any]:
    output: dict[str, Any] = {
        "protocol": META_STATE_PROTOCOL_VERSION,
        "operation": operation,
        "status": status,
        "current_state": current_state,
        "target_state": target_state,
    }
    if definition is not None:
        output["state"] = definition.to_dict()
    if execution is not None:
        output["execution"] = execution.to_dict()
    if snapshot is not None:
        output["snapshot"] = snapshot
    if reason:
        output["reason"] = reason
    if reason_code:
        output["reason_code"] = reason_code
    if source_identity is not None:
        output["source_identity"] = dict(source_identity)
    if target_identity is not None:
        output["target_identity"] = dict(target_identity)
    if identity_mode is not None:
        output["identity_mode"] = identity_mode
    if downgrade_policy is not None:
        output["downgrade_policy"] = downgrade_policy
    if warnings:
        output["warnings"] = list(warnings)
    if gate_binding is not None:
        output["gate_binding"] = dict(gate_binding)
    return output


def _contract_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _runtime_snapshot_inputs(declaration: SkillStateDeclaration) -> dict[str, Any]:
    registry = declaration.registry()
    definitions = [registry.resolve(state_id) for state_id in declaration.states]
    state_versions = {item.id: item.version for item in definitions}
    state_hashes = {
        item.id: _contract_hash(Path(item.source))
        for item in definitions
        if item.source and Path(item.source).is_file()
    }
    verifier_versions = {
        str(item["id"]): str(item["version"])
        for item in declaration.verifier_requirements()
    }
    verifier_hashes: dict[str, Any] = {}
    if declaration.verifier_requirements():
        verifier_registry = SkillVerifierDeclaration.from_skill_root(declaration.skill_root).registry()
        for requirement in declaration.verifier_requirements():
            verifier_id = str(requirement["id"])
            version = str(requirement["version"])
            pack = verifier_registry.resolve(verifier_id, version).contract_pack()
            verifier_hashes[verifier_id] = {
                "contract_hash": pack.contract_hash,
                "plan_hash": pack.plan_hash,
                "component_hashes": {
                    component.id: component.component_hash
                    for component in pack.components
                },
                "component_asset_hashes": {
                    component.id: _contract_hash(pack.root / component.entrypoint)
                    for component in pack.components
                    if component.entrypoint and (pack.root / component.entrypoint).is_file()
                },
            }
    return {
        "skill_id": str(declaration.skill_id or declaration.skill_root.name),
        "skill_version": declaration.skill_version,
        "identity_policy": declaration.identity_policy,
        "runtime_config": {
            "initial_state": declaration.initial_state,
            "states": list(declaration.states),
            "identity_policy": declaration.identity_policy,
            "declaration_hash": _contract_hash(declaration.source),
        },
        "state_versions": state_versions,
        "state_contract_hashes": state_hashes,
        "verifier_versions": verifier_versions,
        "verifier_contract_hashes": verifier_hashes,
    }


def _require_declared_state(registry: Any, declaration: SkillStateDeclaration | None, state_id: str) -> None:
    if not declaration:
        return
    definition = registry.resolve(state_id)
    declared = {
        registry.resolve(item).id
        for item in (*declaration.states, declaration.initial_state)
    }
    if definition.id not in declared and definition.kind != "system":
        raise ValueError(f"state {state_id!r} is not declared by {declaration.source}")


def _run_state_command(args: argparse.Namespace) -> int:
    registry, declaration = _state_registry(args)
    if args.state_command == "list":
        states = registry.definitions(kind=args.kind)
        if declaration:
            allowed = {
                registry.resolve(item).id
                for item in (*declaration.states, declaration.initial_state)
            }
            states = tuple(item for item in states if item.id in allowed or item.kind == "system")
        _print({"states": [item.to_dict() for item in states], "declaration": declaration.to_dict() if declaration else None}, pretty=True)
    elif args.state_command == "describe":
        _require_declared_state(registry, declaration, args.state_id)
        _print(registry.resolve(args.state_id).to_dict(), pretty=True)
    elif args.state_command == "check":
        _require_declared_state(registry, declaration, args.current_state)
        _require_declared_state(registry, declaration, args.target_state)
        machine = StateMachine(registry, args.current_state)
        current = registry.resolve(args.current_state).id
        target = registry.resolve(args.target_state)
        if machine.can_transition(args.target_state):
            _print(_state_response("check", "allowed", current_state=current, target_state=target.id, definition=target), pretty=True)
        else:
            _print(_state_response("check", "rejected", current_state=current, target_state=target.id, definition=target, reason="The target is not an allowed transition from the current state."), pretty=True)
    elif args.state_command == "execute":
        _require_declared_state(registry, declaration, args.state_id)
        definition = registry.resolve(args.state_id)
        context = _json_object(args.context_json, label="--context-json")
        execution = execute_state(definition, {"operation": "execute", "context": context}, timeout=args.timeout)
        _print(_state_response("execute", "completed", target_state=definition.id, definition=definition, execution=execution), pretty=True)
    elif args.state_command == "transition":
        _require_declared_state(registry, declaration, args.target_state)
        workspace = TaskWorkspace.open_existing(args.task_root)
        previous = workspace.read_meta_state(args.skill)
        persisted_current = str(previous.get("current_state", "bensz.workspace.ready"))
        _require_declared_state(registry, declaration, persisted_current)
        current = registry.resolve(persisted_current).id
        machine = StateMachine(registry, current)
        target = registry.resolve(args.target_state)
        strict_identity = bool(declaration and declaration.identity_policy == STRICT_IDENTITY_POLICY)
        previous_is_v2 = previous.get("identity_protocol") == STATE_IDENTITY_PROTOCOL
        requested_v2 = previous_is_v2 or args.target_attempt_id is not None or args.target_state_visit_id is not None
        identity_mode = "strict-v2" if strict_identity else ("v2" if requested_v2 else "legacy")
        downgrade_policy = "forbid" if strict_identity else ("forbid-after-v2" if requested_v2 else "warn")

        def reject_identity(reason_code: str, reason: str) -> int:
            _print(_state_response(
                "transition",
                "rejected",
                current_state=current,
                target_state=target.id,
                definition=target,
                snapshot=previous,
                reason=reason,
                reason_code=reason_code,
                identity_mode=identity_mode,
                downgrade_policy=downgrade_policy,
            ), pretty=True)
            return 2

        if strict_identity:
            if not args.run_id:
                return reject_identity("strict_identity_required", "A strict-v2 Skill requires a non-empty run_id.")
            if args.target_attempt_id is None:
                return reject_identity("initial_attempt_required", "A strict-v2 Skill requires an explicit target attempt.")
            if args.target_attempt_id == "default":
                return reject_identity("default_attempt_forbidden", "The legacy 'default' attempt is forbidden in strict-v2 mode.")
            if not previous_is_v2 and current != declaration.initial_state:
                return reject_identity("legacy_snapshot_not_upgradable", "A legacy State snapshot cannot be upgraded in place; create a new workspace/task root.")
        events = EventLog(workspace.events).read()
        if args.idempotency_key:
            existing = next((item for item in events if item.idempotency_key == args.idempotency_key), None)
            if existing is not None:
                existing_source = existing.payload.get("source_identity")
                existing_target = existing.payload.get("target_identity")
                requested_target_attempt = args.target_attempt_id or args.attempt_id
                requested_target_visit = args.target_state_visit_id
                if existing_target is not None and requested_target_visit is None:
                    seed = {
                        "skill": args.skill,
                        "source": existing_source,
                        "target_state": target.id,
                        "target_attempt_id": requested_target_attempt,
                    }
                    requested_target_visit = "state-visit-" + hashlib.sha256(
                        json.dumps(seed, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    ).hexdigest()[:24]
                requested_target_matches = (
                    existing.payload.get("to_state") == target.id
                    and existing.payload.get("skill") == args.skill
                    and existing.run_id == args.run_id
                    and (
                        existing_target is None
                        or (
                            existing_target.get("state_visit_id") == requested_target_visit
                            and existing_target.get("attempt_id") == requested_target_attempt
                        )
                    )
                    and (
                        (existing_source is None and args.state_visit_id is None)
                        or (
                            existing_source is not None
                            and existing_source.get("state_visit_id") == args.state_visit_id
                            and existing_source.get("attempt_id") == args.attempt_id
                        )
                    )
                    and existing.payload.get("gate_event_id") == args.gate_event_id
                    and existing.payload.get("evidence_hash") == args.evidence_hash
                    and tuple(existing.payload.get("evidence_refs", ())) == tuple(args.evidence_ref)
                )
                if existing.event_type != "state.transition" or not requested_target_matches:
                    raise ValueError(f"idempotency key conflict: {args.idempotency_key}")
                _print(_state_response(
                    "transition",
                    "transitioned",
                    current_state=existing.payload.get("from_state"),
                    target_state=target.id,
                    definition=target,
                    snapshot=previous,
                    source_identity=existing_source,
                    target_identity=existing_target,
                    identity_mode=identity_mode,
                    downgrade_policy=downgrade_policy,
                    warnings=["legacy_state_write"] if identity_mode == "legacy" else None,
                    gate_binding=EventLog(workspace.events).inspect_transition_binding(existing.event_id),
                ), pretty=True)
                return 0
        if not machine.can_transition(args.target_state):
            _print(_state_response("transition", "rejected", current_state=current, target_state=target.id, definition=target, snapshot=previous, reason="The target is not an allowed transition from the current state.", reason_code="transition_not_allowed"), pretty=True)
            return 0
        context = _json_object(args.context_json, label="--context-json")
        context = {**context, "skill": args.skill}
        if args.run_id is not None:
            context = {
                **context,
                "run_id": args.run_id,
                "state_visit_id": args.state_visit_id,
                "attempt_id": args.attempt_id,
            }
        source_identity = None
        if previous_is_v2:
            source_identity = normalize_state_identity(
                {
                    "run_id": args.run_id,
                    "state_visit_id": args.state_visit_id,
                    "attempt_id": args.attempt_id,
                },
                label="source identity",
            )
            expected_source = normalize_state_identity(
                {
                    "run_id": previous.get("run_id"),
                    "state_visit_id": previous.get("state_visit_id"),
                    "attempt_id": previous.get("active_attempt_id"),
                },
                label="snapshot identity",
            )
            if source_identity != expected_source:
                _print(_state_response(
                    "transition",
                    "rejected",
                    current_state=current,
                    target_state=target.id,
                    definition=target,
                    snapshot=previous,
                    reason="state_identity_mismatch: source identity is not the active State visit/attempt",
                    reason_code="state_identity_mismatch",
                    source_identity=source_identity,
                ), pretty=True)
                return 0
        binding_complete = bool(args.gate_event_id and args.evidence_hash and args.evidence_ref)
        binding_partial = any((args.gate_event_id, args.evidence_hash, args.evidence_ref)) and not binding_complete
        binding_required = bool(
            strict_identity
            and source_identity is not None
            and state_requires_gate_binding(registry.resolve(current))
        )
        if binding_partial or (binding_required and not binding_complete):
            reason_code = "gate_binding_incomplete" if binding_partial else "gate_binding_required"
            reason = (
                "gate_event_id, evidence_hash and at least one evidence_ref must be provided together."
                if binding_partial
                else "A strict-v2 protected transition must consume its source Gate and evidence binding."
            )
            _print(_state_response(
                "transition",
                "rejected",
                current_state=current,
                target_state=target.id,
                definition=target,
                snapshot=previous,
                reason=reason,
                reason_code=reason_code,
                source_identity=source_identity,
                identity_mode=identity_mode,
                downgrade_policy=downgrade_policy,
            ), pretty=True)
            return 2
        if binding_complete:
            EventLog(workspace.events).validate_transition_gate_binding(
                gate_event_id=args.gate_event_id,
                source_identity=source_identity or {},
                evidence_hash=args.evidence_hash,
                evidence_refs=args.evidence_ref,
            )
        v2_requested = strict_identity or requested_v2
        target_identity = None
        run_snapshot = None
        snapshot_inputs = None
        if v2_requested:
            if args.run_id is None:
                raise ValueError("--run-id is required for a v2 target State identity")
            target_attempt_id = args.target_attempt_id or args.attempt_id
            target_visit_id = args.target_state_visit_id
            if target_visit_id is None:
                seed = {
                    "skill": args.skill,
                    "source": source_identity,
                    "target_state": target.id,
                    "target_attempt_id": target_attempt_id,
                }
                target_visit_id = "state-visit-" + hashlib.sha256(
                    json.dumps(seed, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest()[:24]
            target_identity = normalize_state_identity(
                {
                    "run_id": args.run_id,
                    "state_visit_id": target_visit_id,
                    "attempt_id": target_attempt_id,
                },
                label="target identity",
            )
            if source_identity is not None and source_identity["run_id"] != target_identity["run_id"]:
                raise ValueError("source and target State identities must use the same run_id")
        if target_identity is not None and declaration is not None:
            snapshot_inputs = _runtime_snapshot_inputs(declaration)
            existing_run_snapshot = workspace.manifest().get("run_snapshot")
            if existing_run_snapshot:
                if existing_run_snapshot.get("run_id") != target_identity["run_id"]:
                    return reject_identity("run_snapshot_mismatch", "The workspace is already bound to another run snapshot; create a new workspace/task root.")
                for key in ("skill_id", "skill_version", "identity_policy", "runtime_config", "state_versions", "state_contract_hashes", "verifier_versions", "verifier_contract_hashes"):
                    if existing_run_snapshot.get(key) != snapshot_inputs.get(key):
                        return reject_identity("runtime_contract_drift", "The active Skill runtime differs from the bound run snapshot; create a new workspace/task root.")
                run_snapshot = existing_run_snapshot
        if declaration:
            context = {**context, "required_verifiers": list(declaration.verifier_requirements())}
        invariant_failures = check_state_invariants(registry.resolve(current), events, context=context)
        if invariant_failures:
            _print(_state_response(
                "transition",
                "rejected",
                current_state=current,
                target_state=target.id,
                definition=target,
                snapshot=previous,
                reason="State invariant failed: " + "; ".join(invariant_failures),
                reason_code="state_invariant_failed",
            ), pretty=True)
            return 0
        entry_context = {**context, **(target_identity or {})}
        execution = execute_state(target, {"operation": "enter", "task_root": str(workspace.task_root), "skill": args.skill, "current_state": current, "target_state": target.id, "context": entry_context}, timeout=args.timeout)
        if execution.execution_status != "not_applicable" and execution.verdict != "pass":
            _print(_state_response("transition", "rejected", current_state=current, target_state=target.id, definition=target, execution=execution, snapshot=previous, reason="The state helper did not pass, so the transition was not persisted.", reason_code="state_entry_helper_failed"), pretty=True)
            return 0
        machine.transition(args.target_state, events=events, context=context)
        if target_identity is not None and snapshot_inputs is not None and run_snapshot is None:
            run_snapshot = workspace.record_run_snapshot(run_id=target_identity["run_id"], **snapshot_inputs)["run_snapshot"]
        snapshot = {
            "protocol": META_STATE_PROTOCOL_VERSION if target_identity is not None else "bensz-meta-state-v1",
            "skill": workspace.paths(args.skill).skill,
            "current_state": target.id,
            "state_version": target.version,
            "workspace_state": workspace.manifest().get("state"),
            "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "last_operation": {
                "operation": "transition",
                "status": "transitioned",
                "current_state": current,
                "target_state": target.id,
                "execution_status": execution.execution_status,
                "verdict": execution.verdict,
            },
        }
        if target_identity is not None:
            snapshot.update({
                "identity_protocol": STATE_IDENTITY_PROTOCOL,
                "run_id": target_identity["run_id"],
                "state_visit_id": target_identity["state_visit_id"],
                "active_attempt_id": target_identity["attempt_id"],
                "legacy_identity": False,
            })
            if run_snapshot is not None:
                snapshot.update({
                    "run_snapshot_id": run_snapshot["snapshot_id"],
                    "run_snapshot_hash": run_snapshot["snapshot_hash"],
                })
        snapshot_hash = state_snapshot_hash(snapshot)
        # Stage a pending snapshot before appending the event.  The stable
        # event ID is preallocated so recovery can detect an interrupted
        # commit instead of silently accepting a split projection.
        state_event_id = str(uuid.uuid4())
        snapshot["state_event_id"] = state_event_id
        snapshot["snapshot_hash"] = snapshot_hash
        event_payload = {
            "state_domain": "skill",
            "skill": args.skill,
            "from_state": current,
            "to_state": target.id,
            "state_version": target.version,
            "snapshot_hash": snapshot_hash,
            "snapshot_path": f"{args.skill}/log/meta-state.json",
            "state_event_id": state_event_id,
        }
        if target_identity is not None:
            event_payload.update({
                "identity_protocol": STATE_IDENTITY_PROTOCOL,
                "source_identity": source_identity,
                "target_identity": target_identity,
            })
            if run_snapshot is not None:
                event_payload.update({
                    "run_snapshot_id": run_snapshot["snapshot_id"],
                    "run_snapshot_hash": run_snapshot["snapshot_hash"],
                })
        if binding_complete:
            event_payload.update({
                "gate_event_id": args.gate_event_id,
                "evidence_hash": args.evidence_hash,
                "evidence_refs": list(args.evidence_ref),
            })
        event_run_id = target_identity["run_id"] if target_identity is not None else args.run_id
        event_attempt_id = target_identity["attempt_id"] if target_identity is not None else args.attempt_id
        event_visit_id = target_identity["state_visit_id"] if target_identity is not None else None
        log = EventLog(workspace.events)
        with log._locked():
            pending_tmp, pending_target = workspace.prepare_meta_state(args.skill, snapshot)
            event = log.append(
                "state.transition",
                payload=event_payload,
                scope="skill",
                actor="bsk:state",
                attempt_id=event_attempt_id,
                run_id=event_run_id,
                state_visit_id=event_visit_id,
                idempotency_key=(args.idempotency_key or (
                    f"state:{args.skill}:{event_run_id}:{source_identity['state_visit_id'] if source_identity else 'initial'}:{event_visit_id or event_attempt_id}:{target.id}"
                    if event_run_id else None
                )),
                snapshot={"skill": args.skill, "state_hash": snapshot_hash},
                evidence_refs=args.evidence_ref if binding_complete else (),
                event_id=state_event_id,
                _lock_held=True,
            )
            path = workspace.commit_meta_state(pending_tmp, pending_target)
        snapshot["path"] = str(path)
        warnings = ["legacy_state_write"] if identity_mode == "legacy" else None
        gate_binding = log.inspect_transition_binding(event.event_id)
        _print(_state_response("transition", "transitioned", current_state=current, target_state=target.id, definition=target, execution=execution, snapshot=snapshot, source_identity=source_identity, target_identity=target_identity, identity_mode=identity_mode, downgrade_policy=downgrade_policy, warnings=warnings, gate_binding=gate_binding), pretty=True)
    else:
        build_parser().parse_args(["state", "--help"])
    return 0


def _run_workspace_command(args: argparse.Namespace) -> int:
    if args.workspace_command == "init":
        workspace = TaskWorkspace.open(args.project_root, task_root=args.task_root, description=args.description)
        _print({"status": "ready", **workspace.status()}, pretty=True)
    elif args.workspace_command == "path":
        workspace = TaskWorkspace.open_existing(args.task_root)
        paths = workspace.paths(args.skill)
        _print({"status": "ready", "task_root": str(paths.task_root), "skill": paths.skill, "kind": args.kind, "path": str(paths.path(args.kind))}, pretty=True)
    elif args.workspace_command == "status":
        _print(TaskWorkspace.open_existing(args.task_root).status(), pretty=True)
    elif args.workspace_command == "initialize":
        if args.attempt_id == "default":
            raise ValueError("default_attempt_forbidden: atomic initialization requires a non-default attempt_id")
        declaration = SkillStateDeclaration.from_skill_root(args.skill_root)
        registry = declaration.registry()
        _require_declared_state(registry, declaration, args.target_state)
        task_root = Path(args.task_root).expanduser().resolve() if args.task_root else None
        workspace, initialization_owner = TaskWorkspace.create_exclusive(
            args.project_root,
            task_root=task_root,
            description=args.description,
        )
        created_root = workspace.task_root
        transition_args = argparse.Namespace(
            state_command="transition",
            root=[],
            skill_root=args.skill_root,
            task_root=str(workspace.task_root),
            skill=args.skill,
            target_state=args.target_state,
            context_json=args.context_json,
            run_id=args.run_id,
            attempt_id="default",
            state_visit_id=None,
            target_state_visit_id=args.state_visit_id,
            target_attempt_id=args.attempt_id,
            gate_event_id=None,
            evidence_hash=None,
            evidence_ref=[],
            idempotency_key=args.idempotency_key,
            timeout=args.timeout,
        )
        captured = io.StringIO()
        try:
            with redirect_stdout(captured):
                code = _run_state_command(transition_args)
            response = json.loads(captured.getvalue())
            if code != 0 or response.get("status") != "transitioned":
                workspace.rollback_initialization(initialization_owner)
                response["status"] = "initialization_rejected"
                _print(response, pretty=True)
                return 2
        except Exception:
            if created_root.exists():
                workspace.rollback_initialization(initialization_owner)
            raise
        workspace.complete_initialization(initialization_owner)
        _print({
            **response,
            "status": "initialized",
            "task_root": str(workspace.task_root),
            "active_identity": response.get("target_identity"),
        }, pretty=True)
    else:
        build_parser().parse_args(["workspace", "--help"])
    return 0


def _run_action_command(args: argparse.Namespace) -> int:
    log = EventLog(args.events)
    if args.action_command == "preflight":
        event = log.preflight_action(
            skill=args.skill,
            action=args.action,
            state=args.state,
            state_version=args.state_version,
            run_id=args.run_id,
            attempt_id=args.attempt_id,
            state_visit_id=args.state_visit_id,
            handoff_id=args.handoff_id,
            evidence_refs=args.evidence_ref,
            idempotency_key=args.idempotency_key,
            expected_last_seq=args.expected_last_seq,
        )
        _print(event.to_dict())
    elif args.action_command == "consume":
        event = log.consume_action_authorization(
            args.authorization_id,
            skill=args.skill,
            action=args.action,
            run_id=args.run_id,
            attempt_id=args.attempt_id,
            state_visit_id=args.state_visit_id,
            idempotency_key=args.idempotency_key,
            expected_last_seq=args.expected_last_seq,
        )
        _print(event.to_dict())
    else:
        build_parser().parse_args(["action", "--help"])
    return 0


def _run_attempt_command(args: argparse.Namespace) -> int:
    if args.attempt_command != "start":
        build_parser().parse_args(["attempt", "--help"])
        return 0
    workspace = TaskWorkspace.open_existing(args.task_root)
    log = EventLog(workspace.events)
    with log._locked():
        return _start_attempt_locked(args, workspace, log)


def _start_attempt_locked(args: argparse.Namespace, workspace: TaskWorkspace, log: EventLog) -> int:
    """Persist one attempt event and its snapshot under the event-log lock."""
    previous = workspace.read_meta_state(args.skill)
    existing = next((item for item in log.read() if item.idempotency_key == args.idempotency_key), None)
    if existing is not None:
        if (
            existing.event_type != "state.attempt.started"
            or existing.payload.get("skill") != args.skill
            or existing.run_id != args.run_id
            or existing.state_visit_id != args.state_visit_id
            or existing.attempt_id != args.attempt_id
            or existing.payload.get("reason") != args.reason
            or previous.get("run_id") != args.run_id
            or previous.get("state_visit_id") != args.state_visit_id
            or previous.get("active_attempt_id") != args.attempt_id
        ):
            raise ValueError(f"idempotency key conflict: {args.idempotency_key}")
        _print({
            "protocol": META_STATE_PROTOCOL_VERSION,
            "operation": "attempt.start",
            "status": "started",
            "active_identity": {
                "run_id": args.run_id,
                "state_visit_id": args.state_visit_id,
                "attempt_id": args.attempt_id,
            },
            "event": existing.to_dict(),
            "snapshot": previous,
        }, pretty=True)
        return 0
    if previous.get("identity_protocol") != STATE_IDENTITY_PROTOCOL:
        raise ValueError("attempt start requires a v2 State visit snapshot")
    active = normalize_state_identity(
        {
            "run_id": previous.get("run_id"),
            "state_visit_id": previous.get("state_visit_id"),
            "attempt_id": previous.get("active_attempt_id"),
        },
        label="active identity",
    )
    if active["run_id"] != args.run_id or active["state_visit_id"] != args.state_visit_id:
        raise ValueError("requested run/state visit does not match the active snapshot")
    if active["attempt_id"] == args.attempt_id:
        raise ValueError("new attempt_id must differ from the active attempt")
    event_id = str(uuid.uuid4())
    snapshot = {
        key: value
        for key, value in previous.items()
        if key not in {"snapshot_hash", "path"}
    }
    snapshot.update({
        "protocol": META_STATE_PROTOCOL_VERSION,
        "active_attempt_id": args.attempt_id,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "last_operation": {
            "operation": "attempt.start",
            "status": "started",
            "supersedes_attempt_id": active["attempt_id"],
            "attempt_id": args.attempt_id,
            "reason": args.reason,
        },
    })
    snapshot_hash = state_snapshot_hash(snapshot)
    snapshot["snapshot_hash"] = snapshot_hash
    pending_tmp, pending_target = workspace.prepare_meta_state(args.skill, snapshot)
    event = log.start_attempt(
        skill=args.skill,
        state=str(previous["current_state"]),
        state_version=str(previous["state_version"]),
        run_id=args.run_id,
        state_visit_id=args.state_visit_id,
        attempt_id=args.attempt_id,
        reason=args.reason,
        idempotency_key=args.idempotency_key,
        expected_last_seq=args.expected_last_seq,
        event_id=event_id,
        snapshot={"skill": args.skill, "state_hash": snapshot_hash},
        snapshot_hash=snapshot_hash,
        snapshot_path=f"{args.skill}/log/meta-state.json",
        state_event_id=str(previous.get("state_event_id", "")),
        _lock_held=True,
    )
    workspace.commit_meta_state(pending_tmp, pending_target)
    active_identity = {
        "run_id": args.run_id,
        "state_visit_id": args.state_visit_id,
        "attempt_id": args.attempt_id,
    }
    _print({
        "protocol": META_STATE_PROTOCOL_VERSION,
        "operation": "attempt.start",
        "status": "started",
        "active_identity": active_identity,
        "event": event.to_dict(),
        "snapshot": snapshot,
    }, pretty=True)
    return 0


def _run_verifier_command(args: argparse.Namespace) -> int:
    registry, declaration = _verifier_registry(args)
    if args.verifier_command == "list":
        requirements = {
            (item["id"], item["version"]): item
            for item in declaration.verifier_requirements()
        } if declaration else None
        specs = registry.specs(tag=args.tag)
        if requirements is not None:
            specs = tuple(spec for spec in specs if (spec.verifier_id, spec.version) in requirements)
        values = []
        for spec in specs:
            value = _spec_dict(spec)
            if requirements is not None:
                value["required"] = requirements[(spec.verifier_id, spec.version)]["required"]
            values.append(value)
        _print({"verifiers": values}, pretty=True)
        return 0
    if args.verifier_command == "describe":
        definition = registry.describe(args.verifier_id, args.version)
        _declared_verifier_requirement(declaration, definition.verifier_id, definition.version)
        _print(definition.to_dict(), pretty=True)
        return 0
    if args.verifier_command != "run":
        build_parser().parse_args(["verifier", "--help"])
        return 0

    definition = registry.resolve(args.verifier_id, args.version)
    requirement = _declared_verifier_requirement(declaration, definition.verifier_id, definition.version)
    target = None
    if args.input:
        target = Path(args.input).expanduser().resolve()
        if not target.is_file():
            raise ValueError(f"input file does not exist: {args.input}")
        content_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        request_id = args.run_id or f"{definition.verifier_id}:{content_hash[:16]}"
        request_payload: dict[str, Any] = {
            "request_id": request_id,
            "subject": {"type": "file", "path": str(target), "content_hash": content_hash},
            "context": {"timeout": args.timeout, "blacklist": args.blacklist, "whitelist": args.whitelist},
        }
    else:
        raw_request = _read_json_value(args.request_file, args.request_json, label="a Verifier request")
        if not isinstance(raw_request, Mapping):
            raise ValueError("Verifier request must be a JSON object")
        request_payload = dict(raw_request)
        request_hash = hashlib.sha256(
            json.dumps(request_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()
        request_id = str(request_payload.get("request_id") or args.run_id or f"{definition.verifier_id}:{request_hash[:16]}")
        request_payload["request_id"] = request_id
    run_id = str(args.run_id or request_payload.get("run_id") or request_id)
    attempt_id = str(args.attempt_id or request_payload.get("attempt_id") or "default")
    state_visit_id = args.state_visit_id or request_payload.get("state_visit_id")
    state_visit_id = str(state_visit_id) if state_visit_id is not None else None
    request_payload["run_id"] = run_id
    request_payload["attempt_id"] = attempt_id
    if state_visit_id is not None:
        request_payload["state_visit_id"] = state_visit_id
    index = definition.metadata.get("index")
    contract_execution = None
    if isinstance(index, Mapping) and "components" in index:
        contract_execution = registry.run_contract(
            args.verifier_id,
            request_payload,
            version=args.version,
            timeout=args.timeout,
            run_id=run_id,
            attempt_id=attempt_id,
            state_visit_id=state_visit_id,
            submissions=request_payload.get("component_results", request_payload.get("submissions", ())),
        )
        raw_result = contract_execution.to_event_payload()
    else:
        raw_result = registry.run(args.verifier_id, request_payload, version=args.version, timeout=args.timeout)
    result_payloads = [{**raw_result, "request_id": request_id}]
    normalized = normalize_result(raw_result, definition.spec, evidence_refs=raw_result.get("evidence_refs", ()))
    component_gate = contract_execution.gate if contract_execution is not None else None
    gate = component_gate or apply_gate((normalized,))
    if requirement is not None:
        workflow_gate = apply_gate((normalized,), requirements=(requirement,))
        if component_gate is not None and component_gate.decision == "allow_with_warnings" and workflow_gate.decision == "allow":
            gate = component_gate
        else:
            gate = workflow_gate
    metric_results = contract_execution.components if contract_execution is not None else (normalized,)
    required_metric_ids = (
        ()
        if requirement is not None and not requirement["required"]
        else (definition.verifier_id,)
    )
    output: dict[str, Any] = {
        "verifier": _spec_dict(definition.spec),
        "request_id": request_id,
        "results": result_payloads,
        "gate": gate.to_dict(),
        "metrics": summarize_metrics(metric_results, (gate,), required_ids=required_metric_ids),
        "verification": {"request_id": request_id, "results": result_payloads, "gate": gate.to_dict()},
    }
    if target is not None:
        output["file"] = str(target)
    if requirement is not None:
        output["requirement"] = dict(requirement)
    if contract_execution is not None and contract_execution.report.handoffs:
        # Full hand-offs are returned to the invoking Agent but deliberately
        # kept outside ``results`` so EventLog never persists contract text or
        # raw subject/context as verification evidence.
        output["handoffs"] = [item.to_dict() for item in contract_execution.report.handoffs]
    facts = raw_result.get("facts", {})
    if isinstance(facts, Mapping) and "summary" in facts:
        output.update({"summary": facts["summary"], "references": facts.get("references", [])})
    if args.events:
        log = EventLog(args.events)
        persisted = []
        persisted_gate = None
        for index, result in enumerate(result_payloads):
            verification, gate_event = log.record_verification(
                result,
                {**gate.to_dict(), "request_id": request_id} if index == len(result_payloads) - 1 else None,
                scope=args.scope,
                actor=args.actor,
                attempt_id=attempt_id,
                idempotency_key=f"{args.idempotency_key or request_id}:{index}",
                run_id=run_id,
                state_visit_id=state_visit_id,
                requirements=(requirement,) if requirement is not None else None,
            )
            persisted.append({"result_event": verification.to_dict(), "gate_event": gate_event.to_dict() if gate_event else None})
            if gate_event is not None:
                persisted_gate = GateDecision(
                    decision=str(gate_event.payload["decision"]),
                    reason=str(gate_event.payload["reason"]),
                    result_refs=tuple(gate_event.payload.get("result_refs", ())),
                    unresolved=tuple(gate_event.payload.get("unresolved", ())),
                )
        if persisted_gate is not None:
            output["gate"] = persisted_gate.to_dict()
            output["verification"]["gate"] = persisted_gate.to_dict()
            output["metrics"] = summarize_metrics(metric_results, (persisted_gate,), required_ids=required_metric_ids)
        output["runtime"] = {"recorded": True, "events": persisted}
    _print(output, pretty=True)
    return 0


def _run_command(args: argparse.Namespace) -> int:
    if args.command == "verifier":
        return _run_verifier_command(args)
    if args.command == "state":
        return _run_state_command(args)
    if args.command == "workspace":
        return _run_workspace_command(args)
    if args.command == "attempt":
        return _run_attempt_command(args)
    if args.command == "action":
        return _run_action_command(args)
    if args.command == "capabilities":
        _print(kernel_capabilities(version=__version__), pretty=True)
        return 0
    if args.command == "diagnostics":
        _print(kernel_diagnostics(version=__version__), pretty=True)
        return 0
    if args.command == "status":
        _print(_log(args).projection(), pretty=True)
    elif args.command == "rebuild":
        _print(_log(args).rebuild(args.state_file), pretty=True)
    elif args.command == "append":
        payload = _json_object(args.payload, label="--payload")
        if args.payload_file:
            payload = _read_json_file(args.payload_file, label="--payload-file")
        event = _log(args).append(
            args.event_type,
            payload=payload,
            summary=args.summary,
            scope=args.scope,
            actor=args.actor,
            attempt_id=args.attempt_id,
            path=args.path,
            evidence_refs=args.evidence_ref,
            idempotency_key=args.idempotency_key,
            run_id=args.run_id,
            state_visit_id=args.state_visit_id,
        )
        _print(event.to_dict())
    elif args.command == "transition":
        payload = {key: value for key, value in (("wait_reason", args.wait_reason), ("phase", args.phase)) if value is not None}
        _print(_log(args).transition(args.to, scope=args.scope, actor=args.actor, attempt_id=args.attempt_id, **payload).to_dict())
    elif args.command == "artifact":
        _print(_log(args).record_artifact(args.artifact_id, required=args.required, **_json_object(args.metadata, label="--metadata")).to_dict())
    elif args.command == "validation":
        _print(_log(args).record_validation(args.verdict, evidence_refs=args.evidence_ref, **_json_object(args.metadata, label="--metadata")).to_dict())
    elif args.command == "verification":
        raw_results = _read_json_value(args.result_file, args.result_json, label="a verification result")
        results = raw_results if isinstance(raw_results, list) else [raw_results]
        if not results:
            raise ValueError("verification result list cannot be empty")
        if not all(isinstance(item, Mapping) for item in results):
            raise ValueError("verification result must be a JSON object or list of objects")
        gate = _read_json_value(args.gate_file, args.gate_json, label="a gate") if (args.gate_file or args.gate_json) else None
        if gate is not None and not isinstance(gate, Mapping):
            raise ValueError("gate must be a JSON object")
        log = _log(args)
        before_count = len(log.read())
        last_result, gate_event = log.record_verification_batch(
            (dict(result) for result in results),
            dict(gate) if gate is not None else None,
            scope=args.scope,
            actor=args.actor,
            attempt_id=args.attempt_id,
            idempotency_key=args.idempotency_key,
            run_id=args.run_id,
            state_visit_id=args.state_visit_id,
        )
        # Keep the historical per-result CLI response while persisting one
        # kernel-computed gate for the complete batch.  Reading the appended
        # slice avoids expanding the public EventLog return type.
        all_events = log.read()
        result_events = [event for event in all_events[before_count:] if event.event_type == "verification.result"]
        if len(result_events) < len(results):
            # Idempotent retries append nothing; recover the existing batch
            # events so the response shape remains one entry per input.
            if args.idempotency_key:
                key_order = [f"{args.idempotency_key}:{index}" for index in range(len(results))]
                by_key = {event.idempotency_key: event for event in all_events if event.event_type == "verification.result"}
                result_events = [by_key[key] for key in key_order if key in by_key]
            else:
                matching = [
                    event for event in all_events
                    if event.event_type == "verification.result"
                    and event.run_id == args.run_id
                    and event.state_visit_id == args.state_visit_id
                    and event.attempt_id == args.attempt_id
                    and event.scope == args.scope
                    and event.actor == args.actor
                ]
                result_events = matching[-len(results):]
        if not result_events:
            result_events = [last_result]
        events = [
            {
                "result_event": event.to_dict(),
                "gate_event": gate_event.to_dict() if index == len(result_events) - 1 and gate_event else None,
            }
            for index, event in enumerate(result_events)
        ]
        _print({"events": events})
    elif args.command == "delivery":
        _print(_log(args).record_delivery(args.report, **_json_object(args.metadata, label="--metadata")).to_dict())
    else:
        build_parser().print_help()
    return 0


def _run_legacy(argv: list[str]) -> int:
    args = _legacy_parser().parse_args(argv)
    if args.status:
        _print(EventLog(args.status).projection(), pretty=True)
    elif args.rebuild:
        _print(EventLog(args.rebuild).rebuild(), pretty=True)
    elif args.append_event:
        if not args.event_type:
            raise ValueError("--append-event requires --type")
        event = EventLog(args.append_event).append(args.event_type, payload=_json_object(args.payload, label="--payload"), summary=args.summary)
        _print(event.to_dict())
    else:
        _legacy_parser().print_help()
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv and argv[0].startswith("--") and argv[0] not in {"--help", "-h", "--version"}:
            return _run_legacy(argv)
        args = build_parser().parse_args(argv)
        return _run_command(args)
    except IntegrityError as exc:
        print(json.dumps({"error": "integrity_error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (KernelError, KeyError, ValueError, OSError) as exc:
        print(f"bsk: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
