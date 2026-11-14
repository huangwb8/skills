import copy
import json
import subprocess
import sys

import pytest

from bensz_skill_identity import (
    IdentityError,
    install_release,
    recover_install,
    security_metadata,
    verify_installation,
    verify_persisted,
)
from bensz_skill_identity.protocol import inventory
from bensz_skill_identity.state import file_lock


def test_install_exact_content_and_external_records(sample, tmp_path):
    target = tmp_path / "target"
    result = install_release(sample["release"], target, sample["policy"])
    assert result["decision"] == "allow"
    assert inventory(target / "sample") == inventory(sample["content"])
    assert (target / "sample/.asset").is_file()
    assert not list((target / "sample").glob(".skill-manifest*"))
    record = json.loads(
        (target / ".bensz-skill-identity/records/sample.json").read_text()
    )
    assert record["manifest_digest"] == sample["wanted"]["manifest_digest"]
    # Reinstallation repairs actual tampering; a saved record never skips verification.
    (target / "sample/SKILL.md").write_text("tampered", encoding="utf-8")
    install_release(sample["release"], target, sample["policy"])
    assert inventory(target / "sample") == inventory(sample["content"])


def test_dry_run_and_invalid_candidate_do_not_modify_target(sample, tmp_path):
    target = tmp_path / "target"
    install_release(sample["release"], target, sample["policy"], dry_run=True)
    assert not target.exists()
    install_release(sample["release"], target, sample["policy"])
    before = inventory(target)
    (sample["release"] / "content/SKILL.md").write_text("tampered", encoding="utf-8")
    with pytest.raises(IdentityError):
        install_release(sample["release"], target, sample["policy"])
    assert inventory(target) == before


@pytest.mark.parametrize(
    "phase",
    [
        "prepared",
        "old_moved",
        "new_moved",
        "metadata_manifest.json",
        "metadata_authorization.json",
        "committed",
    ],
)
def test_transaction_failure_recovers(sample, tmp_path, phase):
    target = tmp_path / "target"
    install_release(sample["release"], target, sample["policy"])
    original = inventory(target / "sample")

    def fail(current):
        if current == phase:
            raise OSError("injected failure")

    with pytest.raises(OSError):
        install_release(sample["release"], target, sample["policy"], _checkpoint=fail)
    recover_install(target)
    assert inventory(target / "sample") == original
    assert not (target / ".bensz-skill-identity/journal.json").exists()


