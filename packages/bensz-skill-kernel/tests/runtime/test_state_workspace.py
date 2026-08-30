import json
from datetime import datetime
from pathlib import Path

import pytest

from bensz_skill_kernel import (
    FilesystemStateRegistry,
    SkillStateDeclaration,
    StateDefinitionError,
    StateMachine,
    StateTransitionError,
    TaskWorkspace,
    WorkspaceError,
    build_builtin_state_registry,
    workspace_path,
    validate_state_id,
)
from bensz_skill_kernel.cli import main


def test_builtin_state_catalog_is_discoverable():
    registry = build_builtin_state_registry()
    ready = registry.resolve("bensz.workspace.ready")
    assert registry.resolve("workspace.ready").id == "bensz.workspace.ready"
    assert ready.kind == "system"
    assert "input" in ready.instructions
    assert {item.id for item in registry.definitions()} == {
        "bensz.workspace.closed", "bensz.workspace.ready",
        "bensz.runtime.planned", "bensz.runtime.active", "bensz.runtime.waiting",
        "bensz.runtime.checking", "bensz.runtime.delivering", "bensz.runtime.completed",
        "bensz.runtime.failed", "bensz.runtime.cancelled",
    }
    assert registry.resolve("bensz.runtime.active").kind == "system"
    assert registry.resolve("runtime.active").id == "bensz.runtime.active"
    machine = StateMachine(registry)
    assert machine.snapshot()["state"] == "bensz.workspace.ready"
    machine.transition("bensz.workspace.closed")
    with pytest.raises(StateTransitionError):
        machine.transition("bensz.workspace.ready")


def test_lifecycle_state_directories_match_runtime_transition_table() -> None:
    from bensz_skill_kernel.runtime import ALLOWED_TRANSITIONS

    registry = build_builtin_state_registry()
    for short_id, targets in ALLOWED_TRANSITIONS.items():
        definition = registry.resolve(f"bensz.runtime.{short_id}")
        assert set(definition.transitions) == {f"bensz.runtime.{target}" for target in targets}


def test_builtin_state_index_is_flat_and_exposes_attributes() -> None:
    root = Path(__file__).parents[2] / "src" / "bensz_skill_kernel" / "states"
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    assert index["protocol"] == "bensz-pack-index-v1"
    assert index["package_kind"] == "state"
    assert all("/" not in item["directory"] for item in index["entries"])
    assert all(item["classification"] == "atomic" for item in index["entries"])
    registry = build_builtin_state_registry()
    active = registry.resolve("bensz.runtime.active")
    assert active.classification == "atomic"
    assert "lifecycle" in active.tags
    assert Path(active.source).parent.parent == root
    contract = Path(active.source).read_text(encoding="utf-8")
    assert "kind:" not in contract
    assert "aliases:" not in contract


def test_custom_state_definition_supports_metadata_and_scripts(tmp_path: Path):
    state = tmp_path / "custom" / "STATE.md"
    state.parent.mkdir()
    state.write_text(
        "---\n"
        "id: test.demo.review\n"
        "version: 2.0.0\n"
        "kind: skill\n"
        "entry_conditions: test.input.ready, test.snapshot.present\n"
        "invariants: no-secrets\n"
        "next_states: test.demo.done\n"
        "---\n\n# Review\n",
        encoding="utf-8",
    )
    definition = FilesystemStateRegistry(tmp_path).resolve("test.demo.review")
    assert definition.entry_conditions == ("test.input.ready", "test.snapshot.present")
    assert definition.transitions == ("test.demo.done",)
    assert definition.invariants == ("no-secrets",)


def test_workspace_is_locked_and_skill_paths_are_scoped(tmp_path: Path):
    workspace = TaskWorkspace.open(tmp_path, description="引用 核验", now=datetime(2026, 8, 26, 20, 20))
    paths = workspace.paths("validate-md-ref")
    assert workspace.manifest()["state"] == "bensz.workspace.ready"
    assert paths.path("input").is_dir()
    assert paths.events == workspace.task_root / "log" / "events.ndjson"
    assert (workspace.task_root / "shared" / "input").is_dir()
    assert workspace.read_meta_state("validate-md-ref")["current_state"] == "bensz.workspace.ready"
    assert workspace_path(tmp_path, skill="validate-md-ref", kind="log", task_root=workspace.task_root) == paths.path("log")

    reopened = TaskWorkspace.open(tmp_path, task_root=workspace.task_root)
    assert reopened.task_root == workspace.task_root
    with pytest.raises(WorkspaceError):
        workspace.paths("../escape")
    with pytest.raises(WorkspaceError):
        paths.path("state")
    with pytest.raises(WorkspaceError):
        TaskWorkspace.open_existing(tmp_path / "outside")


