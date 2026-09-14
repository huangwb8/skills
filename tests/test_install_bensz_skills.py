import ast
import importlib.util
import json
import os
import subprocess
import sys
import time
import tomllib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


install = load_module(
    "install_bensz_skills",
    "skills/alpha/install-bensz-skills/scripts/install.py",
)
bootstrap = load_module(
    "bootstrap_install",
    "skills/alpha/install-bensz-skills/scripts/bootstrap_install.py",
)
updater = load_module(
    "update_remote_skills",
    "skills/alpha/install-bensz-skills/scripts/update_remote_skills.py",
)
managed_runtime = load_module(
    "managed_runtime_under_test",
    "skills/alpha/install-bensz-skills/scripts/managed_runtime.py",
)


def test_python_support_boundaries_match_project_contract():
    pyproject = tomllib.loads(
        (ROOT / "packages/bensz-skill-kernel/pyproject.toml").read_text(
            encoding="utf-8"
        )
    )

    assert install.MIN_PYTHON == (3, 11)
    assert bootstrap.MIN_PYTHON == (3, 8)
    assert pyproject["project"]["requires-python"] == ">=3.11"


def test_local_installer_rejects_python_below_311(monkeypatch):
    monkeypatch.setattr(install.sys, "version_info", (3, 10, 14))

    with pytest.raises(SystemExit, match=r"requires Python 3\.11\+"):
        install.ensure_python()


def test_bootstrap_keeps_python_38_compatible_syntax_and_runtime_gate(monkeypatch):
    source = (
        ROOT / "skills/alpha/install-bensz-skills/scripts/bootstrap_install.py"
    ).read_text(encoding="utf-8")
    ast.parse(source, feature_version=(3, 8))

    monkeypatch.setattr(bootstrap.sys, "version_info", (3, 8, 0))
    bootstrap.ensure_python("en")

    monkeypatch.setattr(bootstrap.sys, "version_info", (3, 7, 17))
    with pytest.raises(SystemExit, match=r"use Python 3\.8 or newer"):
        bootstrap.ensure_python("en")

    parser = bootstrap.build_parser()
    assert parser.parse_args(["--ensure-runtime"]).ensure_runtime is True
    assert parser.parse_args(["--runtime-status"]).runtime_status is True


def make_skill(root: Path, name: str, body: str = "content") -> Path:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: %s\ncategory: normal\n---\n%s\n" % (name, body),
        encoding="utf-8",
    )
    return skill


def test_default_source_prefers_alpha_and_does_not_implicitly_use_pipelines(tmp_path, monkeypatch):
    # Arrange: both the historical and canonical layouts exist.
    make_skill(tmp_path / "skills" / "alpha", "canonical")
    make_skill(tmp_path / "pipelines" / "skills" / "alpha", "historical")
    monkeypatch.chdir(tmp_path)

    # Act
    detected = install._detect_default_source_roots(Path("/system/install.py"))

    # Assert
    assert detected == [(tmp_path / "skills" / "alpha").resolve()]


def test_default_source_detects_alpha_from_nested_project_directory(tmp_path, monkeypatch):
    # Arrange: the system-installed installer is invoked from a project subdirectory.
    alpha_root = tmp_path / "skills" / "alpha"
    make_skill(alpha_root, "canonical")
    nested_dir = tmp_path / "packages" / "demo"
    nested_dir.mkdir(parents=True)
    monkeypatch.chdir(nested_dir)

    # Act
    detected = install._detect_default_source_roots(Path("/system/install.py"))

    # Assert
    assert detected == [alpha_root.resolve()]


def test_default_source_detects_alpha_when_cwd_is_inside_alpha(tmp_path, monkeypatch):
    # Arrange: an agent may run the system installer while focused on ./skills/alpha.
    alpha_root = tmp_path / "skills" / "alpha"
    make_skill(alpha_root, "canonical")
    nested_dir = alpha_root / "canonical"
    monkeypatch.chdir(nested_dir)

    # Act
    detected = install._detect_default_source_roots(Path("/system/install.py"))

    # Assert
    assert detected == [alpha_root.resolve()]


def test_remote_general_source_uses_canonical_alpha_path():
    # Both installation entry points must keep the production channel aligned.
    config_path = ROOT / "skills/alpha/install-bensz-skills/config.yaml"
    config = install._load_config(config_path)
    local_general = next(
        source
        for source in config.get("remote_sources", [])
        if source["id"] == "general"
    )
    bootstrap_general = next(
        source for source in bootstrap.DEFAULT_SOURCES if source["id"] == "general"
    )

    assert local_general["skills_path"] == "skills/alpha"
    assert bootstrap_general["skills_path"] == "skills/alpha"
    assert config["skill_info"]["version"] == bootstrap.FALLBACK_CONFIG_VERSION


