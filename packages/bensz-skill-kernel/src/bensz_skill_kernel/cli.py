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
from pathlib import Path
from typing import Any, Mapping

from .builtins import build_builtin_registry, collect_markdown
from .runtime import EventLog, KernelError
from .states import FilesystemStateRegistry, build_builtin_state_registry
from .workspace import TaskWorkspace, WorkspaceError, WORKSPACE_KINDS
from .verifiers import Evidence, FilesystemVerifierRegistry, VerificationRequest, VerifierRunner, VerificationResult, apply_gate


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
    state_list.add_argument("--root", help="additional state definition root")
    state_list.add_argument("--kind")
    state_describe = state_commands.add_parser("describe", help="show one state definition")
    state_describe.add_argument("state_id")
    state_describe.add_argument("--root", help="additional state definition root")

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
        "metadata": dict(spec.metadata),
    }


def _verifier_registry() -> FilesystemVerifierRegistry:
    root = Path(__file__).resolve().parents[2] / "verifiers"
    return FilesystemVerifierRegistry(root)


def _state_registry(root: str | None = None):
    return build_builtin_state_registry() if root is None else FilesystemStateRegistry(root)


def _run_state_command(args: argparse.Namespace) -> int:
    registry = _state_registry(getattr(args, "root", None))
    if args.state_command == "list":
        _print({"states": [item.to_dict() for item in registry.definitions(kind=args.kind)]}, pretty=True)
    elif args.state_command == "describe":
        _print(registry.resolve(args.state_id).to_dict(), pretty=True)
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
    raw_result = registry.run(args.verifier_id, request_payload, version=args.version, timeout=args.timeout)
    result_payloads = [{**raw_result, "request_id": request_id}]
    normalized = VerificationResult(
        verifier_id=raw_result["verifier_id"], verifier_version=raw_result["verifier_version"], execution_status=raw_result["execution_status"], verdict=raw_result["verdict"], findings=tuple(raw_result.get("findings", ())), facts=dict(raw_result.get("facts", {})), evidence_refs=tuple(raw_result.get("evidence_refs", ())), confidence=raw_result.get("confidence"), uncertainty_reason=raw_result.get("uncertainty_reason"), model_or_engine=raw_result.get("model_or_engine"), duration_ms=raw_result.get("duration_ms"),
    )
    gate = apply_gate((normalized,))
    output: dict[str, Any] = {
        "verifier": _spec_dict(definition.spec),
        "request_id": request_id,
        "file": str(target),
        "results": result_payloads,
        "gate": gate.to_dict(),
        "verification": {"request_id": request_id, "results": result_payloads, "gate": gate.to_dict()},
    }
    facts = raw_result.get("facts", {})
    if isinstance(facts, Mapping) and "summary" in facts:
        output.update({"summary": facts["summary"], "references": facts.get("references", [])})
    if args.events:
        log = EventLog(args.events)
        persisted = []
        for index, result in enumerate(result_payloads):
            verification, gate_event = log.record_verification(
                result,
                {**gate.to_dict(), "request_id": request_id} if index == len(result_payloads) - 1 else None,
                scope=args.scope,
                actor=args.actor,
                attempt_id=args.attempt_id,
                idempotency_key=f"{args.idempotency_key or request_id}:{index}",
            )
            persisted.append({"result_event": verification.to_dict(), "gate_event": gate_event.to_dict() if gate_event else None})
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
        events = []
        for index, result in enumerate(results):
            result_event, gate_event = _log(args).record_verification(
                dict(result),
                dict(gate) if gate is not None and index == len(results) - 1 else None,
                scope=args.scope,
                actor=args.actor,
                attempt_id=args.attempt_id,
                idempotency_key=f"{args.idempotency_key}:{index}" if args.idempotency_key else None,
            )
            events.append({"result_event": result_event.to_dict(), "gate_event": gate_event.to_dict() if gate_event else None})
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
        if argv and argv[0].startswith("--") and argv[0] not in {"--help", "-h"}:
            return _run_legacy(argv)
        args = build_parser().parse_args(argv)
        return _run_command(args)
    except (KernelError, KeyError, ValueError, OSError) as exc:
        print(f"bsk: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
