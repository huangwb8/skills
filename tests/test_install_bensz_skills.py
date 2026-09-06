import ast
import importlib.util
import json
import os
import subprocess
import sys
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
