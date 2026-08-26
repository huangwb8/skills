import json
from datetime import datetime
from pathlib import Path

import pytest

from bensz_skill_kernel import (
    FilesystemStateRegistry,
    StateDefinitionError,
    StateMachine,
    StateTransitionError,
    TaskWorkspace,
    WorkspaceError,
    build_builtin_state_registry,
    workspace_path,
)
from bensz_skill_kernel.cli import main


def test_builtin_state_catalog_is_discoverable():
    registry = build_builtin_state_registry()
    ready = registry.resolve("workspace.ready")
    assert ready.kind == "system"
    assert "input" in ready.instructions
    assert {item.id for item in registry.definitions()} == {"workspace.closed", "workspace.ready"}
    machine = StateMachine(registry)
    assert machine.snapshot()["state"] == "workspace.ready"
    machine.transition("workspace.closed")
    with pytest.raises(StateTransitionError):
        machine.transition("workspace.ready")


def test_custom_state_definition_supports_metadata_and_scripts(tmp_path: Path):
    state = tmp_path / "custom" / "STATE.md"
    state.parent.mkdir()
    state.write_text(
        "---\n"
        "id: demo.review\n"
        "version: 2.0.0\n"
        "kind: skill\n"
        "entry_conditions: input.ready, snapshot.present\n"
        "invariants: no-secrets\n"
        "next_states: demo.done\n"
        "---\n\n# Review\n",
        encoding="utf-8",
    )
    definition = FilesystemStateRegistry(tmp_path).resolve("demo.review")
    assert definition.entry_conditions == ("input.ready", "snapshot.present")
    assert definition.transitions == ("demo.done",)
    assert definition.invariants == ("no-secrets",)


def test_workspace_is_locked_and_skill_paths_are_scoped(tmp_path: Path):
    workspace = TaskWorkspace.open(tmp_path, description="引用 核验", now=datetime(2026, 8, 26, 20, 20))
    paths = workspace.paths("validate-md-ref")
    assert workspace.manifest()["state"] == "workspace.ready"
    assert paths.path("input").is_dir()
    assert paths.events == workspace.task_root / "log" / "events.ndjson"
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
    assert payload["manifest"]["state"] == "workspace.ready"
    assert main(["workspace", "path", task_root, "demo-skill", "output"]) == 0
    path_payload = json.loads(capsys.readouterr().out)
    assert path_payload["path"].endswith("demo-skill/output")
    assert main(["state", "describe", "workspace.ready"]) == 0
    state_payload = json.loads(capsys.readouterr().out)
    assert state_payload["id"] == "workspace.ready"


def test_malformed_state_definition_is_rejected(tmp_path: Path):
    (tmp_path / "STATE.md").write_text("---\nid: bad id\n---\n", encoding="utf-8")
    with pytest.raises(StateDefinitionError):
        FilesystemStateRegistry(tmp_path)