def test_remote_updater_compares_versions_and_parses_sources(tmp_path):
    assert updater.parse_version("v1.2.0") == (1, 2, 0)
    assert updater.version_is_newer((1, 2), (1, 1, 9))
    assert not updater.version_is_newer((1, 2), (1, 2, 1))

    config = tmp_path / "config.yaml"
    config.write_text(
        "remote_sources:\n"
        "  - id: general\n"
        "    name: General\n"
        "    url: https://github.com/huangwb8/skills\n"
        "    branch: main\n"
        "    skills_path: skills/alpha\n",
        encoding="utf-8",
    )
    assert updater.load_sources(config)[0]["id"] == "general"


def test_local_manifest_exposes_shared_core_contract(tmp_path):
    skill_dir = make_skill(tmp_path / "source", "demo")
    target = install.Target("codex", tmp_path / "dest", tmp_path / "legacy")
    info = install.SkillInfo(
        name="demo",
        src=skill_dir,
        dest=target.root / "demo",
        md5="abc123",
        installed=True,
        reason="updated",
    )
    report = install.InstallReport(
        target_label=target.label,
        target_root=target.root,
        installed_skills=[info],
        skipped_skills=[],
    )

    manifest = report.to_manifest_dict(source="local:test")

    assert manifest["schema_version"] == 1
    assert manifest["source"] == "local:test"
    assert manifest["target"] == "codex"
    assert manifest["target_root"] == str(target.root)
    assert manifest["skills"][0]["name"] == "demo"
    assert manifest["skills"][0]["md5"] == "abc123"
    assert manifest["skills"][0]["status"] == "installed"
    assert manifest["skills"][0]["reason"] == "updated"


def test_bootstrap_skill_manifest_uses_same_core_fields(tmp_path):
    skill_dir = make_skill(tmp_path / "source", "demo")
    target = bootstrap.Target("claude", tmp_path / "dest", tmp_path / "legacy")

    bootstrap.save_skill_manifest(skill_dir, "abc123", "remote:test", target)
    data = json.loads((skill_dir / ".skill-manifest.claude.json").read_text(encoding="utf-8"))

    assert data["schema_version"] == 1
    assert data["source"] == "remote:test"
    assert data["target"] == "claude"
    assert data["target_root"] == str(target.root)
    assert data["skills"][0] == {
        "name": "demo", "md5": "abc123", "status": "installed", "reason": ""
    }


def test_bootstrap_remote_config_parser_reads_canonical_source_contract():
    text = """
remote_sources:
  - id: general
    name: General
    url: https://github.com/example/skills
    branch: main
    skills_path: skills/alpha
  - id: research
    name: Research
    url: https://github.com/example/research
    branch: stable
    skills_path: skills
legacy_skill_names:
  - old-name
"""

    sources = bootstrap.parse_remote_sources_from_text(text)

    assert sources == [
        {
            "id": "general",
            "name": "General",
            "url": "https://github.com/example/skills",
            "branch": "main",
            "skills_path": "skills/alpha",
        },
        {
            "id": "research",
            "name": "Research",
            "url": "https://github.com/example/research",
            "branch": "stable",
            "skills_path": "skills",
        },
    ]


def test_bootstrap_selective_archive_include_does_not_extract_other_skills():
    include = bootstrap.build_archive_include_paths("skills/alpha", ["demo"])

    assert include == ["skills/alpha/demo"]
    assert bootstrap.should_extract_archive_member(
        "repo-main/skills/alpha/demo/SKILL.md", include
    )
    assert not bootstrap.should_extract_archive_member(
        "repo-main/skills/alpha/other/SKILL.md", include
    )


