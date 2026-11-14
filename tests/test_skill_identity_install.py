"""Public installer integration, all installations confined to pytest basetemp."""

import ast
import importlib.util
import json
import sys
import time
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "packages/bensz-skill-identity/src")
)

from bensz_skill_identity import (
    TrustPolicy,
    authorize,
    build_release,
    public_hex,
    publisher_id,
    security_metadata,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/alpha/install-bensz-skills/scripts"
sys.path.insert(0, str(SCRIPTS))
import bootstrap_install as bootstrap  # noqa: E402
import remove_legacy_skills as cleaner  # noqa: E402
import update_remote_skills as updater  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "identity_full_installer", SCRIPTS / "install.py"
)
install = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = install
spec.loader.exec_module(install)


@pytest.fixture
def signed(tmp_path, monkeypatch):
    monkeypatch.setattr(install.Path, "home", staticmethod(lambda: tmp_path / "home"))
    now = int(time.time())
    root = Ed25519PrivateKey.generate()
    key = Ed25519PrivateKey.generate()
    pub = publisher_id(public_hex(root))
    content = tmp_path / "content"
    content.mkdir()
    (content / "config.yaml").write_text(
        f'skill_info:\n  name: sample\n  version: "0.1.0"\n  identity:\n    publisher_id: {pub}\n    skill_key: sample\n',
        encoding="utf-8",
    )
    for name in ("SKILL.md", "README.md", ".asset"):
        (content / name).write_text("public synthetic fixture", encoding="utf-8")
    auth = authorize(
        root, public_hex(key), ["sample"], not_before=0, expires_at=now + 600
    )
    release = tmp_path / "release"
    build_release(content, release, key, auth, history={})
    policy = TrustPolicy(
        {pub: public_hex(root)},
        {pub: security_metadata(root, revision=1, issued_at=0, expires_at=now + 600)},
        {pub: 1},
    )
    trust = tmp_path / "trust.json"
    trust.write_text(json.dumps(policy.to_dict()), encoding="utf-8")
    return release, trust, tmp_path / "home/.codex/skills"


def test_public_strict_install(signed):
    release, trust, target = signed
    assert (
        install.main(
            ["--release", str(release), "--trust-store", str(trust), "--codex"]
        )
        == 0
    )
    assert (target / "sample/.asset").is_file()
    assert (target / "sample/README.md").is_file()
    assert not (target / "sample/.skill-manifest.codex.json").exists()
    assert (target / ".bensz-skill-identity/records/sample.json").is_file()
    assert not (target.parent.parent / ".claude").exists()


def test_strict_dry_run_is_readonly(signed):
    release, trust, target = signed
    assert (
        install.main(
            [
                "--release",
                str(release),
                "--trust-store",
                str(trust),
                "--codex",
                "--force",
                "--dry-run",
            ]
        )
        == 0
    )
    assert not target.exists()


@pytest.mark.parametrize(
    "entry",
    [
        "local",
        "remote",
        "bootstrap",
        "cleaner",
        "bootstrap-cleaner",
        "updater",
        "corrupt",
    ],
)
def test_all_legacy_entries_protect_managed(signed, entry, monkeypatch):
    release, trust, target = signed
    assert (
        install.main(
            ["--release", str(release), "--trust-store", str(trust), "--codex"]
        )
        == 0
    )
    body = (target / "sample/SKILL.md").read_bytes()
    if entry == "corrupt":
        (target / ".bensz-skill-identity/records/sample.json").write_text(
            "corrupt", encoding="utf-8"
        )
    with pytest.raises(RuntimeError, match="managed_install_protected"):
        if entry in ("local", "corrupt"):
            install._install_to_target(
                target=install.Target("codex", target, target / "pipeline-skills"),
                skills_root=release,
                skill_dirs_by_type={
                    "normal": [release / "content"],
                    "test": [],
                    "auxiliary": [],
                },
                dry_run=False,
                force=True,
                legacy_skill_names=["sample"],
                t=install.get_translator(),
            )
        elif entry == "remote":
            install._install_remote_skills(
                [
                    install.SkillComparison(
                        "sample",
                        "x",
                        "x",
                        "unchanged",
                        release / "content",
                        target / "sample",
                    )
                ],
                install.Target("codex", target, target / "pipeline-skills"),
                True,
                "test",
                [],
                install.get_translator(),
            )
        elif entry == "bootstrap":
            bootstrap.install_skills(
                [],
                0,
                bootstrap.Target("codex", target, target / "pipeline-skills"),
                "test",
                ["sample"],
                True,
                False,
                "en",
            )
        elif entry == "cleaner":
            cleaner.remove_legacy_skills(
                target_root=target, legacy_skill_names=["sample"], dry_run=False
            )
        elif entry == "bootstrap-cleaner":
            bootstrap.remove_legacy_skills(
                bootstrap.Target("codex", target, target / "pipeline-skills"),
                set(),
                ["sample"],
                "en",
                False,
                bootstrap.InstallResult(),
            )
        else:
            monkeypatch.setattr(updater, "TARGETS", {"codex": target})
            monkeypatch.setattr(
                updater,
                "load_sources",
                lambda: pytest.fail("network/source discovery reached"),
            )
            updater.main(["--skill", "sample", "--codex"])
    assert (target / "sample/SKILL.md").read_bytes() == body


