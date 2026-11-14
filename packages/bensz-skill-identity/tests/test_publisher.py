"""Publisher tests create disposable PEMs and always remove them at teardown."""

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from bensz_skill_identity import (
    IdentityError,
    TrustPolicy,
    authorize,
    build_release,
    empty_state,
    initialize_publisher,
    public_hex,
    publisher_id,
    security_metadata,
    verify_release,
)
from bensz_skill_identity import publisher as module
from bensz_skill_identity.state import file_lock


@pytest.fixture
def lab(tmp_path):
    try:
        yield tmp_path
    finally:
        # No generated private key survives even when a test fails.
        shutil.rmtree(tmp_path, ignore_errors=True)


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(directory):
    return {
        p.relative_to(directory).as_posix(): fingerprint(p)
        for p in directory.rglob("*")
        if p.is_file()
    }


def key(directory, name):
    return load_pem_private_key(
        (directory / "bsi-keys" / f"{name}.pem").read_bytes(), password=None
    )


def error(code, operation):
    with pytest.raises(IdentityError) as raised:
        operation()
    assert raised.value.code == code
    assert raised.value.path == ""


def test_default_layout_distinct_keys_and_idempotent_reuse(lab, monkeypatch):
    monkeypatch.setenv("HOME", str(lab))
    result = initialize_publisher()
    directory = lab / ".bensz-skills/config"
    assert result["state"] == "created"
    assert result["publisher_id"] == publisher_id(result["root_public_key"])
    assert result["root_public_key"] != result["release_public_key"]
    assert public_hex(key(directory, "root")) == result["root_public_key"]
    assert public_hex(key(directory, "release")) == result["release_public_key"]
    before = files(directory)
    mtimes = {p: p.stat().st_mtime_ns for p in directory.rglob("*") if p.is_file()}
    repeated = initialize_publisher()
    assert repeated == {**result, "state": "reused"}
    assert files(directory) == before
    assert all(p.stat().st_mtime_ns == value for p, value in mtimes.items())
    if os.name != "nt":
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
        assert stat.S_IMODE((directory / "bsi-keys").stat().st_mode) == 0o700
        assert all(stat.S_IMODE(p.stat().st_mode) == 0o600 for p in mtimes)


def test_separate_developers_receive_distinct_identities(lab):
    first = initialize_publisher(lab / "developer-a")
    second = initialize_publisher(lab / "developer-b")
    assert first["publisher_id"] != second["publisher_id"]
    assert first["release_public_key"] != second["release_public_key"]


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission semantics")
@pytest.mark.parametrize("mask", [0o000, 0o777])
def test_permissions_do_not_depend_on_process_umask(lab, mask):
    old = os.umask(mask)
    try:
        assert initialize_publisher(lab / "config")["state"] == "created"
        assert initialize_publisher(lab / "config")["state"] == "reused"
    finally:
        os.umask(old)
    directory = lab / "config"
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert stat.S_IMODE((directory / "bsi-keys").stat().st_mode) == 0o700
    assert all(
        stat.S_IMODE(p.stat().st_mode) == 0o600
        for p in directory.rglob("*")
        if p.is_file()
    )


@pytest.mark.parametrize("suffix", [b"", b"\n", b"\r\n"])
def test_preserve_unrelated_environment_without_evaluating_shell(lab, suffix):
    directory = lab / "config with spaces and 'quotes'"
    directory.mkdir()
    original = b"# Existing settings\r\nUNRELATED_SETTING=$(not-a-command)" + suffix
    (directory / "remote.env").write_bytes(original)
    initialize_publisher(directory)
    assert (directory / "remote.env").read_bytes().startswith(original)
    assert initialize_publisher(directory)["state"] == "reused"


def test_existing_pair_recovers_missing_public_configuration(lab):
    result = initialize_publisher(lab)
    before = files(lab / "bsi-keys")
    (lab / "remote.env").unlink()
    restored = initialize_publisher(lab)
    assert restored == {**result, "state": "recovered"}
    assert files(lab / "bsi-keys") == before


@pytest.mark.parametrize("name", ["root.pem", "release.pem"])
def test_partial_pair_is_not_regenerated(lab, name):
    initialize_publisher(lab)
    (lab / "bsi-keys" / name).unlink()
    before = files(lab)
    error("publisher_incomplete", lambda: initialize_publisher(lab))
    assert files(lab) == before


