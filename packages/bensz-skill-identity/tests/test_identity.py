import copy
import hashlib
import json
import os

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bensz_skill_identity import (
    IdentityError,
    Limits,
    TrustPolicy,
    authorize,
    build_release,
    digest,
    empty_state,
    public_hex,
    publisher_id,
    read_identity,
    resolve_lock,
    resolve_name,
    security_metadata,
    snapshot_release,
    verify_lock,
    verify_persisted,
    verify_release,
)
from bensz_skill_identity.crypto import authenticate
from bensz_skill_identity.protocol import canonical, inventory, load_json, safe_path


def check(sample, **kwargs):
    return verify_release(
        sample["release"],
        sample["policy"],
        state=kwargs.pop("state", empty_state()),
        now=kwargs.pop("now", sample["now"]),
        **kwargs,
    )


def test_valid_deterministic_request_binding(sample, tmp_path):
    result = check(sample, request=sample["wanted"])
    assert (result.verification, result.decision, result.assurance) == (
        "verified",
        "allow",
        "files_verified",
    )
    other = tmp_path / "other"
    assert (
        build_release(
            sample["content"],
            other,
            sample["key"],
            sample["auth"],
            history={},
            now=sample["now"],
        )
        == result.as_requirement()
    )
    assert (other / "manifest.json").read_bytes() == (
        sample["release"] / "manifest.json"
    ).read_bytes()
    wrong = {**sample["wanted"], "content_digest": "0" * 64}
    assert check(sample, request=wrong).reason == "request_mismatch"
    assert result.request_digest != check(sample).request_digest


def test_unknown_root_does_not_become_trusted(sample):
    sample["policy"] = TrustPolicy()
    result = check(sample)
    assert (result.verification, result.decision, result.reason) == (
        "verified",
        "trust_required",
        "publisher_untrusted",
    )


@pytest.mark.parametrize(
    "text,reason",
    [
        ("skill_info:\n  identity: {}\n", "invalid_metadata"),
        ("skill_info:\n  identity: null\n", "invalid_metadata"),
        ("skill_info: {}\nskill_info: {}\n", "duplicate_key"),
        ("a: &x [1]\nb: *x\n", "invalid_yaml"),
        ("skill_info: []\n", "invalid_identity"),
    ],
)
def test_config_rejects_ambiguous_input(tmp_path, text, reason):
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(IdentityError) as error:
        read_identity(path)
    assert error.value.code == reason


