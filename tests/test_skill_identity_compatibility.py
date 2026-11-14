"""Unsigned installation stays usable without the optional identity runtime."""

import builtins
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/alpha/install-bensz-skills/scripts"


@pytest.fixture
def legacy_tools(tmp_path, monkeypatch):
    original_import = builtins.__import__

    def without_identity(name, *args, **kwargs):
        if name.split(".")[0] in {"bensz_skill_identity", "cryptography"}:
            raise ModuleNotFoundError("optional identity runtime unavailable", name=name)
        return original_import(name, *args, **kwargs)

    # Block before loading the installer, including its transitive imports.
    monkeypatch.setattr(builtins, "__import__", without_identity)
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("compat_installer", SCRIPTS / "install.py")
    install = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, install)
    spec.loader.exec_module(install)
    import bootstrap_install as bootstrap
    import update_remote_skills as updater

    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
    return install, bootstrap, updater


def make_unsigned(source, identity):
    skill = source / "unsigned-probe"
    (skill / "scripts").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: unsigned-probe\ndescription: Public compatibility fixture\n"
        "category: normal\n---\n\nRun scripts/helper.py.\n",
        encoding="utf-8",
    )
    (skill / "scripts/helper.py").write_text(
        "print('unsigned-helper-ok')\n", encoding="utf-8"
    )
    if identity != "no-config":
        declaration = {
            "absent": "",
            "unconfirmed": "  identity:\n    publisher_id: unconfirmed\n    skill_key: unsigned-probe\n",
            "partial": "  identity:\n    skill_key: unsigned-probe\n",
        }[identity]
        (skill / "config.yaml").write_text(
            "skill_info:\n  name: unsigned-probe\n  version: 0.1.0\n" + declaration,
            encoding="utf-8",
        )
    return skill


def assert_usable(target):
    skill = target / "unsigned-probe"
    assert "Public compatibility fixture" in (skill / "SKILL.md").read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(skill / "scripts/helper.py")],
        cwd=target.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "unsigned-helper-ok"
    assert not (target / ".bensz-skill-identity/records/unsigned-probe.json").exists()


@pytest.mark.parametrize("identity", ["no-config", "absent", "unconfirmed", "partial"])
@pytest.mark.parametrize("platform", ["codex", "claude"])
def test_local_unsigned_install_update_and_execute_without_identity(
    tmp_path, legacy_tools, identity, platform
):
    install, _, _ = legacy_tools
    source = tmp_path / "source"
    skill = make_unsigned(source, identity)
    args = ["--source", str(source), "--skill", skill.name, "--" + platform]
    target = tmp_path / f"home/.{platform}/skills"
    assert install.main(args + ["--dry-run"]) == 0
    assert not target.exists()
    assert install.main(args) == 0
    assert install.main(args) == 0
    (skill / "scripts/helper.py").write_text(
        "# changed unsigned source\nprint('unsigned-helper-ok')\n", encoding="utf-8"
    )
    assert install.main(args) == 0
    assert "changed unsigned source" in (target / skill.name / "scripts/helper.py").read_text(encoding="utf-8")
    assert_usable(target)
    assert not (tmp_path / f"home/.{'claude' if platform == 'codex' else 'codex'}").exists()