def test_existing_configuration_without_keys_is_not_replaced(lab):
    initialize_publisher(lab)
    shutil.rmtree(lab / "bsi-keys")
    before = files(lab)
    error("publisher_incomplete", lambda: initialize_publisher(lab))
    assert files(lab) == before


@pytest.mark.parametrize("change", ["public", "path", "duplicate", "partial", "syntax"])
def test_conflicting_or_malformed_configuration_is_preserved(lab, change):
    result = initialize_publisher(lab)
    env = lab / "remote.env"
    text = env.read_text(encoding="utf-8")
    if change == "public":
        text = text.replace(result["root_public_key"], "0" * 64)
    elif change == "path":
        text = text.replace("root.pem", "other.pem")
    elif change == "duplicate":
        text += "BSI_ROOT_PUBLIC_KEY=duplicate\n"
    elif change == "partial":
        text = "BSI_PUBLISHER_ID=partial\n"
    else:
        text += "BSI_ROOT_PUBLIC_KEY 'unterminated\n"
    env.write_text(text, encoding="utf-8")
    before = files(lab)
    expected = (
        "publisher_identity_mismatch"
        if change in {"public", "path"}
        else "publisher_config_invalid"
    )
    error(expected, lambda: initialize_publisher(lab))
    assert files(lab) == before


def test_invalid_pem_is_not_replaced(lab):
    initialize_publisher(lab)
    (lab / "bsi-keys/root.pem").write_text("invalid PEM", encoding="utf-8")
    before = files(lab)
    error("invalid_key", lambda: initialize_publisher(lab))
    assert files(lab) == before


def test_same_root_and_release_key_is_rejected(lab):
    initialize_publisher(lab)
    (lab / "bsi-keys/release.pem").write_bytes((lab / "bsi-keys/root.pem").read_bytes())
    error("invalid_key", lambda: initialize_publisher(lab))


def test_invalid_environment_encoding_rejected_before_generating_keys(lab):
    (lab / "remote.env").write_bytes(b"UNRELATED_SETTING=\xff\n")
    error("publisher_config_invalid", lambda: initialize_publisher(lab))
    assert not (lab / "bsi-keys").exists()


def test_oversized_environment_rejected_before_generating_keys(lab):
    (lab / "remote.env").write_bytes(b"#" * (module.MAX_ENV_BYTES + 1))
    error("limit_exceeded", lambda: initialize_publisher(lab))
    assert not (lab / "bsi-keys").exists()


@pytest.mark.parametrize(
    "relative", ["remote.env", "bsi-keys", "bsi-keys/root.pem", ".bsi-init.lock"]
)
def test_symlink_resources_rejected(lab, relative):
    initialize_publisher(lab)
    path = lab / relative
    moved = lab / "moved"
    path.rename(moved)
    path.symlink_to(moved, target_is_directory=moved.is_dir())
    # Private permissions reject a linked lock before file_lock is called.
    expected = (
        "unsupported_file_type" if relative == ".bsi-init.lock" else "unsafe_path"
    )
    error(expected, lambda: initialize_publisher(lab))


def test_symlink_config_directory_rejected(lab):
    actual = lab / "actual"
    actual.mkdir()
    linked = lab / "linked"
    linked.symlink_to(actual, target_is_directory=True)
    error("unsafe_path", lambda: initialize_publisher(linked))
    assert not list(actual.iterdir())


def test_hardlinked_private_key_rejected(lab):
    initialize_publisher(lab)
    os.link(lab / "bsi-keys/root.pem", lab / "copy.pem")
    error("unsupported_file_type", lambda: initialize_publisher(lab))


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission semantics")
@pytest.mark.parametrize("relative", ["remote.env", "bsi-keys", "bsi-keys/root.pem"])
def test_insecure_existing_permissions_rejected(lab, relative):
    initialize_publisher(lab)
    (lab / relative).chmod(0o755)
    before = files(lab)
    error("publisher_permissions_invalid", lambda: initialize_publisher(lab))
    assert files(lab) == before


def test_locked_initializer_does_not_generate_keys(lab):
    with file_lock(lab / ".bsi-init.lock"):
        error("state_locked", lambda: initialize_publisher(lab))
    assert not (lab / "bsi-keys").exists()


def test_concurrent_initializers_never_publish_multiple_identities(lab):
    def run():
        try:
            return initialize_publisher(lab)
        except IdentityError as exc:
            return {"reason": exc.code}

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: run(), range(4)))
    successful = [r for r in results if r["reason"] == "ok"]
    assert successful
    assert len({r["publisher_id"] for r in successful}) == 1
    assert all(r["reason"] in {"ok", "state_locked"} for r in results)
    assert initialize_publisher(lab)["state"] == "reused"


