"""Root-level smoke tests for the public API of packages/bensz-skill-kernel."""

import shutil
import subprocess
import sys
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


def test_pypi_publish_helper_has_safe_explicit_upload_boundary() -> None:
    script = Path(__file__).with_name("publish_bsk_pypi.py")
    system_python = shutil.which("python3") or sys.executable
    completed = subprocess.run(
        [system_python, str(script), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "--upload" in completed.stdout
    assert "默认只构建和检查" in completed.stdout