def test_workspace_cli_returns_machine_readable_paths(tmp_path: Path, capsys):
    assert main(["workspace", "init", str(tmp_path), "--description", "demo"]) == 0
    payload = json.loads(capsys.readouterr().out)
    task_root = payload["task_root"]
    assert payload["manifest"]["state"] == "bensz.workspace.ready"
    assert main(["workspace", "path", task_root, "demo-skill", "output"]) == 0
    path_payload = json.loads(capsys.readouterr().out)
    assert path_payload["path"].endswith("demo-skill/output")
    assert main(["state", "describe", "bensz.workspace.ready"]) == 0
    state_payload = json.loads(capsys.readouterr().out)
    assert state_payload["id"] == "bensz.workspace.ready"


def test_malformed_state_definition_is_rejected(tmp_path: Path):
    (tmp_path / "STATE.md").write_text("---\nid: bad id\n---\n", encoding="utf-8")
    with pytest.raises(StateDefinitionError):
        FilesystemStateRegistry(tmp_path)


def test_skill_declaration_combines_system_and_skill_state_packages(tmp_path: Path):
    skill = tmp_path / "demo-skill"
    state = skill / "states" / "collect" / "STATE.md"
    state.parent.mkdir(parents=True)
    (skill / "state-machine.json").write_text(
        '{"protocol":"bensz-skill-state-v1","initial_state":"bensz.workspace.ready",'
        '"state_roots":["states"],"states":["test.demo.collect"]}\n',
        encoding="utf-8",
    )
    state.write_text(
        "---\n"
        "id: test.demo.collect\n"
        "version: 1.0.0\n"
        "kind: skill\n"
        "entry_conditions: bensz.workspace.ready\n"
        "transitions: bensz.workspace.closed\n"
        "---\n\n# Collect\n",
        encoding="utf-8",
    )
    declaration = SkillStateDeclaration.from_skill_root(skill)
    machine = StateMachine(declaration.registry(), declaration.initial_state)
    assert machine.can_transition("test.demo.collect")
    assert declaration.registry().resolve("bensz.workspace.ready").kind == "system"


def test_skill_declaration_reads_runtime_config_yaml_and_rejects_undeclared_state(tmp_path: Path):
    skill = tmp_path / "demo-skill"
    state = skill / "references" / "states" / "collect" / "STATE.md"
    state.parent.mkdir(parents=True)
    (skill / "config.yaml").write_text(
        "runtime:\n"
        "  state_roots: [references/states]\n"
        "  initial_state: bensz.workspace.ready\n"
        "  states: [test.demo.collect]\n",
        encoding="utf-8",
    )
    state.write_text(
        "---\n"
        "id: test.demo.collect\n"
        "version: 1.0.0\n"
        "kind: skill\n"
        "entry_conditions: bensz.workspace.ready\n"
        "---\n",
        encoding="utf-8",
    )
    declaration = SkillStateDeclaration.from_skill_root(skill)
    assert declaration.source.name == "config.yaml"
    assert declaration.state_roots == (state.parents[1],)
    assert declaration.registry().resolve("test.demo.collect").id == "test.demo.collect"


def test_projection_keeps_effect_status_as_an_orthogonal_field(tmp_path: Path):
    from bensz_skill_kernel import EventLog

    log = EventLog(tmp_path / "events.ndjson")
    log.append("effect.updated", payload={"effect_status": "unknown"})
    assert log.projection()["effect_status"] == "unknown"


