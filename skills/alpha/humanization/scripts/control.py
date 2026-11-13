#!/usr/bin/env python3
"""The single controlled revision release entry. Run with Bensz managed Python."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from revision_evidence import (
    ControlError, SKILL_ROOT, canonical, config, digest, load_request,
    read_bytes, read_json, safe_path, validate_review, validate_reviewers, write_json,
)

PROTOCOL = "bensz-revision-control-v1"
SKILL = "humanization"
SESSION = "humanization/log/control-session.json"
BSK = Path.home() / ".bensz-skills/bin/bsk"
MANAGED_PYTHON = Path.home() / ".bensz-skills/envs/benszapi/bin/python"


def run_json(argv: list[str], *, timeout: int | None = None) -> dict:
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout or config()["control_policy"]["command_timeout_seconds"],
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, check=False)
    except subprocess.TimeoutExpired as error:
        raise ControlError("runtime_timeout") from error
    try:
        value = json.loads(result.stdout)
    except (ValueError, TypeError) as error:
        raise ControlError("runtime_invalid_json") from error
    if result.returncode or not isinstance(value, dict):
        raise ControlError("runtime_command_failed")
    return value


def managed_runtime(*, update: bool) -> str:
    if not MANAGED_PYTHON.is_file() or Path(sys.executable).resolve() != MANAGED_PYTHON.resolve() or not BSK.is_file():
        raise ControlError("managed_python_required")
    if update:
        installers = [Path.home() / f".{host}/skills/install-bensz-skills/scripts/install.py" for host in ("codex", "claude")]
        installer = next((p for p in installers if p.is_file()), None)
        if installer is None:
            raise ControlError("runtime_manager_missing")
        receipt = run_json([str(MANAGED_PYTHON), str(installer), "--force-runtime-update"], timeout=300)
        if receipt.get("last_result") != "success" or receipt.get("ready") is not True:
            raise ControlError("runtime_update_unconfirmed")
        expected = receipt.get("packages", {}).get("bensz-skill-kernel")
    else:
        expected = importlib.metadata.version("bensz-skill-kernel")
    diagnostics = run_json([str(BSK), "diagnostics"])
    version = importlib.metadata.version("bensz-skill-kernel")
    if diagnostics.get("protocol") != "bensz-kernel-diagnostics-v1" or diagnostics.get("kernel_version") != version or version != expected:
        raise ControlError("runtime_version_mismatch")
    return version


def validate_name(value: str) -> str:
    if value == "default" or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", value):
        raise ControlError("invalid_identity")
    return value


def asset_hashes() -> dict:
    paths = [SKILL_ROOT / "config.yaml", SKILL_ROOT / "SKILL.md"]
    paths += list((SKILL_ROOT / "scripts").glob("*.py"))
    paths += list((SKILL_ROOT / "references").rglob("*.py"))
    paths += list((SKILL_ROOT / "references").rglob("*.md"))
    paths += list((SKILL_ROOT / "references").rglob("index.json"))
    return {p.relative_to(SKILL_ROOT).as_posix(): digest(p.read_bytes()) for p in sorted(paths)}


def task_path(project: Path, task: str) -> Path:
    if project.is_symlink():
        raise ControlError("project_symlink_forbidden")
    project = project.resolve(strict=True)
    path = Path(task)
    if not path.is_absolute():
        path = project / path
    # Check the complete path before resolving it, including .bensz-api itself.
    try:
        relative = path.relative_to(project).as_posix()
    except ValueError as error:
        raise ControlError("task_outside_project") from error
    path = safe_path(project, relative)
    if path.parent != project / ".bensz-api" or not path.name.startswith("task-"):
        raise ControlError("invalid_task_root")
    return path


def identity(snapshot: dict) -> dict:
    return {"run_id": snapshot.get("run_id"), "state_visit_id": snapshot.get("state_visit_id"),
            "attempt_id": snapshot.get("active_attempt_id")}


def read_state(root: Path, run_id: str, attempt_id: str | None = None) -> dict:
    from bensz_skill_kernel import EventLog, SkillStateDeclaration, TaskWorkspace

    workspace = TaskWorkspace.open_existing(root)
    snapshot = workspace.read_meta_state(SKILL)
    declaration = SkillStateDeclaration.from_skill_root(SKILL_ROOT)
    registry = declaration.registry()
    if snapshot.get("protocol") != "bensz-meta-state-v2" or snapshot.get("identity_protocol") != "bensz-state-identity-v2":
        raise ControlError("state_identity_required")
    state = registry.resolve(snapshot.get("current_state"))
    if state.id not in declaration.states or snapshot.get("state_version") != state.version:
        raise ControlError("state_version_mismatch")
    if snapshot.get("run_id") != run_id or (attempt_id is not None and snapshot.get("active_attempt_id") != attempt_id):
        raise ControlError("state_identity_mismatch")
    events = EventLog(workspace.events).query_transitions(run_id=run_id, skill=SKILL)
    if not events or events[-1].payload.get("to_state") != state.id or events[-1].event_id != snapshot.get("state_event_id"):
        raise ControlError("state_event_mismatch")
    manifest_snapshot = workspace.manifest().get("run_snapshot", {})
    if snapshot.get("run_snapshot_hash") != manifest_snapshot.get("snapshot_hash"):
        raise ControlError("run_snapshot_mismatch")
    return snapshot


def check_transition(response: dict, root: Path, target: str, run_id: str, target_attempt: str,
                     *, source: dict | None = None, gate_id: str | None = None) -> dict:
    from bensz_skill_kernel import SkillStateDeclaration

    state = SkillStateDeclaration.from_skill_root(SKILL_ROOT).registry().resolve(target)
    expected = {"protocol": "bensz-meta-state-v2", "operation": "transition", "status": "transitioned", "target_state": target}
    if any(response.get(k) != v for k, v in expected.items()) or response.get("state", {}).get("id") != target or response.get("state", {}).get("version") != state.version:
        raise ControlError("transition_receipt_invalid")
    snapshot = read_state(root, run_id, target_attempt)
    target_identity = identity(snapshot)
    if snapshot["current_state"] != target or response.get("target_identity") != target_identity:
        raise ControlError("transition_snapshot_mismatch")
    if response.get("snapshot", {}).get("snapshot_hash") != snapshot.get("snapshot_hash"):
        raise ControlError("transition_snapshot_mismatch")
    if source is not None:
        binding = response.get("gate_binding", {})
        if response.get("source_identity") != source or binding.get("status") != "bound" or binding.get("gate_event_id") != gate_id:
            raise ControlError("transition_binding_invalid")
    return snapshot


def state_command(root: Path, target: str, run_id: str, target_attempt: str, *, source: dict | None = None,
                  gate_id: str | None = None, evidence_hash: str | None = None, evidence_ref: str | None = None) -> dict:
    argv = [str(BSK), "state", "transition", str(root), SKILL, target, "--skill-root", str(SKILL_ROOT),
            "--run-id", run_id, "--target-attempt-id", target_attempt]
    if source:
        argv += ["--state-visit-id", source["state_visit_id"], "--attempt-id", source["attempt_id"],
                 "--gate-event-id", gate_id, "--evidence-hash", evidence_hash, "--evidence-ref", evidence_ref,
                 "--idempotency-key", "revision-release:" + evidence_hash]
    else:
        argv += ["--idempotency-key", "revision-init:" + digest(canonical({"run_id": run_id, "attempt_id": target_attempt}))]
    return run_json(argv)


def session(root: Path, args: argparse.Namespace, version: str, *, allow_pending: bool = False) -> dict:
    data = read_json(root, SESSION)
    if data.get("run_id") != args.run_id or data.get("request_ref") != args.request_file:
        raise ControlError("session_mismatch")
    if data.get("runtime_version") != version or data.get("runtime_update_confirmed") is not True:
        raise ControlError("runtime_update_unconfirmed")
    if data.get("asset_hashes") != asset_hashes():
        raise ControlError("runtime_contract_drift")
    if data.get("pending_operation") and not allow_pending:
        raise ControlError("operation_incomplete_resume_required")
    if load_request(root, args.request_file, complete=False) != data.get("input"):
        raise ControlError("input_changed_retry_required")
    return data


def check_frozen(root: Path, request_ref: str, index: dict) -> None:
    if load_request(root, request_ref, complete=True) != index:
        raise ControlError("evidence_changed_retry_required")


def check_gate(event, requirements: list, source: dict, evidence_hash: str, evidence_ref: str) -> dict:
    gate = event.payload
    refs = {r["id"] + "@" + r["version"] for r in requirements if r["required"]}
    if gate.get("computed_by") != "kernel" or set(gate.get("result_refs", [])) != refs or any(getattr(event, k) != v for k, v in source.items()):
        raise ControlError("gate_binding_invalid")
    if gate.get("evidence_hash") != evidence_hash or gate.get("evidence_refs") != [evidence_ref]:
        raise ControlError("gate_evidence_mismatch")
    return gate


def validate_submissions(submissions: list, index: dict, root: Path, source: dict, *, readback: bool = False) -> None:
    """Skill-level schemas; BSK remains responsible for ComponentResult binding."""
    expected = {"bensz.prose.revision-readiness": "semantic-review",
                "bensz.prose.defensive-framing": "defensive-review"}
    rosters = []
    seen = set()
    for submission in submissions:
        pack_id = submission.get("pack_id")
        if pack_id not in expected or submission.get("component_id") != expected[pack_id] or pack_id in seen:
            raise ControlError("unexpected_review_component")
        seen.add(pack_id)
        if submission.get("verdict") != "pass":
            continue
        facts = submission.get("facts")
        # BSK audit redaction intentionally masks keys such as protected_token_diff.
        # Readback trusts the recorded completed verdict for that already-checked schema,
        # while rechecking the externally stored reviewer bytes and their bindings.
        if readback:
            pass
        elif pack_id == "bensz.prose.revision-readiness":
            validate_review(facts, index, root)
        else:
            path = SKILL_ROOT / "references/verifiers/defensive-framing/scripts/evidence.py"
            spec = importlib.util.spec_from_file_location("defensive_evidence", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.validate_defensive_review(facts, index, root)
        rosters.append(validate_reviewers(facts, index, root, source, pack_id))
    if rosters and any(roster != rosters[0] for roster in rosters[1:]):
        raise ControlError("reviewer_roster_mismatch")


def recover_ready(root: Path, args: argparse.Namespace, snapshot: dict, mapping: dict) -> dict:
    """Read only authoritative BSK events and frozen bytes; receipt is a cache."""
    from bensz_skill_kernel import EventLog, SkillVerifierDeclaration, TaskWorkspace

    log = EventLog(TaskWorkspace.open_existing(root).events)
    transition = log.query_transitions(run_id=args.run_id, skill=SKILL)[-1]
    binding = log.inspect_transition_binding(transition.event_id)
    source = transition.payload.get("source_identity")
    if (binding.get("status") != "bound" or not isinstance(source, dict)
            or transition.payload.get("from_state") != mapping["current_state"]
            or transition.payload.get("to_state") != mapping["target_state"]
            or transition.payload.get("target_identity") != identity(snapshot)):
        raise ControlError("ready_transition_invalid")
    source_attempt = validate_name(source["attempt_id"])
    index_ref = f"humanization/log/attempt-{source_attempt}-evidence.json"
    index = read_json(root, index_ref)
    check_frozen(root, args.request_file, index)
    evidence_hash = digest(canonical(index))
    if transition.payload.get("evidence_hash") != evidence_hash or transition.payload.get("evidence_refs") != [index_ref]:
        raise ControlError("ready_evidence_mismatch")
    gate_event = log.validate_transition_gate_binding(gate_event_id=transition.payload["gate_event_id"],
                source_identity=source, evidence_hash=evidence_hash, evidence_refs=[index_ref])
    requirements = SkillVerifierDeclaration.from_skill_root(SKILL_ROOT).verifier_requirements()
    required = [r for r in requirements if r["required"]]
    if not required:
        raise ControlError("required_verifiers_missing")
    gate = check_gate(gate_event, required, source, evidence_hash, index_ref)
    if gate.get("decision") not in {"allow", "allow_with_warnings"}:
        raise ControlError("ready_gate_not_allowing")
    # A batch is appended atomically: the required result events immediately
    # precede its Gate. Do not select unrelated later results for the same ID.
    events = log.read()
    position = next(i for i, e in enumerate(events) if e.event_id == gate_event.event_id)
    results = events[max(0, position - len(required)):position]
    expected = {(r["id"], r["version"]) for r in required}
    if (len(results) != len(required) or not results or results[-1].event_id != gate.get("result_event_id")
            or {(e.payload.get("verifier_id"), e.payload.get("verifier_version")) for e in results} != expected):
        raise ControlError("ready_results_missing")
    for event in results:
        if (event.event_type != "verification.result" or event.payload.get("verdict") != "pass"
                or event.payload.get("execution_status") != "completed"
                or any(getattr(event, k) != v for k, v in source.items())
                or event.payload.get("evidence_hash") != evidence_hash or event.payload.get("evidence_refs") != [index_ref]):
            raise ControlError("ready_result_invalid")
    reviews = [component for event in results for component in event.payload.get("component_results", [])
               if component.get("component_id") in {"semantic-review", "defensive-review"}]
    if len(reviews) != len(required) or any(review.get("verdict") != "pass" for review in reviews):
        raise ControlError("ready_reviews_missing")
    validate_submissions(reviews, index, root, source, readback=True)
    receipt = {"protocol": PROTOCOL, "action": args.action, "run_id": args.run_id,
               "attempt_id": args.attempt_id, "source_attempt_id": source_attempt, "status": "already_ready",
               "previous_state": mapping["current_state"], "target_state": mapping["target_state"],
               "current_state": snapshot["current_state"], "evidence_hash": evidence_hash, "delivery": index["delivery"],
               "required_results": [{"id": e.payload["verifier_id"], "version": e.payload["verifier_version"], "verdict": "pass"} for e in results],
               "gate": {**gate, "event_id": gate_event.event_id},
               "transition": {"operation": "readback", "status": "transitioned", "event": transition.to_dict(), "gate_binding": binding}}
    check_frozen(root, args.request_file, index)
    write_json(root, "humanization/log/release.json", receipt)
    return receipt


def execute(args: argparse.Namespace) -> dict:
    action = args.action
    cfg = config()
    mappings = cfg["runtime"]["orchestration"]["actions"]
    if action not in {*mappings, "init", "retry", "status"}:
        raise ControlError("unknown_action")
    validate_name(args.run_id)
    validate_name(args.attempt_id)
    root = task_path(Path(args.project_root), args.task_root)
    version = managed_runtime(update=action == "init")
    from bensz_skill_kernel import EventLog, SkillVerifierDeclaration, TaskWorkspace

    if action == "init":
        initial_input = load_request(root, args.request_file, complete=False)
        target = cfg["runtime"]["initial_state"]
        pending = {"action": "init", "attempt_id": args.attempt_id}
        if safe_path(root, SESSION).exists():
            data = session(root, args, version, allow_pending=True)
            if data.get("pending_operation") != pending:
                if data.get("pending_operation") or data.get("initial_attempt_id") != args.attempt_id:
                    raise ControlError("initialization_identity_mismatch")
                snapshot = read_state(root, args.run_id, args.attempt_id)
                if snapshot["current_state"] != target:
                    raise ControlError("already_initialized")
                return {"status": "initialized", "current_state": target, "identity": identity(snapshot)}
        else:
            initialized = run_json([str(BSK), "workspace", "init", args.project_root, "--task-root", str(root)])
            if initialized.get("status") != "ready":
                raise ControlError("workspace_init_failed")
            if TaskWorkspace.open_existing(root).manifest().get("run_snapshot"):
                raise ControlError("workspace_already_bound")
            data = {"protocol": PROTOCOL, "run_id": args.run_id, "request_ref": args.request_file,
                    "runtime_version": version, "runtime_update_confirmed": True,
                    "asset_hashes": asset_hashes(), "input": initial_input,
                    "initial_attempt_id": args.attempt_id, "pending_operation": pending}
            # Commit intent first. The stable CLI key resumes either side of
            # the BSK transition without inventing a second State visit.
            write_json(root, SESSION, data)
        response = state_command(root, target, args.run_id, args.attempt_id)
        snapshot = check_transition(response, root, target, args.run_id, args.attempt_id)
        if load_request(root, args.request_file, complete=False) != initial_input:
            raise ControlError("input_changed_retry_required")
        data.pop("pending_operation")
        write_json(root, SESSION, data)
        return {"status": "initialized", "current_state": snapshot["current_state"], "transition": response}

    data = read_json(root, SESSION)
    if action == "retry":
        if data.get("run_id") != args.run_id or data.get("request_ref") != args.request_file or data.get("runtime_version") != version:
            raise ControlError("session_mismatch")
        if data.get("asset_hashes") != asset_hashes() or data.get("runtime_update_confirmed") is not True:
            raise ControlError("runtime_contract_drift")
        new_input = load_request(root, args.request_file, complete=False)
        snapshot = read_state(root, args.run_id)
        if snapshot["current_state"] != cfg["runtime"]["initial_state"]:
            raise ControlError("new_working_attempt_required")
        pending = data.get("pending_operation")
        if pending:
            if (pending.get("action") != "retry" or pending.get("attempt_id") != args.attempt_id
                    or pending.get("input") != new_input):
                raise ControlError("retry_intent_mismatch")
            old = pending["source"]
            if identity(snapshot) not in (old, {**old, "attempt_id": args.attempt_id}):
                raise ControlError("retry_identity_mismatch")
        else:
            if args.attempt_id == snapshot["active_attempt_id"]:
                if data.get("last_retry", {}).get("attempt_id") == args.attempt_id and data.get("input") == new_input:
                    return {"status": "retry_started", "current_state": snapshot["current_state"]}
                raise ControlError("new_working_attempt_required")
            old = identity(snapshot)
            pending = {"action": "retry", "attempt_id": args.attempt_id, "source": old, "input": new_input}
            data["pending_operation"] = pending
            write_json(root, SESSION, data)
        run_json([str(BSK), "attempt", "start", str(root), SKILL, "--run-id", args.run_id,
                  "--state-visit-id", old["state_visit_id"], "--attempt-id", args.attempt_id,
                  "--reason", "revision-or-evidence-changed", "--idempotency-key", "revision-retry:" + args.attempt_id])
        snapshot = read_state(root, args.run_id, args.attempt_id)
        if load_request(root, args.request_file, complete=False) != new_input:
            raise ControlError("retry_intent_mismatch")
        data["input"] = new_input
        data["last_retry"] = pending
        data.pop("pending_operation")
        write_json(root, SESSION, data)
        return {"status": "retry_started", "current_state": snapshot["current_state"]}

    session(root, args, version)
    snapshot = read_state(root, args.run_id, args.attempt_id)
    if action == "status":
        return {"status": "observed", "current_state": snapshot["current_state"], "identity": identity(snapshot)}
    mapping = mappings[action]
    if snapshot["current_state"] not in {mapping["current_state"], mapping["target_state"]}:
        raise ControlError("action_state_mismatch")
    if snapshot["current_state"] == mapping["target_state"]:
        return recover_ready(root, args, snapshot, mapping)
    prefix = f"humanization/log/attempt-{args.attempt_id}"
    index_ref = prefix + "-evidence.json"
    index = load_request(root, args.request_file, complete=True)
    frozen_path = safe_path(root, index_ref)
    if frozen_path.exists():
        if read_json(root, index_ref) != index:
            raise ControlError("evidence_changed_retry_required")
    else:
        write_json(root, index_ref, index)
    evidence_hash = digest(canonical(index))
    declaration = SkillVerifierDeclaration.from_skill_root(SKILL_ROOT)
    requirements = declaration.verifier_requirements()
    required = [r for r in requirements if r["required"]]
    if not required:
        raise ControlError("required_verifiers_missing")
    registry = declaration.registry()
    source = identity(snapshot)
    request = {**source, "subject": {"type": "revision", "ref": index_ref, "content_hash": evidence_hash},
               "context": {"task_root": str(root), "request_ref": args.request_file, "index": index},
               "evidence": [{"ref": index_ref, "content_hash": evidence_hash, "source_type": "local", "summary": "Frozen revision evidence index"}]}
    submissions = read_json(root, args.submission_file).get("results") if args.submission_file else []
    if not isinstance(submissions, list):
        raise ControlError("submission_list_required")
    packs = {r["id"]: registry.resolve(r["id"], r["version"]).contract_pack() for r in required}
    if any(not isinstance(s, dict) or s.get("pack_id") not in packs for s in submissions):
        raise ControlError("unknown_submission")
    validate_submissions(submissions, index, root, source)
    results, handoffs = [], []
    for requirement in required:
        item_id, version_id = requirement["id"], requirement["version"]
        execution = registry.run_contract(item_id, request, version=version_id, **source,
                                          submissions=[s for s in submissions if s["pack_id"] == item_id])
        payload = execution.to_event_payload()
        if payload.get("protocol") != "bensz-verification-v2" or payload.get("verifier_id") != item_id or payload.get("verifier_version") != version_id:
            raise ControlError("verifier_receipt_invalid")
        if any(payload.get(k) != v for k, v in source.items()) or payload.get("contract_hash") != packs[item_id].contract_hash or payload.get("plan_hash") != packs[item_id].plan_hash:
            raise ControlError("verifier_binding_invalid")
        results.append({**payload, "evidence_hash": evidence_hash, "evidence_refs": [index_ref]})
        handoffs.extend(h.to_dict() for h in execution.report.handoffs)
    check_frozen(root, args.request_file, index)
    log = EventLog(TaskWorkspace.open_existing(root).events)
    _, gate_event = log.record_verification_batch(results, gate={}, requirements=requirements, **source,
                                                 idempotency_key="revision-check:" + evidence_hash + ":" + digest(canonical(submissions)))
    if gate_event is None:
        raise ControlError("gate_missing")
    gate = check_gate(gate_event, required, source, evidence_hash, index_ref)
    base = {"previous_state": snapshot["current_state"], "target_state": mapping["target_state"],
            "current_state": snapshot["current_state"], "required_results": [{"id": r["verifier_id"], "version": r["verifier_version"], "verdict": r["verdict"]} for r in results],
            "gate": {**gate, "event_id": gate_event.event_id}, "evidence_hash": evidence_hash}
    if gate.get("decision") not in {"allow", "allow_with_warnings"}:
        if handoffs:
            handoff_ref = prefix + "-handoffs.json"
            write_json(root, handoff_ref, {"handoffs": handoffs, "evidence_hash": evidence_hash})
            return {**base, "status": "pending_review", "reason_code": "required_review_incomplete", "handoff_ref": handoff_ref,
                    "recovery": "Execute the real handoff, submit bound results, then repeat release with the same identity."}
        return {**base, "status": "blocked", "reason_code": "required_verification_not_passed", "recovery": "Repair the candidate or evidence; retry with a new attempt."}
    if handoffs or any(r["execution_status"] != "completed" or r["verdict"] != "pass" for r in results):
        raise ControlError("required_results_incomplete")
    check_frozen(root, args.request_file, index)
    validate_submissions(submissions, index, root, source)
    target_attempt = args.attempt_id + "-ready"
    if len(target_attempt) > 80:
        target_attempt = "ready-" + digest(args.attempt_id.encode()).removeprefix("sha256:")[:24]
    response = state_command(root, mapping["target_state"], args.run_id, target_attempt, source=source,
                             gate_id=gate_event.event_id, evidence_hash=evidence_hash, evidence_ref=index_ref)
    new_state = check_transition(response, root, mapping["target_state"], args.run_id, target_attempt, source=source, gate_id=gate_event.event_id)
    check_frozen(root, args.request_file, index)
    receipt = {**base, "protocol": PROTOCOL, "action": action, "run_id": args.run_id,
               "attempt_id": target_attempt, "source_attempt_id": args.attempt_id, "status": "ready",
               "current_state": new_state["current_state"], "transition": response, "delivery": index["delivery"]}
    write_json(root, "humanization/log/release.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--task-root", required=True)
    parser.add_argument("--request-file", required=True, help="path relative to task root")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--submission-file", help="bound component results, relative to task root")
    args = parser.parse_args()
    receipt = {"protocol": PROTOCOL, "action": args.action, "run_id": args.run_id, "attempt_id": args.attempt_id,
               "previous_state": None, "target_state": None, "current_state": None,
               "required_results": [], "gate": None, "transition": None}
    try:
        receipt.update(execute(args))
    except Exception as error:
        receipt.update(status="blocked", reason_code=str(error) if isinstance(error, ControlError) else "invalid_input_or_runtime",
                       recovery="Keep the draft; inspect local evidence and the managed runtime. Do not bypass release.")
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if receipt["status"] in {"ready", "already_ready", "initialized", "retry_started", "observed"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
