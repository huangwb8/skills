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


def test_stdio_does_not_write_bytecode_into_pack(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv('PYTHONPYCACHEPREFIX', raising=False)
    monkeypatch.delenv('PYTHONDONTWRITEBYTECODE', raising=False)
    (tmp_path / 'helper.py').write_text('value = 1\n', encoding='utf-8')
    (tmp_path / 'check.py').write_text(
        'import helper, json\nprint(json.dumps({"value": helper.value}))\n', encoding='utf-8')
    assert run_stdio(tmp_path, 'check.py', {}, timeout=5).status == 'completed'
    assert not (tmp_path / '__pycache__').exists()


def test_stdio_propagates_explicit_cache_prefix(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv('PYTHONPYCACHEPREFIX', '.bensz-api/explicit-cache')
    (tmp_path / 'check.py').write_text(
        'import os, json\nprint(json.dumps({"prefix": os.getenv("PYTHONPYCACHEPREFIX")}))\n', encoding='utf-8')
    assert run_stdio(tmp_path, 'check.py', {}, timeout=5).value['prefix'] == '.bensz-api/explicit-cache'


def test_shared_entrypoint_validation_rejects_path_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="inside its directory"):
        resolve_entrypoint(tmp_path, "../outside.py")


def test_stdio_denies_untrusted_execution_and_rejects_missing_entrypoint(tmp_path: Path) -> None:
    denied = run_stdio(tmp_path, "missing.py", {"request": {}}, timeout=1, trusted=False)
    assert denied.status == "denied"

    missing = run_stdio(tmp_path, "missing.py", {"request": {}}, timeout=1)
    assert missing.status == "error"


def test_stdio_normalizes_invalid_input_and_input_limit(tmp_path: Path) -> None:
    script = tmp_path / "check.py"
    script.write_text("import json, sys\njson.dump({'verdict': 'pass'}, sys.stdout)\n", encoding="utf-8")

    unserialisable = run_stdio(tmp_path, "check.py", {"value": object()}, timeout=1)
    assert unserialisable.status == "invalid_input"
    oversized = run_stdio(tmp_path, "check.py", {"value": "x" * 100}, timeout=1, max_input_bytes=10)
    assert oversized.status == "input_too_large"


def test_stdio_reports_invalid_json_and_nonzero_exit(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.py"
    invalid.write_text("print('not-json')\n", encoding="utf-8")
    result = run_stdio(tmp_path, "invalid.py", {}, timeout=1)
    assert result.status == "invalid_json"

    failing = tmp_path / "failing.py"
    failing.write_text("raise SystemExit(3)\n", encoding="utf-8")
    result = run_stdio(tmp_path, "failing.py", {}, timeout=1)
    assert result.status == "error"
    assert "code 3" in result.detail


def test_stdio_times_out_and_limits_stdout(tmp_path: Path) -> None:
    slow = tmp_path / "slow.py"
    slow.write_text("import time\ntime.sleep(2)\n", encoding="utf-8")
    result = run_stdio(tmp_path, "slow.py", {}, timeout=1)
    assert result.status == "timed_out"

    noisy = tmp_path / "noisy.py"
    noisy.write_text("print('x' * 100)\n", encoding="utf-8")
    result = run_stdio(tmp_path, "noisy.py", {}, timeout=1, max_output_bytes=10)
    assert result.status == "output_too_large"