def test_bootstrap_capability_failure_before_download(signed, monkeypatch):
    release, trust, target = signed
    monkeypatch.delenv("BENSZ_IDENTITY_PYTHON", raising=False)
    monkeypatch.delenv("BENSZ_IDENTITY_INSTALLER", raising=False)
    monkeypatch.setattr(
        bootstrap,
        "load_remote_config_contract",
        lambda: pytest.fail("remote config reached"),
    )
    assert bootstrap.main(["--release", str(release), "--trust-store", str(trust)]) == 3
    assert not target.exists()


def test_bootstrap_delegation_argument_array_and_exit(signed, monkeypatch):
    release, trust, _ = signed
    calls = []

    def run(command, **kwargs):
        from subprocess import CompletedProcess

        calls.append(command)
        if "--identity-capabilities" in command:
            return CompletedProcess(
                command,
                0,
                json.dumps(
                    {
                        "schema": "bensz-skill-identity/v1/capabilities",
                        "protocol": 1,
                        "strict_install": True,
                    }
                ),
            )
        return CompletedProcess(command, 7)

    monkeypatch.setattr(bootstrap.subprocess, "run", run)
    assert (
        bootstrap.main(
            [
                "--release",
                str(release),
                "--trust-store",
                str(trust),
                "--identity-python",
                "trusted python",
                "--identity-installer",
                "trusted installer.py",
                "--codex",
                "--dry-run",
            ]
        )
        == 7
    )
    assert calls[-1][:2] == ["trusted python", "trusted installer.py"]
    assert "--codex" in calls[-1] and "--dry-run" in calls[-1]


def test_bootstrap_stays_python38_self_contained():
    ast.parse(
        (SCRIPTS / "bootstrap_install.py").read_text(encoding="utf-8"),
        feature_version=(3, 8),
    )


def test_repository_skill_temporary_release(tmp_path):
    """Real maintained Skill copy; all identity material remains synthetic."""
    import shutil
    import yaml
    from bensz_skill_identity import install_release, verify_installation

    content = tmp_path / "git-commit"
    shutil.copytree(ROOT / "skills/alpha/git-commit", content)
    root = Ed25519PrivateKey.generate()
    key = Ed25519PrivateKey.generate()
    pub = publisher_id(public_hex(root))
    info = yaml.safe_load((content / "config.yaml").read_text(encoding="utf-8"))
    info["skill_info"]["identity"] = {"publisher_id": pub, "skill_key": "git-commit"}
    (content / "config.yaml").write_text(
        yaml.safe_dump(info, allow_unicode=True), encoding="utf-8"
    )
    expires = int(time.time()) + 600
    auth = authorize(
        root, public_hex(key), ["git-commit"], not_before=0, expires_at=expires
    )
    release = tmp_path / "release"
    build_release(content, release, key, auth, history={})
    policy = TrustPolicy(
        {pub: public_hex(root)},
        {pub: security_metadata(root, revision=1, issued_at=0, expires_at=expires)},
        {pub: 1},
    )
    install_release(release, tmp_path / "target", policy)
    assert (
        verify_installation(tmp_path / "target", "git-commit", policy).decision
        == "allow"
    )
