"""Public ``bsk`` command line interface.

The CLI is intentionally domain-neutral.  Skills collect their own facts and
use these small commands to append lifecycle, evidence, verification and
delivery events without reimplementing the kernel protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .builtins import build_builtin_registry
from .runtime import EventLog, IntegrityError, KernelError
from .states import META_STATE_PROTOCOL_VERSION, SkillStateDeclaration, StateMachine, build_state_registry, check_state_invariants, execute_state
from .workspace import TaskWorkspace, WorkspaceError, WORKSPACE_KINDS, state_snapshot_hash
from .verifiers import Evidence, FilesystemVerifierRegistry, GateDecision, VerificationRequest, VerifierRunner, VerificationResult, apply_gate, builtin_verifier_root, summarize_metrics
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bsk",
        description="Bensz Skill lifecycle and verification kernel",
        epilog="Skills normally use subcommands; legacy --status/--rebuild/--append-event remain supported.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")

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
    _add_contract(verification)

    delivery = commands.add_parser("delivery", help="record a delivery report")
    delivery.add_argument("events", metavar="EVENTS")
    delivery.add_argument("report", metavar="REPORT")
    delivery.add_argument("--metadata", default="{}")
    _add_contract(delivery)

    verifier = commands.add_parser("verifier", help="discover and run built-in verifier packs")
    verifier_commands = verifier.add_subparsers(dest="verifier_command", metavar="ACTION")
    verifier_list = verifier_commands.add_parser("list", help="list available verifier ids")
    verifier_list.add_argument("--tag")
    verifier_describe = verifier_commands.add_parser("describe", help="show one verifier contract")
    verifier_describe.add_argument("verifier_id")
    verifier_describe.add_argument("--version")
    verifier_run = verifier_commands.add_parser("run", help="run a built-in verifier")
    verifier_run.add_argument("verifier_id")
    verifier_run.add_argument("--version")
    verifier_run.add_argument("--input", required=True, help="subject file path")
    verifier_run.add_argument("--timeout", type=int, default=10)
    verifier_run.add_argument("--blacklist", action="append", default=[])
    verifier_run.add_argument("--whitelist", action="append", default=[])
    verifier_run.add_argument("--events", help="append verifier results and Gate to an event log")
    verifier_run.add_argument("--run-id")
    verifier_run.add_argument("--attempt-id", default="default")
    verifier_run.add_argument("--actor", default="bsk:verifier")
    verifier_run.add_argument("--scope", default="skill")
    verifier_run.add_argument("--idempotency-key")

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
    state_transition.add_argument("--timeout", type=int, default=10)
    _add_state_source(state_transition)

    workspace = commands.add_parser("workspace", help="initialize and resolve BenszAPI task workspaces")
    workspace_commands = workspace.add_subparsers(dest="workspace_command", metavar="ACTION")
    workspace_init = workspace_commands.add_parser("init", help="create or reopen a task workspace")
    workspace_init.add_argument("project_root", nargs="?", default=".")
    workspace_init.add_argument("--task-root")
    workspace_init.add_argument("--description", default="task")
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


def _verifier_registry() -> FilesystemVerifierRegistry:
    return FilesystemVerifierRegistry(builtin_verifier_root())


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


def _state_response(operation: str, status: str, *, current_state: str | None = None, target_state: str | None = None, definition: Any = None, execution: Any = None, snapshot: Any = None, reason: str | None = None) -> dict[str, Any]:
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
    return output


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
        if not machine.can_transition(args.target_state):
            _print(_state_response("transition", "rejected", current_state=current, target_state=target.id, definition=target, snapshot=previous, reason="The target is not an allowed transition from the current state."), pretty=True)
            return 0
        events = EventLog(workspace.events).read()
        context = _json_object(args.context_json, label="--context-json")
        if args.run_id is not None:
            context = {**context, "run_id": args.run_id, "attempt_id": args.attempt_id}
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
            ), pretty=True)
            return 0
        execution = execute_state(target, {"operation": "enter", "task_root": str(workspace.task_root), "skill": args.skill, "current_state": current, "target_state": target.id, "context": context}, timeout=args.timeout)
        if execution.execution_status != "not_applicable" and execution.verdict != "pass":
            _print(_state_response("transition", "rejected", current_state=current, target_state=target.id, definition=target, execution=execution, snapshot=previous, reason="The state helper did not pass, so the transition was not persisted."), pretty=True)
            return 0
        machine.transition(args.target_state, events=events, context=context)
        snapshot = {
            "protocol": META_STATE_PROTOCOL_VERSION,
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
        snapshot_hash = state_snapshot_hash(snapshot)
        # Stage a pending snapshot before appending the event.  The stable
        # event ID is preallocated so recovery can detect an interrupted
        # commit instead of silently accepting a split projection.
        state_event_id = str(uuid.uuid4())
        snapshot["state_event_id"] = state_event_id
        snapshot["snapshot_hash"] = snapshot_hash
        pending_tmp, pending_target = workspace.prepare_meta_state(args.skill, snapshot)
        state_event = EventLog(workspace.events).append(
            "state.transition",
            payload={
                "state_domain": "skill",
                "skill": args.skill,
                "from_state": current,
                "to_state": target.id,
                "state_version": target.version,
                "snapshot_hash": snapshot_hash,
                "snapshot_path": f"{args.skill}/log/meta-state.json",
                "state_event_id": state_event_id,
            },
            scope="skill",
            actor="bsk:state",
            attempt_id=args.attempt_id,
            run_id=args.run_id,
            idempotency_key=(f"state:{args.skill}:{args.run_id}:{args.attempt_id}:{target.id}" if args.run_id else None),
            snapshot={"skill": args.skill, "state_hash": snapshot_hash},
            event_id=state_event_id,
        )
        path = workspace.commit_meta_state(pending_tmp, pending_target)
        snapshot["path"] = str(path)
        _print(_state_response("transition", "transitioned", current_state=current, target_state=target.id, definition=target, execution=execution, snapshot=snapshot), pretty=True)
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
    else:
        build_parser().parse_args(["workspace", "--help"])
    return 0


def _run_verifier_command(args: argparse.Namespace) -> int:
    registry = _verifier_registry()
    if args.verifier_command == "list":
        _print({"verifiers": [_spec_dict(spec) for spec in registry.specs(tag=args.tag)]}, pretty=True)
        return 0
    if args.verifier_command == "describe":
        definition = registry.describe(args.verifier_id, args.version)
        _print(definition.to_dict(), pretty=True)
        return 0
    if args.verifier_command != "run":
        build_parser().parse_args(["verifier", "--help"])
        return 0

    definition = registry.resolve(args.verifier_id, args.version)
    target = Path(args.input).expanduser().resolve()
    if not target.is_file():
        raise ValueError(f"input file does not exist: {args.input}")
    content_hash = hashlib.sha256(target.read_bytes()).hexdigest()
    request_id = args.run_id or f"{definition.verifier_id}:{content_hash[:16]}"
    request_payload = {"request_id": request_id, "subject": {"type": "file", "path": str(target), "content_hash": content_hash}, "context": {"timeout": args.timeout, "blacklist": args.blacklist, "whitelist": args.whitelist}}
    index = definition.metadata.get("index")
    contract_execution = None
    if isinstance(index, Mapping) and "components" in index:
        contract_execution = registry.run_contract(
            args.verifier_id,
            request_payload,
            version=args.version,
            timeout=args.timeout,
            run_id=request_id,
            attempt_id=args.attempt_id,
        )
        raw_result = contract_execution.to_event_payload()
    else:
        raw_result = registry.run(args.verifier_id, request_payload, version=args.version, timeout=args.timeout)
    result_payloads = [{**raw_result, "request_id": request_id}]
    normalized = VerificationResult(
        verifier_id=raw_result["verifier_id"], verifier_version=raw_result["verifier_version"], execution_status=raw_result["execution_status"], verdict=raw_result["verdict"], findings=tuple(raw_result.get("findings", ())), facts=dict(raw_result.get("facts", {})), evidence_refs=tuple(raw_result.get("evidence_refs", ())), confidence=raw_result.get("confidence"), uncertainty_reason=raw_result.get("uncertainty_reason"), model_or_engine=raw_result.get("model_or_engine"), duration_ms=raw_result.get("duration_ms"),
    )
    gate = contract_execution.gate if contract_execution is not None else apply_gate((normalized,))
    output: dict[str, Any] = {
        "verifier": _spec_dict(definition.spec),
        "request_id": request_id,
        "file": str(target),
        "results": result_payloads,
        "gate": gate.to_dict(),
        "metrics": summarize_metrics((normalized,), (gate,)),
        "verification": {"request_id": request_id, "results": result_payloads, "gate": gate.to_dict()},
    }
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
                attempt_id=args.attempt_id,
                idempotency_key=f"{args.idempotency_key or request_id}:{index}",
                run_id=request_id,
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
            output["metrics"] = summarize_metrics((normalized,), (persisted_gate,))
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