def test_legacy_identity_is_unverified(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("skill_info:\n  name: legacy\n", encoding="utf-8")
    assert read_identity(path) is None


@pytest.mark.parametrize(
    "name",
    [
        "config.yaml",
        "SKILL.md",
        "scripts/helper.py",
        "references/reference.md",
        "agents/reviewer/SKILL.md",
        ".asset",
    ],
)
def test_each_asset_is_protected(sample, name):
    (sample["release"] / "content" / name).write_text("changed", encoding="utf-8")
    result = check(sample)
    assert result.decision == "deny"
    assert result.verification == "failed"


@pytest.mark.parametrize(
    "operation", ["extra", "missing", "mode", "symlink", "hardlink", "case"]
)
def test_inventory_attacks(sample, operation):
    content = sample["release"] / "content"
    if operation == "extra":
        (content / "extra").write_text("extra", encoding="utf-8")
    elif operation == "missing":
        (content / "SKILL.md").unlink()
    elif operation == "mode":
        (content / "SKILL.md").chmod(0o755)
    elif operation == "symlink":
        (content / "alias").symlink_to(content / "SKILL.md")
    elif operation == "hardlink":
        os.link(content / "SKILL.md", content / "alias")
    else:
        (content / "skill.MD").write_text("collision", encoding="utf-8")
    assert check(sample).decision == "deny"


@pytest.mark.parametrize(
    "path",
    [
        "../x",
        "/tmp/x",
        "a//b",
        "a/./b",
        "C:/x",
        "a\\b",
        "NUL",
        "a/COM1.txt",
        "a.",
        "a ",
        "a\x00b",
        "a?b",
        "e\u0301",
    ],
)
def test_portable_paths(path):
    with pytest.raises(IdentityError):
        safe_path(path)


def test_limits_and_special_file(sample):
    assert (
        verify_release(
            sample["release"],
            sample["policy"],
            state=empty_state(),
            limits=Limits(files=1),
        ).reason
        == "limit_exceeded"
    )
    if hasattr(os, "mkfifo"):
        os.mkfifo(sample["content"] / "pipe")
        with pytest.raises(IdentityError, match="unsupported_file_type"):
            inventory(sample["content"])


def test_signature_and_domain_separation(sample):
    env = load_json(sample["release"] / "manifest.json")
    with pytest.raises(IdentityError, match="signature_invalid"):
        authenticate(env, "security")
    env["signature"] = "0" * 128
    (sample["release"] / "manifest.json").write_bytes(canonical(env))
    assert check(sample).reason == "signature_invalid"


@pytest.mark.parametrize(
    "kind,reason",
    [
        ("disabled", "publisher_disabled"),
        ("key", "key_revoked"),
        ("release", "release_revoked"),
        ("expired", "metadata_expired"),
        ("future", "metadata_not_yet_valid"),
    ],
)
def test_security_revocation_and_time(sample, kind, reason):
    args = {
        "revision": 2,
        "issued_at": sample["now"] - 10,
        "expires_at": sample["now"] + 100,
    }
    if kind == "disabled":
        args["disabled"] = True
    if kind == "key":
        args["revoked_keys"] = [
            hashlib.sha256(bytes.fromhex(public_hex(sample["key"]))).hexdigest()
        ]
    if kind == "release":
        args["revoked_releases"] = [sample["wanted"]["manifest_digest"]]
    if kind == "expired":
        args["expires_at"] = sample["now"]
    if kind == "future":
        args["issued_at"] = sample["now"] + 1
    sample["policy"].security[sample["publisher"]] = security_metadata(
        sample["root"], **args
    )
    assert check(sample).reason == reason


def test_security_rollback_equivocation_and_invalid_high_water(sample):
    state = empty_state()
    assert check(sample, state=state).decision == "allow"
    previous = copy.deepcopy(sample["policy"].security[sample["publisher"]])
    sample["policy"].security[sample["publisher"]] = security_metadata(
        sample["root"],
        revision=2,
        issued_at=sample["now"] - 1,
        expires_at=sample["now"] + 300,
        disabled=True,
    )
    assert check(sample, state=state).reason == "publisher_disabled"
    sample["policy"].security[sample["publisher"]] = previous
    assert check(sample, state=state).reason == "metadata_rollback"
    sample["policy"].security[sample["publisher"]] = security_metadata(
        sample["root"],
        revision=2,
        issued_at=sample["now"] - 1,
        expires_at=sample["now"] + 301,
    )
    assert check(sample, state=state).reason == "metadata_equivocation"
    assert state["revisions"][sample["publisher"]]["revision"] == 2


def test_missing_metadata_is_not_signature_only_allow(sample):
    sample["policy"].security.clear()
    assert check(sample).reason == "metadata_missing"


def test_offline_and_persisted_state(sample, tmp_path):
    sample["policy"].offline = True
    assert check(sample).metadata_status == "cached_valid"
    path = tmp_path / "state.json"
    assert (
        verify_persisted(sample["release"], sample["policy"], state_path=path).decision
        == "allow"
    )
    path.write_text("corrupt", encoding="utf-8")
    with pytest.raises(IdentityError, match="security_state_invalid"):
        verify_persisted(sample["release"], sample["policy"], state_path=path)


def test_build_and_observed_version_conflict(sample, tmp_path):
    history = {
        sample["wanted"]["skill_id"] + "@0.1.0": sample["wanted"]["manifest_digest"]
    }
    (sample["content"] / "SKILL.md").write_text("new content", encoding="utf-8")
    with pytest.raises(IdentityError, match="release_conflict"):
        build_release(
            sample["content"],
            tmp_path / "refused",
            sample["key"],
            sample["auth"],
            history=history,
        )
    state = empty_state()
    assert check(sample, state=state).decision == "allow"
    other = tmp_path / "conflicting"
    build_release(sample["content"], other, sample["key"], sample["auth"], history={})
    assert (
        verify_release(other, sample["policy"], state=state).reason
        == "release_conflict"
    )


def test_rotation_and_scope(sample, tmp_path):
    key = Ed25519PrivateKey.generate()
    auth = authorize(
        sample["root"],
        public_hex(key),
        ["sample"],
        not_before=0,
        expires_at=sample["now"] + 300,
    )
    path = tmp_path / "rotated"
    build_release(sample["content"], path, key, auth, history={})
    result = verify_release(path, sample["policy"], state=empty_state())
    assert (
        result.decision == "allow" and result.skill_id == sample["wanted"]["skill_id"]
    )
    bad = authorize(
        sample["root"],
        public_hex(key),
        ["different"],
        not_before=0,
        expires_at=sample["now"] + 300,
    )
    with pytest.raises(IdentityError, match="authorization_scope_mismatch"):
        build_release(sample["content"], tmp_path / "bad-scope", key, bad, history={})


def test_exact_lock_and_old_receipt(sample, tmp_path):
    state = empty_state()
    lock = resolve_lock(
        [sample["wanted"]], [sample["release"]], sample["policy"], state=state
    )
    assert verify_lock(lock, [sample["release"]], sample["policy"], state=state) == lock
    assert "source" not in json.dumps(lock)
    wrong = copy.deepcopy(lock)
    wrong["releases"][0]["content_digest"] = "0" * 64
    with pytest.raises(IdentityError, match="lock_mismatch"):
        verify_lock(wrong, [sample["release"]], sample["policy"], state=state)
    with pytest.raises(IdentityError, match="dependency_missing"):
        resolve_lock([sample["wanted"]], [], sample["policy"], state=state)
    (sample["release"] / "content/SKILL.md").write_text("changed", encoding="utf-8")
    with pytest.raises(IdentityError):
        verify_lock(lock, [sample["release"]], sample["policy"], state=state)


def test_lock_policy_binding_and_name_ambiguity(sample):
    state = empty_state()
    lock = resolve_lock(
        [sample["wanted"]], [sample["release"]], sample["policy"], state=state
    )
    sample["policy"].offline = True
    with pytest.raises(IdentityError, match="policy_mismatch"):
        verify_lock(lock, [sample["release"]], sample["policy"], state=state)
    one = check(sample)
    two = copy.deepcopy(one)
    two.skill_id += "-fork"
    with pytest.raises(IdentityError, match="dependency_ambiguous"):
        resolve_name("sample", [("sample", one), ("sample", two)])


def test_snapshot_remains_fixed_after_new_version(sample, tmp_path):
    state = empty_state()
    snapshot = snapshot_release(
        sample["release"], tmp_path / "store", sample["policy"], state=state
    )
    original = (snapshot / "content/SKILL.md").read_bytes()
    (sample["content"] / "SKILL.md").write_text("new version", encoding="utf-8")
    assert (snapshot / "content/SKILL.md").read_bytes() == original
    assert verify_release(snapshot, sample["policy"], state=state).decision == "allow"


def test_failed_lock_remembers_valid_security_only(sample):
    state = empty_state()
    assert check(sample, state=state).decision == "allow"
    old = copy.deepcopy(sample["policy"])
    sample["policy"].security[sample["publisher"]] = security_metadata(
        sample["root"],
        revision=2,
        issued_at=0,
        expires_at=sample["now"] + 300,
        disabled=True,
    )
    with pytest.raises(IdentityError, match="publisher_disabled"):
        resolve_lock(
            [sample["wanted"]], [sample["release"]], sample["policy"], state=state
        )
    assert (
        verify_release(sample["release"], old, state=state).reason
        == "metadata_rollback"
    )
    sample["policy"].security[sample["publisher"]] = security_metadata(
        sample["root"], revision=9, issued_at=0, expires_at=sample["now"] - 1
    )
    assert check(sample, state=state).reason == "metadata_expired"
    assert state["revisions"][sample["publisher"]]["revision"] == 2


def test_public_signature_vector():
    # Public non-production vector; its discarded private key is not part of this repository.
    env = {
        "payload": {
            "revision": 1,
            "schema": "bensz-skill-identity/v1/test-vector",
            "text": "公开非生产测试向量",
        },
        "public_key": "5df6cc789af773cb422c8a60cae314a8c5e2dd0398556666c3b5b0fba4e10c1e",
        "signature": "0a6f856d389a78c01033c52341a1ceda6753f35f82b037670322b62a0e47ddbfa3c6e9e1750490a968f588bb592aaca4dc137d7f681e2d4696462ea661dce20c",
    }
    assert (
        digest(authenticate(env, "manifest"))
        == "b70a14a76f8ee769ad24db883a659077464f1fad69b24b96ad8b3e1762c241dc"
    )
    with pytest.raises(IdentityError, match="signature_invalid"):
        authenticate(env, "security")


def test_external_distributor_identity(sample, tmp_path):
    (sample["content"] / "config.yaml").unlink()
    external = {k: sample["wanted"][k] for k in ("skill_id", "version")}
    release = tmp_path / "distributed"
    build_release(
        sample["content"],
        release,
        sample["key"],
        sample["auth"],
        external_identity=external,
        history={},
    )
    assert (
        verify_release(release, sample["policy"], state=empty_state()).decision
        == "allow"
    )


def test_signed_transitive_dependency_and_conflict(sample, tmp_path):
    from bensz_skill_identity.protocol import read_config
    import yaml

    info = read_config(sample["content"] / "config.yaml")
    info["skill_info"]["identity"]["skill_key"] = "parent"
    (sample["content"] / "config.yaml").write_text(
        yaml.safe_dump(info), encoding="utf-8"
    )
    auth = authorize(
        sample["root"],
        public_hex(sample["key"]),
        ["parent"],
        not_before=0,
        expires_at=sample["now"] + 300,
    )
    parent = tmp_path / "parent"
    wanted = build_release(
        sample["content"],
        parent,
        sample["key"],
        auth,
        dependencies=[sample["wanted"]],
        history={},
    )
    lock = resolve_lock(
        [wanted], [parent, sample["release"]], sample["policy"], state=empty_state()
    )
    assert len(lock["releases"]) == 2
    with pytest.raises(IdentityError, match="dependency_missing"):
        resolve_lock([wanted], [parent], sample["policy"], state=empty_state())
    bad = {**sample["wanted"], "content_digest": "0" * 64}
    with pytest.raises(IdentityError, match="dependency_conflict"):
        resolve_lock(
            [wanted, bad],
            [parent, sample["release"]],
            sample["policy"],
            state=empty_state(),
        )


def test_two_real_publishers_same_name_and_stable_rename(sample, tmp_path):
    from bensz_skill_identity.protocol import read_config
    import yaml

    other_root = Ed25519PrivateKey.generate()
    other_public = public_hex(other_root)
    other_publisher = publisher_id(other_public)
    info = read_config(sample["content"] / "config.yaml")
    info["skill_info"]["identity"]["publisher_id"] = other_publisher
    (sample["content"] / "config.yaml").write_text(
        yaml.safe_dump(info), encoding="utf-8"
    )
    auth = authorize(
        other_root,
        public_hex(sample["key"]),
        ["sample"],
        not_before=0,
        expires_at=sample["now"] + 300,
    )
    second = tmp_path / "second-publisher"
    build_release(sample["content"], second, sample["key"], auth, history={})
    policy = sample["policy"]
    policy.roots[other_publisher] = other_public
    policy.minimum_revisions[other_publisher] = 1
    policy.security[other_publisher] = security_metadata(
        other_root, revision=1, issued_at=0, expires_at=sample["now"] + 300
    )
    one = check(sample)
    two = verify_release(second, policy, state=empty_state())
    assert one.decision == two.decision == "allow" and one.skill_id != two.skill_id
    with pytest.raises(IdentityError, match="dependency_ambiguous"):
        resolve_name("display-name", [("display-name", one), ("display-name", two)])
    info["skill_info"]["name"] = "renamed-display"
    info["skill_info"]["version"] = "0.1.1"
    (sample["content"] / "config.yaml").write_text(
        yaml.safe_dump(info), encoding="utf-8"
    )
    renamed = tmp_path / "renamed"
    build_release(sample["content"], renamed, sample["key"], auth, history={})
    assert verify_release(renamed, policy, state=empty_state()).skill_id == two.skill_id


def test_build_does_not_delete_competing_output(sample, tmp_path, monkeypatch):
    from pathlib import Path

    output = tmp_path / "contended"
    original = Path.mkdir

    def competing_creator(path, *args, **kwargs):
        if path == output:
            original(path, *args, **kwargs)
            (path / "other-builder").write_text("keep", encoding="utf-8")
            raise FileExistsError("another builder won")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", competing_creator)
    with pytest.raises(FileExistsError):
        build_release(
            sample["content"], output, sample["key"], sample["auth"], history={}
        )
    assert (output / "other-builder").read_text(encoding="utf-8") == "keep"


def test_build_cleans_only_its_own_partial_output(sample, tmp_path, monkeypatch):
    import bensz_skill_identity.release as release_module

    output = tmp_path / "own-partial"

    def fail_copy(*args, **kwargs):
        raise OSError("injected copy failure")

    monkeypatch.setattr(release_module.shutil, "copytree", fail_copy)
    with pytest.raises(OSError):
        build_release(
            sample["content"], output, sample["key"], sample["auth"], history={}
        )
    assert not output.exists()


def test_dependency_cycle_guard_is_a_graph_unit_test(sample, monkeypatch):
    """Synthetic graph unit only: circular exact hashes are not signed fixtures."""
    from pathlib import Path
    from types import SimpleNamespace
    import bensz_skill_identity.dependencies as graph

    one = {**sample["wanted"], "manifest_digest": "0" * 64}
    two = {
        **sample["wanted"],
        "skill_id": sample["wanted"]["skill_id"] + "-child",
        "manifest_digest": "1" * 64,
    }
    manifests = {
        "one": {
            "skill_id": one["skill_id"],
            "version": one["version"],
            "test_digest": one["manifest_digest"],
            "dependencies": [two],
        },
        "two": {
            "skill_id": two["skill_id"],
            "version": two["version"],
            "test_digest": two["manifest_digest"],
            "dependencies": [one],
        },
    }
    monkeypatch.setattr(
        graph,
        "inspect_release",
        lambda candidate, **kwargs: (manifests[candidate.name], None, None),
    )
    monkeypatch.setattr(graph, "digest", lambda value: value["test_digest"])
    monkeypatch.setattr(
        graph,
        "verify_release",
        lambda *args, **kwargs: SimpleNamespace(decision="allow", reason="ok"),
    )
    with pytest.raises(IdentityError, match="dependency_cycle"):
        graph.resolve_lock(
            [one], [Path("one"), Path("two")], sample["policy"], state=empty_state()
        )