def test_state_transition_cli_executes_helper_and_persists_snapshot(tmp_path: Path, capsys):
    workspace = TaskWorkspace.open(tmp_path, description="demo")
    skill = tmp_path / "demo-skill"
    state = skill / "states" / "collect" / "STATE.md"
    script = state.parent / "check.py"
    state.parent.mkdir(parents=True)
    (skill / "state-machine.json").write_text(
        '{"protocol":"bensz-skill-state-v1","initial_state":"bensz.workspace.ready",'
        '"state_roots":["states"],"states":["test.demo.collect"]}\n',
        encoding="utf-8",
    )
    state.write_text(
        "---\n"
        "id: test.demo.collect\n"
        "version: 1.0.0\n"
        "kind: skill\n"
        "entry_conditions: bensz.workspace.ready\n"
        "entrypoint: check.py\n"
        "---\n\n# Collect\n",
        encoding="utf-8",
    )
    script.write_text(
        "import json, sys\n"
        "payload = json.load(sys.stdin)\n"
        "print(json.dumps({'verdict': 'pass', 'facts': {'operation': payload['request']['operation']}, 'evidence_refs': ['check.py']}))\n",
        encoding="utf-8",
    )
    assert main([
        "state", "transition", str(workspace.task_root), "demo-skill", "test.demo.collect",
        "--skill-root", str(skill), "--context-json", "{\"document\": \"README.md\"}",
    ]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "transitioned"
    assert payload["execution"]["verdict"] == "pass"
    assert workspace.read_meta_state("demo-skill")["current_state"] == "test.demo.collect"
    projection = __import__("bensz_skill_kernel").EventLog(workspace.events).projection()
    assert projection["skill_states"]["demo-skill"]["state"] == "test.demo.collect"
    assert projection["skill_state_transitions"][-1]["from_state"] == "bensz.workspace.ready"


def test_state_transition_cli_keeps_snapshot_when_helper_fails(tmp_path: Path, capsys):
    workspace = TaskWorkspace.open(tmp_path, description="demo")
    skill = tmp_path / "demo-skill"
    state = skill / "states" / "collect" / "STATE.md"
    script = state.parent / "check.py"
    state.parent.mkdir(parents=True)
    (skill / "state-machine.json").write_text(
        '{"protocol":"bensz-skill-state-v1","states":["test.demo.collect"]}\n', encoding="utf-8"
    )
    state.write_text(
        "---\nid: test.demo.collect\nentry_conditions: bensz.workspace.ready\nentrypoint: check.py\n---\n\n# Collect\n",
        encoding="utf-8",
    )
    script.write_text("import json\nprint(json.dumps({'verdict': 'fail'}))\n", encoding="utf-8")
    assert main(["state", "transition", str(workspace.task_root), "demo-skill", "test.demo.collect", "--skill-root", str(skill)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "rejected"
    assert workspace.read_meta_state("demo-skill")["current_state"] == "bensz.workspace.ready"


def test_state_transition_cli_enforces_verifier_result_invariant(tmp_path: Path, capsys):
    workspace = TaskWorkspace.open(tmp_path, description="demo")
    skill = tmp_path / "demo-skill"
    for name in ("checking", "reported"):
        (skill / "states" / name).mkdir(parents=True)
    (skill / "config.yaml").write_text(
        "runtime:\n"
        "  state_roots: [states]\n"
        "  initial_state: bensz.workspace.ready\n"
        "  states: [test.demo.checking, test.demo.reported]\n",
        encoding="utf-8",
    )
    (skill / "states" / "checking" / "STATE.md").write_text(
        "---\n"
        "id: test.demo.checking\n"
        "entry_conditions: bensz.workspace.ready\n"
        "invariants: verifier-result-recorded\n"
        "transitions: test.demo.reported\n"
        "---\n\n# Checking\n",
        encoding="utf-8",
    )
    (skill / "states" / "reported" / "STATE.md").write_text(
        "---\n"
        "id: test.demo.reported\n"
        "entry_conditions: test.demo.checking\n"
        "transitions: bensz.workspace.closed\n"
        "---\n\n# Reported\n",
        encoding="utf-8",
    )

    assert main([
        "state", "transition", str(workspace.task_root), "demo-skill", "test.demo.checking",
        "--skill-root", str(skill),
    ]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "transitioned"

    assert main([
        "state", "transition", str(workspace.task_root), "demo-skill", "test.demo.reported",
        "--skill-root", str(skill),
    ]) == 0
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["status"] == "rejected"
    assert "verifier-result-recorded" in rejected["reason"]
    assert workspace.read_meta_state("demo-skill")["current_state"] == "test.demo.checking"

    from bensz_skill_kernel import EventLog

    log = EventLog(workspace.events)
    log.record_verification(
        {"verifier_id": "test.demo.links", "verdict": "pass", "execution_status": "completed"},
        {"decision": "allow", "result_refs": ["test.demo.links@1.0.0"]},
    )
    assert main([
        "state", "transition", str(workspace.task_root), "demo-skill", "test.demo.reported",
        "--skill-root", str(skill),
    ]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "transitioned"


def test_verifier_invariant_rejects_ambiguous_historical_run_identity():
    from bensz_skill_kernel import EventLog, StateDefinition, check_state_invariants

    definition = StateDefinition(id="test.demo.checking", version="1.0.0", invariants=("verifier-result-recorded",))
    log = EventLog(Path(__import__("tempfile").mkdtemp()) / "events.ndjson")
    log.record_verification(
        {"verifier_id": "test.demo.links", "verifier_version": "1.0.0", "verdict": "pass", "execution_status": "completed"},
        {"decision": "allow", "result_refs": ["test.demo.links@1.0.0"]},
        run_id="old-run",
    )
    failures = check_state_invariants(definition, log.read())
    assert any("run_id/attempt_id required" in item for item in failures)
    assert check_state_invariants(definition, log.read(), context={"run_id": "new-run", "attempt_id": "default"})


def test_verifier_invariant_rejects_half_bound_identity():
    from bensz_skill_kernel import EventLog, StateDefinition, check_state_invariants

    definition = StateDefinition(id="test.demo.checking", version="1.0.0", invariants=("verifier-result-recorded",))
    log = EventLog(Path(__import__("tempfile").mkdtemp()) / "events.ndjson")
    log.record_verification(
        {"verifier_id": "test.demo.links", "verifier_version": "1.0.0", "verdict": "pass", "execution_status": "completed"},
        {"decision": "allow", "result_refs": ["test.demo.links@1.0.0"]},
        run_id="run-1", attempt_id="attempt-1",
    )
    failures = check_state_invariants(definition, log.read(), context={"attempt_id": "attempt-1"})
    assert any("both must be provided" in item for item in failures)


def test_state_id_requires_owner_machine_and_state() -> None:
    assert validate_state_id("bensz.workspace.ready") == "bensz.workspace.ready"
    assert validate_state_id("org.example.deploy.awaiting-approval") == "org.example.deploy.awaiting-approval"

    for invalid in ("workspace.ready", "bensz.workspace", "bensz.Workspace.ready", "bensz.workspace.input_ready", "bensz.workspace.ready.v1"):
        with pytest.raises(ValueError):
            validate_state_id(invalid)


def test_state_registry_resolves_legacy_alias_to_canonical_id(tmp_path: Path) -> None:
    state = tmp_path / "ready" / "STATE.md"
    state.parent.mkdir()
    state.write_text(
        "---\n"
        "id: bensz.demo.ready\n"
        "version: 1.0.0\n"
        "aliases: demo.ready\n"
        "transitions: bensz.demo.done\n"
        "---\n",
        encoding="utf-8",
    )
    registry = FilesystemStateRegistry(tmp_path)
    assert registry.resolve("demo.ready").id == "bensz.demo.ready"
    assert registry.resolve("demo.ready").aliases == ("demo.ready",)


def test_state_graph_references_require_canonical_ids(tmp_path: Path) -> None:
    state = tmp_path / "checking" / "STATE.md"
    state.parent.mkdir()
    state.write_text(
        "---\nid: bensz.demo.checking\nentry_conditions: workspace.ready\n---\n",
        encoding="utf-8",
    )
    with pytest.raises(StateDefinitionError, match="canonical state graph reference"):
        FilesystemStateRegistry(tmp_path)


def test_state_machine_accepts_alias_and_persists_canonical_state(tmp_path: Path) -> None:
    for slug, state_id, aliases, transitions, entry_conditions in (
        ("ready", "bensz.demo.ready", "demo.ready", "bensz.demo.done", ""),
        ("done", "bensz.demo.done", "demo.done", "", "bensz.demo.ready"),
    ):
        state = tmp_path / slug / "STATE.md"
        state.parent.mkdir()
        state.write_text(
            f"---\nid: {state_id}\nversion: 1.0.0\naliases: {aliases}\n"
            f"transitions: {transitions}\nentry_conditions: {entry_conditions}\n---\n",
            encoding="utf-8",
        )
    machine = StateMachine(FilesystemStateRegistry(tmp_path), "demo.ready")
    assert machine.can_transition("demo.done")
    machine.transition("demo.done")
    assert machine.snapshot()["state"] == "bensz.demo.done"


def test_cli_resumes_legacy_snapshot_and_persists_canonical_state(tmp_path: Path, capsys) -> None:
    workspace = TaskWorkspace.open(tmp_path, description="legacy")
    workspace.write_meta_state(
        "demo-skill",
        {
            "protocol": "bensz-meta-state-v1",
            "skill": "demo-skill",
            "current_state": "workspace.ready",
            "state_version": "1.0.0",
        },
    )
    skill = tmp_path / "demo-skill"
    state = skill / "states" / "collect" / "STATE.md"
    state.parent.mkdir(parents=True)
    (skill / "state-machine.json").write_text(
        '{"protocol":"bensz-skill-state-v1","initial_state":"workspace.ready",'
        '"state_roots":["states"],"states":["demo.collect"]}\n',
        encoding="utf-8",
    )
    state.write_text(
        "---\nid: test.demo.collect\naliases: demo.collect\n"
        "entry_conditions: bensz.workspace.ready\n---\n",
        encoding="utf-8",
    )
    declaration = SkillStateDeclaration.from_skill_root(skill)
    assert declaration.initial_state == "bensz.workspace.ready"
    assert declaration.states == ("test.demo.collect",)

    assert main([
        "state", "transition", str(workspace.task_root), "demo-skill", "demo.collect",
        "--skill-root", str(skill),
    ]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "transitioned"
    assert payload["current_state"] == "bensz.workspace.ready"
    assert payload["target_state"] == "test.demo.collect"
    assert workspace.read_meta_state("demo-skill")["current_state"] == "test.demo.collect"
