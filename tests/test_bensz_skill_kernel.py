"""Root-level smoke tests for the public API of packages/bensz-skill-kernel."""

from pathlib import Path

from bensz_skill_kernel import EventLog, reduce_events


def test_package_public_api_can_create_and_replay_a_lifecycle(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "events.ndjson")
    log.append("task.created", payload={"state": "planned"})
    log.transition("active")

    projection = reduce_events(log.read())

    assert projection["current_state"] == "active"
    assert projection["event_count"] == 2


def test_package_public_api_persists_a_rebuildable_projection(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "events.ndjson")
    log.append("task.created", payload={"state": "planned"})

    state_path = tmp_path / "state.json"
    projection = log.rebuild(state_path)

    assert state_path.is_file()
    assert projection["current_state"] == "planned"