def test_local_cli_dry_run_does_not_create_target_and_real_run_reuses_md5(tmp_path):
    source = tmp_path / "source"
    make_skill(source, "demo")
    home = tmp_path / "home"
    env = {**os.environ, "HOME": str(home)}
    script = ROOT / "skills/alpha/install-bensz-skills/scripts/install.py"

    dry_run = subprocess.run(
        [sys.executable, str(script), "--codex", "--dry-run", "--source", str(source)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert dry_run.returncode == 0
    assert not (home / ".codex/skills/demo").exists()

    first = subprocess.run(
        [sys.executable, str(script), "--codex", "--source", str(source)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert first.returncode == 0
    manifest = home / ".codex/skills/demo/.skill-manifest.codex.json"
    assert json.loads(manifest.read_text(encoding="utf-8"))["schema_version"] == 1

    second = subprocess.run(
        [sys.executable, str(script), "--codex", "--source", str(source)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert second.returncode == 0
    assert "跳过" in second.stdout or "Skipped" in second.stdout


def test_silent_update_creates_state_for_empty_install_set(tmp_path, monkeypatch):
    monkeypatch.setattr(install.Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.setattr(
        install,
        "ensure_managed_runtime",
        lambda: {"ready": True, "packages": {"bensz-skill-kernel": "2.1.2"}},
    )
    assert install._run_silent_update(t=install.get_translator()) == 0
    state_path = tmp_path / ".bensz-skills/installation/state/silent-update.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["last_result"] == "success"
    assert data["runtime"]["ready"] is True


def test_silent_update_respects_ttl_without_remote_call(tmp_path, monkeypatch):
    monkeypatch.setattr(install.Path, "home", staticmethod(lambda: tmp_path))
    install._write_silent_update_state(result="success")
    monkeypatch.setattr(install, "_remote_install_main", lambda **_: pytest.fail("remote call"))
    assert install._run_silent_update(t=install.get_translator()) == 0


def test_silent_update_only_passes_installed_skills_and_never_blocks_on_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(install.Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.setattr(install, "ensure_managed_runtime", lambda: {"ready": True})
    make_skill(tmp_path / ".codex/skills", "installed")
    captured = {}

    def fake_remote(**kwargs):
        captured.update(kwargs)
        raise RuntimeError("offline")

    monkeypatch.setattr(install, "_remote_install_main", fake_remote)
    assert install._run_silent_update(t=install.get_translator()) == 0
    assert captured["skill_filter"] == ["installed"]
    state = json.loads((tmp_path / ".bensz-skills/installation/state/silent-update.json").read_text(encoding="utf-8"))
    assert state["last_result"] == "failed"


def test_managed_runtime_config_uses_owned_conda_prefix_and_latest_bsk():
    config = managed_runtime.load_config(
        ROOT / "skills/alpha/install-bensz-skills/scripts/managed-runtime.json"
    )

    assert config["environment"] == {
        "name": "benszapi",
        "prefix": ".bensz-skills/envs/benszapi",
        "python": "3.12",
    }
    assert config["update_ttl_hours"] == 72
    assert config["packages"][0]["distribution"] == "bensz-skill-kernel"
    assert config["packages"][0]["version_policy"] == "latest-production"


def test_managed_runtime_prefix_cannot_escape_home(tmp_path):
    config = managed_runtime.load_config(
        ROOT / "skills/alpha/install-bensz-skills/scripts/managed-runtime.json"
    )
    config["environment"]["prefix"] = "../outside"

    with pytest.raises(managed_runtime.ManagedRuntimeError, match="escapes"):
        managed_runtime.runtime_prefix(config, home=tmp_path)


def test_managed_runtime_creates_updates_validates_and_installs_launcher(tmp_path, monkeypatch):
    config = managed_runtime.load_config(
        ROOT / "skills/alpha/install-bensz-skills/scripts/managed-runtime.json"
    )
    prefix = managed_runtime.runtime_prefix(config, home=tmp_path)
    calls = []

    def completed(command, stdout=""):
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    def fake_checked_run(command, label, timeout=300):
        command = [str(part) for part in command]
        calls.append(command)
        if "create" in command:
            python = managed_runtime.runtime_python(prefix)
            python.parent.mkdir(parents=True, exist_ok=True)
            python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            python.chmod(0o755)
        elif command[1:4] == ["-m", "pip", "install"]:
            bsk = managed_runtime.runtime_command(prefix, "bsk")
            bsk.write_text("#!/bin/sh\nprintf 'managed-bsk\\n'\n", encoding="utf-8")
            bsk.chmod(0o755)
        if "-c" in command:
            return completed(command, '{"bensz-skill-kernel": "2.1.2"}\n')
        return completed(command)

    monkeypatch.setattr(managed_runtime, "find_conda", lambda: "/fake/conda")
    monkeypatch.setattr(managed_runtime, "_checked_run", fake_checked_run)

    result = managed_runtime.ensure(config=config, home=tmp_path)

    assert result["ready"] is True
    assert result["created"] is True
    assert result["updated"] is True
    assert result["packages"] == {"bensz-skill-kernel": "2.1.2"}
    assert calls[0][:5] == [
        "/fake/conda", "create", "--yes", "--prefix", str(prefix)
    ]
    assert any("bensz-skill-kernel" in command for command in calls)
    launcher = tmp_path / ".bensz-skills/bin/bsk"
    assert launcher.is_file()
    assert subprocess.check_output([launcher], text=True).strip() == "managed-bsk"
    state = json.loads(managed_runtime.state_path(tmp_path).read_text(encoding="utf-8"))
    assert state["prefix"] == "~/.bensz-skills/envs/benszapi"
    assert str(tmp_path) not in json.dumps(state)


def test_managed_runtime_reuses_healthy_environment_inside_ttl(tmp_path, monkeypatch):
    config = managed_runtime.load_config(
        ROOT / "skills/alpha/install-bensz-skills/scripts/managed-runtime.json"
    )
    prefix = managed_runtime.runtime_prefix(config, home=tmp_path)
    python = managed_runtime.runtime_python(prefix)
    bsk = managed_runtime.runtime_command(prefix, "bsk")
    python.parent.mkdir(parents=True)
    python.touch()
    bsk.touch()
    managed_runtime._write_state(
        {
            "last_check_completed_at": int(time.time()),
            "last_result": "success",
            "packages": {"bensz-skill-kernel": "2.1.2"},
        },
        home=tmp_path,
    )
    calls = []

    def fake_checked_run(command, label, timeout=300):
        command = [str(part) for part in command]
        calls.append(command)
        stdout = '{"bensz-skill-kernel": "2.1.2"}\n' if "-c" in command else ""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(managed_runtime, "_checked_run", fake_checked_run)

    result = managed_runtime.ensure(config=config, home=tmp_path)

    assert result["ready"] is True
    assert result["created"] is False
    assert result["updated"] is False
    assert not any(command[1:4] == ["-m", "pip", "install"] for command in calls)


def test_managed_runtime_repairs_package_version_drift_inside_ttl(tmp_path, monkeypatch):
    config = managed_runtime.load_config(
        ROOT / "skills/alpha/install-bensz-skills/scripts/managed-runtime.json"
    )
    prefix = managed_runtime.runtime_prefix(config, home=tmp_path)
    python = managed_runtime.runtime_python(prefix)
    bsk = managed_runtime.runtime_command(prefix, "bsk")
    python.parent.mkdir(parents=True)
    python.touch()
    bsk.touch()
    managed_runtime._write_state(
        {
            "last_check_completed_at": int(time.time()),
            "last_result": "success",
            "packages": {"bensz-skill-kernel": "2.1.2"},
        },
        home=tmp_path,
    )
    calls = []

    def fake_checked_run(command, label, timeout=300):
        command = [str(part) for part in command]
        calls.append(command)
        stdout = '{"bensz-skill-kernel": "1.0.0"}\n' if "-c" in command else ""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(managed_runtime, "_checked_run", fake_checked_run)

    result = managed_runtime.ensure(config=config, home=tmp_path)

    assert result["updated"] is True
    assert any(command[1:4] == ["-m", "pip", "install"] for command in calls)


def test_managed_runtime_dry_run_does_not_require_conda_or_write(tmp_path, monkeypatch):
    config = managed_runtime.load_config(
        ROOT / "skills/alpha/install-bensz-skills/scripts/managed-runtime.json"
    )
    monkeypatch.setattr(
        managed_runtime,
        "find_conda",
        lambda: pytest.fail("dry-run must not resolve or execute Conda"),
    )

    result = managed_runtime.ensure(config=config, home=tmp_path, dry_run=True)

    assert result["dry_run"] is True
    assert result["would_create"] == "~/.bensz-skills/envs/benszapi"
    assert not (tmp_path / ".bensz-skills").exists()


def test_managed_runtime_lock_rejects_concurrent_update(tmp_path, monkeypatch):
    lock = managed_runtime.state_path(tmp_path).with_name("managed-runtime.lock")
    lock.parent.mkdir(parents=True)
    lock.write_text("other-process", encoding="utf-8")
    monkeypatch.setattr(managed_runtime, "LOCK_TIMEOUT_SECONDS", 0)

    with pytest.raises(managed_runtime.ManagedRuntimeError, match="another process"):
        with managed_runtime._runtime_lock(tmp_path):
            pytest.fail("lock must not be acquired")
