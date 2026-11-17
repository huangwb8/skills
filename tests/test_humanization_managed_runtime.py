"""Managed runtime boundary; Windows layout is simulated on non-Windows hosts."""

import importlib.metadata
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "skills/alpha/humanization/scripts"
sys.path.insert(0, str(SCRIPTS))
from revision_evidence import ControlError


@pytest.fixture(params=["win32", "linux", "darwin"])
def runtime(request, tmp_path, monkeypatch):
    home = tmp_path / "managed home & 空间 %literal%!"
    windows = request.param == "win32"
    python = home / ".bensz-skills/envs/benszapi" / ("python.exe" if windows else "bin/python")
    launcher = home / ".bensz-skills/bin" / ("bsk.cmd" if windows else "bsk")
    installer = home / ".codex/skills/install-bensz-skills/scripts/install.py"
    for path in (python, launcher, installer):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    # Select the foreign layout without changing os.name/pathlib's host semantics.
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    with monkeypatch.context() as patch:
        patch.setattr(sys, "platform", request.param)
        spec = importlib.util.spec_from_file_location("platform_revision_control", SCRIPTS / "control.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    monkeypatch.setattr(sys, "executable", str(python))
    version = importlib.metadata.version("bensz-skill-kernel")
    calls = []
    receipt = {"ready": True, "last_result": "success", "packages": {"bensz-skill-kernel": version}}

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        payload = receipt if "--force-runtime-update" in argv else {
            "protocol": "bensz-kernel-diagnostics-v1", "kernel_version": version,
        }
        return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")

    monkeypatch.setattr(module.subprocess, "run", run)
    return module, python, launcher, installer, version, calls, receipt, windows


@pytest.mark.parametrize("update", [False, True])
def test_native_managed_layout_and_version_confirmation(runtime, update):
    module, python, launcher, installer, version, calls, _, windows = runtime
    assert module.managed_runtime(update=update) == version
    if update:
        assert calls[0][0] == [str(python), str(installer), "--force-runtime-update"]
    command, options = calls[-1]
    if windows:
        # No cmd.exe expansion of spaces, Unicode, %, ! or & in user paths.
        assert command[:5] == [str(python), "-I", "-B", "-Xutf8", "-c"]
        assert "bensz_skill_kernel.runtime import main" in command[5]
        assert command[6:] == ["diagnostics"]
    else:
        assert command == [str(launcher), "diagnostics"]
    assert options.get("shell", False) is False


@pytest.mark.parametrize("problem", ["other_python", "missing_python", "missing_launcher"])
def test_unmanaged_or_incomplete_runtime_still_rejected(runtime, monkeypatch, problem):
    module, python, launcher, _, _, calls, _, _ = runtime
    if problem == "other_python":
        monkeypatch.setattr(sys, "executable", str(python.parent / "other-python"))
    elif problem == "missing_python":
        python.unlink()
    else:
        launcher.unlink()
    with pytest.raises(ControlError, match="^managed_python_required$"):
        module.managed_runtime(update=False)
    assert not calls


@pytest.mark.parametrize("problem", ["not_ready", "update_failed", "version_drift"])
def test_unconfirmed_update_and_version_drift_still_rejected(runtime, problem):
    module, _, _, _, _, _, receipt, _ = runtime
    if problem == "not_ready":
        receipt["ready"] = False
    elif problem == "update_failed":
        receipt["last_result"] = "failed"
    else:
        receipt["packages"]["bensz-skill-kernel"] = "0.0.0"
    expected = "runtime_version_mismatch" if problem == "version_drift" else "runtime_update_unconfirmed"
    with pytest.raises(ControlError, match=f"^{expected}$"):
        module.managed_runtime(update=True)


def test_windows_bsk_dispatch_with_real_kernel(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("real_revision_control", SCRIPTS / "control.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "MANAGED_PYTHON", Path(sys.executable))
    monkeypatch.setattr(module, "BSK", tmp_path / "unused launcher & 空间/bsk.cmd")
    assert module.run_json([str(module.BSK), "diagnostics"])["kernel_version"] == importlib.metadata.version("bensz-skill-kernel")
    project = tmp_path / "项目 with spaces & %literal%!"
    project.mkdir()
    (project / "bensz_skill_kernel.py").write_text("raise RuntimeError('project module must not load')\n", encoding="utf-8")
    monkeypatch.chdir(project)
    task = project / ".bensz-api/task-windows-dispatch"
    result = module.run_json([str(module.BSK), "workspace", "init", str(project), "--task-root", str(task)])
    assert result["status"] == "ready"
    assert task.is_dir()