def test_config_commit_failure_reuses_keys_on_retry(lab, monkeypatch):
    def fail(*args):
        raise OSError("synthetic write failure")

    with monkeypatch.context() as patch:
        patch.setattr(module.os, "replace", fail)
        with pytest.raises(OSError):
            initialize_publisher(lab)
    assert not (lab / "remote.env").exists()
    assert not list(lab.glob(".bsi-env-*"))
    before = files(lab / "bsi-keys")
    assert initialize_publisher(lab)["state"] == "recovered"
    assert files(lab / "bsi-keys") == before


def test_interrupted_pair_creation_keeps_first_key_and_refuses_retry(lab, monkeypatch):
    original = module._write_private

    def fail_second(path, private):
        if path.name == "release.pem":
            raise OSError("synthetic second-key failure")
        original(path, private)

    with monkeypatch.context() as patch:
        patch.setattr(module, "_write_private", fail_second)
        with pytest.raises(OSError):
            initialize_publisher(lab)
    before = files(lab)
    error("publisher_incomplete", lambda: initialize_publisher(lab))
    assert files(lab) == before


def test_uncoordinated_environment_edit_is_not_overwritten(lab, monkeypatch):
    original = module.tempfile.mkstemp

    def change(*args, **kwargs):
        result = original(*args, **kwargs)
        (lab / "remote.env").write_text("UNRELATED_SETTING=changed\n", encoding="utf-8")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(module.tempfile, "mkstemp", change)
        error("publisher_config_changed", lambda: initialize_publisher(lab))
    assert (lab / "remote.env").read_text() == "UNRELATED_SETTING=changed\n"
    assert not list(lab.glob(".bsi-env-*"))
    assert initialize_publisher(lab)["state"] == "recovered"


def test_generated_keys_work_with_existing_signing_and_verification(lab, sample):
    result = initialize_publisher(lab / "config")
    root, release = key(lab / "config", "root"), key(lab / "config", "release")
    content = sample["content"]
    (content / "config.yaml").write_text(
        'skill_info:\n  version: "0.1.0"\n  identity:\n'
        f"    publisher_id: {result['publisher_id']}\n    skill_key: sample\n",
        encoding="utf-8",
    )
    now = sample["now"]
    auth = authorize(
        root,
        result["release_public_key"],
        ["sample"],
        not_before=0,
        expires_at=now + 600,
    )
    security = security_metadata(
        root, revision=1, issued_at=now - 1, expires_at=now + 600
    )
    policy = TrustPolicy(
        {result["publisher_id"]: result["root_public_key"]},
        {result["publisher_id"]: security},
        {result["publisher_id"]: 1},
    )
    destination = lab / "signed-release"
    wanted = build_release(content, destination, release, auth, history={}, now=now)
    checked = verify_release(
        destination, policy, state=empty_state(), request=wanted, now=now
    )
    assert checked.decision == "allow"


def test_cli_public_output_and_sanitized_failure(lab):
    directory = lab / "config"
    directory.mkdir()
    (directory / "remote.env").write_text(
        "UNRELATED_SETTING=must-stay-local\n", encoding="utf-8"
    )
    invocation = [
        sys.executable,
        "-m",
        "bensz_skill_identity",
        "init",
        "--config-dir",
        str(directory),
    ]
    created = subprocess.run(invocation, capture_output=True, text=True)
    assert created.returncode == 0
    result = json.loads(created.stdout)
    assert result["state"] == "created"
    assert set(result) == {
        "schema",
        "reason",
        "state",
        "publisher_id",
        "root_public_key",
        "release_public_key",
    }
    assert not created.stderr
    assert "PRIVATE KEY" not in created.stdout
    assert "must-stay-local" not in created.stdout
    assert str(directory) not in created.stdout
    reused = subprocess.run(invocation, capture_output=True, text=True)
    assert reused.returncode == 0
    assert json.loads(reused.stdout)["state"] == "reused"
    (directory / "bsi-keys/root.pem").write_text("invalid PEM", encoding="utf-8")
    failed = subprocess.run(invocation, capture_output=True, text=True)
    assert failed.returncode == 3
    assert json.loads(failed.stdout) == {
        "schema": "bensz-skill-identity/v1/error",
        "reason": "invalid_key",
        "path": "",
    }
    assert not failed.stderr