@pytest.mark.parametrize("entry", ["local", "remote", "bootstrap"])
@pytest.mark.parametrize("mixed", [False, True])
@pytest.mark.parametrize("identity", ["absent", "unconfirmed"])
def test_unsigned_entries_and_unrelated_managed_record(
    tmp_path, monkeypatch, legacy_tools, entry, mixed, identity
):
    install, bootstrap, _ = legacy_tools
    source = tmp_path / "source"
    skill = make_unsigned(source, identity)
    target = tmp_path / "home/.codex/skills"
    record = target / ".bensz-skill-identity/records/other-skill.json"
    if mixed:
        record.parent.mkdir(parents=True)
        record.write_text('{"synthetic_guard_fixture": true}', encoding="utf-8")
    if entry == "local":
        assert install.main(["--source", str(source), "--skill", skill.name, "--codex"]) == 0
    elif entry == "remote":
        monkeypatch.setattr(install, "_check_git_available", lambda: True)
        monkeypatch.setattr(
            install, "_download_remote_source",
            lambda *_args, **_kwargs: install.RemoteDownloadResult(skills_dir=source),
        )
        assert install.main(["--remote", "--auto", "--general", "--skill", skill.name, "--codex"]) == 0
    else:
        monkeypatch.setattr(bootstrap, "load_remote_config_contract", lambda: (
            bootstrap.DEFAULT_SOURCES, [], "synthetic-contract", {},
        ))
        monkeypatch.setattr(bootstrap, "download_source", lambda *_args: (source, False))
        assert bootstrap.main(["--source", "general", "--skill", skill.name, "--codex"]) == 0
    assert_usable(target)
    if mixed:
        assert record.read_text(encoding="utf-8") == '{"synthetic_guard_fixture": true}'


@pytest.mark.parametrize("mixed", [False, True])
def test_fast_updater_can_select_unsigned_without_identity(
    tmp_path, monkeypatch, legacy_tools, mixed
):
    _, _, updater = legacy_tools
    target = tmp_path / "home/.codex/skills"
    if mixed:
        record = target / ".bensz-skill-identity/records/other-skill.json"
        record.parent.mkdir(parents=True)
        record.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(updater, "TARGETS", {"codex": target})
    source = {"id": "general", "url": "https://github.com/huangwb8/skills", "skills_path": "skills/alpha"}
    monkeypatch.setattr(updater, "load_sources", lambda: [source])
    monkeypatch.setattr(updater, "github_tree", lambda _source: ["skills/alpha/unsigned-probe/config.yaml"])
    monkeypatch.setattr(updater, "fetch_preferred_text", lambda *_args: "skill_info:\n  version: 0.2.0\n")
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(updater.subprocess, "run", run)
    assert updater.main(["--skill", "unsigned-probe", "--codex"]) == 0
    assert calls and "unsigned-probe" in calls[0]
    assert "--release" not in calls[0]


def test_identity_capability_missing_does_not_disable_subsequent_legacy_install(tmp_path, legacy_tools):
    install, _, _ = legacy_tools
    assert install.main(["--identity-capabilities"]) == 3
    source = tmp_path / "source"
    skill = make_unsigned(source, "unconfirmed")
    assert install.main(["--source", str(source), "--skill", skill.name, "--codex"]) == 0
    assert_usable(tmp_path / "home/.codex/skills")


@pytest.mark.parametrize("identity", ["absent", "unconfirmed"])
@pytest.mark.parametrize("force", [False, True])
def test_default_bulk_install_remains_unsigned_for_both_platforms(
    tmp_path, legacy_tools, identity, force
):
    install, _, _ = legacy_tools
    source = tmp_path / "source"
    make_unsigned(source, identity)
    args = ["--source", str(source)] + (["--force"] if force else [])
    assert install.main(args) == 0
    assert install.main(args) == 0
    for platform in ("codex", "claude"):
        target = tmp_path / f"home/.{platform}/skills"
        assert_usable(target)
        assert not (target / ".bensz-skill-identity").exists()


def test_mixed_root_bulk_updater_requires_explicit_selection(tmp_path, monkeypatch, legacy_tools):
    """Document the current limit: managed roots reject unfiltered bulk updates."""
    _, bootstrap, updater = legacy_tools
    target = tmp_path / "home/.codex/skills"
    record = target / ".bensz-skill-identity/records/other-skill.json"
    record.parent.mkdir(parents=True)
    record.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(updater, "TARGETS", {"codex": target})
    monkeypatch.setattr(updater, "load_sources", lambda: pytest.fail("network discovery reached"))
    assert bootstrap.guarded_exit(updater.main, ["--codex"]) == 3
    assert record.read_text(encoding="utf-8") == "{}"