@pytest.mark.parametrize(
    "phase",
    [
        "prepared",
        "old_moved",
        "new_moved",
        "metadata_manifest.json",
        "metadata_authorization.json",
        "committed",
    ],
)
def test_process_death_recovers(sample, tmp_path, phase):
    target = tmp_path / "target"
    install_release(sample["release"], target, sample["policy"])
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps(sample["policy"].to_dict()), encoding="utf-8")
    code = """import json,os,sys
from pathlib import Path
from bensz_skill_identity import TrustPolicy,install_release
def stop(phase):
    if phase == sys.argv[4]: os._exit(73)
install_release(Path(sys.argv[1]),Path(sys.argv[2]),TrustPolicy.from_dict(json.loads(Path(sys.argv[3]).read_text())),_checkpoint=stop)
"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            str(sample["release"]),
            str(target),
            str(policy),
            phase,
        ],
        check=False,
        capture_output=True,
    )
    assert result.returncode == 73, result.stderr
    recover_install(target)
    assert inventory(target / "sample") == inventory(sample["content"])
    install_release(sample["release"], target, sample["policy"])
    assert verify_installation(target, "sample", sample["policy"]).decision == "allow"


def test_concurrent_install_fails_closed(sample, tmp_path):
    target = tmp_path / "target"
    install_release(sample["release"], target, sample["policy"])
    with file_lock(target / ".bensz-skill-identity/install.lock"):
        with pytest.raises(IdentityError, match="state_locked"):
            install_release(sample["release"], target, sample["policy"])


def test_cli_verify_and_capabilities(sample, tmp_path):
    policy = tmp_path / "trust.json"
    policy.write_text(json.dumps(sample["policy"].to_dict()), encoding="utf-8")
    command = [
        sys.executable,
        "-m",
        "bensz_skill_identity",
        "verify",
        "--release",
        str(sample["release"]),
        "--trust-store",
        str(policy),
        "--state",
        str(tmp_path / "state.json"),
    ]
    checked = subprocess.run(command, check=False, capture_output=True, text=True)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert json.loads(checked.stdout)["assurance"] == "files_verified"
    (sample["release"] / "content/README.md").unlink()
    checked = subprocess.run(command, check=False, capture_output=True, text=True)
    assert checked.returncode == 3
    assert str(tmp_path) not in checked.stdout


def test_denied_install_remembers_revocation(sample, tmp_path):
    target = tmp_path / "target"
    install_release(sample["release"], target, sample["policy"])
    previous = copy.deepcopy(sample["policy"])
    sample["policy"].security[sample["publisher"]] = security_metadata(
        sample["root"],
        revision=2,
        issued_at=0,
        expires_at=sample["now"] + 300,
        revoked_releases=[sample["wanted"]["manifest_digest"]],
    )
    with pytest.raises(IdentityError, match="release_revoked"):
        install_release(sample["release"], target, sample["policy"])
    assert verify_installation(target, "sample", previous).reason == "metadata_rollback"
    assert inventory(target / "sample") == inventory(sample["content"])
    with pytest.raises(IdentityError, match="metadata_rollback"):
        install_release(sample["release"], target, previous)


def test_metadata_failure_retry_and_partial_directory(sample, tmp_path):
    target = tmp_path / "target"

    def fail(phase):
        if phase == "metadata_manifest.json":
            raise OSError("injected metadata failure")

    with pytest.raises(OSError):
        install_release(sample["release"], target, sample["policy"], _checkpoint=fail)
    assert not (target / "sample").exists()
    install_release(sample["release"], target, sample["policy"])
    assert verify_installation(target, "sample", sample["policy"]).decision == "allow"


def test_cli_and_api_share_state_lock(sample, tmp_path):
    from bensz_skill_identity.cli import execute, parser
    from bensz_skill_identity.state import state_lock_path

    trust = tmp_path / "trust.json"
    trust.write_text(json.dumps(sample["policy"].to_dict()), encoding="utf-8")
    wanted = tmp_path / "requirements.json"
    wanted.write_text(json.dumps([sample["wanted"]]), encoding="utf-8")
    state = tmp_path / "state.json"
    args = parser().parse_args(
        [
            "lock",
            "--trust-store",
            str(trust),
            "--state",
            str(state),
            "--candidate",
            str(sample["release"]),
            "--input",
            str(wanted),
        ]
    )
    with file_lock(state_lock_path(state)):
        with pytest.raises(IdentityError, match="state_locked"):
            execute(args)
        with pytest.raises(IdentityError, match="state_locked"):
            verify_persisted(sample["release"], sample["policy"], state_path=state)


def test_failed_cli_lock_persists_revocation(sample, tmp_path):
    from bensz_skill_identity.cli import execute, parser

    state = tmp_path / "state.json"
    verify_persisted(sample["release"], sample["policy"], state_path=state)
    sample["policy"].security[sample["publisher"]] = security_metadata(
        sample["root"],
        revision=2,
        issued_at=0,
        expires_at=sample["now"] + 300,
        disabled=True,
    )
    trust = tmp_path / "trust.json"
    trust.write_text(json.dumps(sample["policy"].to_dict()), encoding="utf-8")
    wanted = tmp_path / "requirements.json"
    wanted.write_text(json.dumps([sample["wanted"]]), encoding="utf-8")
    args = parser().parse_args(
        [
            "lock",
            "--trust-store",
            str(trust),
            "--state",
            str(state),
            "--candidate",
            str(sample["release"]),
            "--input",
            str(wanted),
        ]
    )
    with pytest.raises(IdentityError, match="publisher_disabled"):
        execute(args)
    assert (
        json.loads(state.read_text())["revisions"][sample["publisher"]]["revision"] == 2
    )
