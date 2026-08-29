import json
from pathlib import Path

import pytest

from bensz_skill_kernel.packs import load_pack_entries, resolve_entrypoint, run_stdio


def test_shared_loader_validates_index_and_returns_contract_paths(tmp_path: Path) -> None:
    package = tmp_path / "demo"
    package.mkdir()
    (package / "STATE.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "index.json").write_text(
        json.dumps(
            {
                "protocol": "bensz-pack-index-v1",
                "package_kind": "state",
                "entries": [{"directory": "demo", "id": "test.demo.ready", "version": "1.0.0"}],
            }
        ),
        encoding="utf-8",
    )

    entries = load_pack_entries(tmp_path, package_kind="state", contract_name="STATE.md")

    assert entries[0][0] == (package / "STATE.md").resolve()
    assert entries[0][1]["id"] == "test.demo.ready"


def test_shared_loader_rejects_stale_index_entries(tmp_path: Path) -> None:
    (tmp_path / "index.json").write_text(
        '{"protocol":"bensz-pack-index-v1","package_kind":"verifier","entries":[]}',
        encoding="utf-8",
    )
    package = tmp_path / "extra"
    package.mkdir()
    (package / "VERIFIER.md").write_text("# Extra\n", encoding="utf-8")

    with pytest.raises(ValueError, match="index/directory mismatch"):
        load_pack_entries(tmp_path, package_kind="verifier", contract_name="VERIFIER.md")


def test_shared_stdio_executor_runs_from_pack_root(tmp_path: Path) -> None:
    script = tmp_path / "check.py"
    script.write_text(
        "import json, pathlib, sys\n"
        "json.dump({'verdict': 'pass', 'cwd': pathlib.Path.cwd().name}, sys.stdout)\n",
        encoding="utf-8",
    )

    result = run_stdio(tmp_path, "check.py", {"request": {}}, timeout=5)

    assert result.status == "completed"
    assert result.value == {"verdict": "pass", "cwd": tmp_path.name}


def test_shared_entrypoint_validation_rejects_path_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="inside its directory"):
        resolve_entrypoint(tmp_path, "../outside.py")
