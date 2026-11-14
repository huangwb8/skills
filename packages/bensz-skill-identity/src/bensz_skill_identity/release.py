from __future__ import annotations

import copy
import hashlib
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .crypto import authenticate, public_hex, sign
from .protocol import (
    SCHEMA,
    IdentityError,
    Limits,
    canonical,
    digest,
    fields,
    hex_value,
    integer,
    inventory,
    load_json,
    publisher_id,
    read_identity,
    require,
    safe_path,
    skill_key,
    validate_id,
    version,
)


def requirement(value: object) -> dict:
    obj = fields(value, {"skill_id", "version", "manifest_digest", "content_digest"})
    validate_id(obj["skill_id"])
    version(obj["version"])
    hex_value(obj["manifest_digest"])
    hex_value(obj["content_digest"])
    return obj


def build_manifest(
    content: Path,
    dependencies: list[dict] | None = None,
    *,
    limits: Limits = Limits(),
    external_identity: dict | None = None,
) -> dict:
    config_exists = (content / "config.yaml").exists() or (
        content / "config.yaml"
    ).is_symlink()
    claim = (
        read_identity(content / "config.yaml") if config_exists else external_identity
    )
    require(claim is not None, "identity_absent")
    fields(claim, {"skill_id", "version"})
    validate_id(claim["skill_id"])
    version(claim["version"])
    require(not config_exists or external_identity is None, "identity_mismatch")
    entries = inventory(content, limits)
    require(
        any(e["path"] == "SKILL.md" and e["type"] == "file" for e in entries),
        "file_missing",
    )
    deps = dependencies or []
    require(type(deps) is list and len(deps) <= 256)
    for item in deps:
        requirement(item)
    require(len({d["skill_id"] for d in deps}) == len(deps), "dependency_conflict")
    return {
        "schema": SCHEMA + "/manifest",
        **claim,
        "identity_source": "config" if config_exists else "external",
        "files": entries,
        "content_digest": digest(entries),
        "dependencies": sorted(deps, key=lambda d: d["skill_id"]),
    }


def _authorization(envelope: dict, manifest: dict, public: str, now: int) -> str:
    payload = authenticate(envelope, "authorization")
    fields(
        payload,
        {
            "schema",
            "publisher_id",
            "release_public_key",
            "skill_keys",
            "not_before",
            "expires_at",
        },
    )
    require(payload["schema"] == SCHEMA + "/authorization", "unsupported_protocol")
    root = envelope["public_key"]
    publisher = publisher_id(root)
    require(
        payload["publisher_id"] == publisher
        and manifest["skill_id"].split("/")[2] == publisher,
        "identity_mismatch",
    )
    require(hex_value(payload["release_public_key"]) == public, "signature_invalid")
    keys = payload["skill_keys"]
    require(type(keys) is list and 0 < len(keys) <= 256)
    for key in keys:
        skill_key(key)
    require(
        manifest["skill_id"].rsplit("/", 1)[1] in keys, "authorization_scope_mismatch"
    )
    integer(payload["not_before"])
    integer(payload["expires_at"])
    require(payload["not_before"] < payload["expires_at"])
    require(payload["not_before"] <= now, "authorization_not_yet_valid")
    require(now < payload["expires_at"], "authorization_expired")
    return root


def build_release(
    content: Path,
    output: Path,
    release_key,
    authorization: dict,
    *,
    dependencies: list[dict] | None = None,
    history: dict,
    now: int | None = None,
    limits: Limits = Limits(),
    external_identity: dict | None = None,
) -> dict:
    """Build a new directory, never overwrite. Caller persists publisher history."""
    now = int(time.time()) if now is None else integer(now)
    require(not output.exists() and not output.is_symlink(), "output_exists")
    # Do not put an output inside its input tree.
    require(not output.resolve().is_relative_to(content.resolve()), "unsafe_path")
    manifest = build_manifest(
        content, dependencies, limits=limits, external_identity=external_identity
    )
    _authorization(authorization, manifest, public_hex(release_key), now)
    identity_version = manifest["skill_id"] + "@" + manifest["version"]
    md = digest(manifest)
    require(history.get(identity_version, md) == md, "release_conflict")
    created = False
    try:
        output.mkdir(parents=True)
        created = True
        shutil.copytree(content, output / "content", symlinks=True)
        require(
            build_manifest(
                output / "content",
                dependencies,
                limits=limits,
                external_identity=external_identity,
            )
            == manifest,
            "file_changed",
        )
        (output / "manifest.json").write_bytes(
            canonical(sign(manifest, release_key, "manifest"))
        )
        (output / "authorization.json").write_bytes(canonical(authorization))
        history[identity_version] = md
    except BaseException:
        if created and output.exists():
            shutil.rmtree(output)
        raise
    return {
        "skill_id": manifest["skill_id"],
        "version": manifest["version"],
        "manifest_digest": md,
        "content_digest": manifest["content_digest"],
    }


@dataclass
class TrustPolicy:
    """Explicit local roots and current root-signed metadata, never TOFU."""

    roots: dict[str, str] = field(default_factory=dict)
    security: dict[str, dict] = field(default_factory=dict)
    minimum_revisions: dict[str, int] = field(default_factory=dict)
    offline: bool = False

    def to_dict(self) -> dict:
        return {"schema": SCHEMA + "/policy", **asdict(self)}

    @classmethod
    def from_dict(cls, value: dict) -> TrustPolicy:
        fields(value, {"schema", "roots", "security", "minimum_revisions", "offline"})
        require(value["schema"] == SCHEMA + "/policy", "unsupported_protocol")
        require(
            type(value["roots"]) is dict
            and type(value["security"]) is dict
            and type(value["minimum_revisions"]) is dict
            and type(value["offline"]) is bool
        )
        for pub, public in value["roots"].items():
            require(publisher_id(public) == pub, "invalid_identity")
            require(pub in value["minimum_revisions"], "metadata_bootstrap_required")
            integer(value["minimum_revisions"][pub])
        require(set(value["security"]) <= set(value["roots"]))
        require(set(value["minimum_revisions"]) == set(value["roots"]))
        return cls(**{k: copy.deepcopy(v) for k, v in value.items() if k != "schema"})


def empty_state() -> dict:
    return {"schema": SCHEMA + "/state", "revisions": {}, "releases": {}}


def validate_state(state: dict) -> None:
    fields(state, {"schema", "revisions", "releases"})
    require(
        state["schema"] == SCHEMA + "/state"
        and type(state["revisions"]) is dict
        and type(state["releases"]) is dict,
        "security_state_invalid",
    )
    for pub, item in state["revisions"].items():
        require(
            type(pub) is str and pub.startswith("ed25519-"), "security_state_invalid"
        )
        fields(item, {"revision", "digest"})
        integer(item["revision"])
        hex_value(item["digest"])
    for key, value in state["releases"].items():
        require(type(key) is str and "@" in key, "security_state_invalid")
        sid, ver = key.rsplit("@", 1)
        validate_id(sid)
        version(ver)
        hex_value(value)


@dataclass
class VerificationResult:
    verification: str = "failed"
    decision: str = "deny"
    reason: str = "invalid_metadata"
    assurance: str = "none"
    skill_id: str | None = None
    version: str | None = None
    manifest_digest: str | None = None
    content_digest: str | None = None
    request_digest: str | None = None
    policy_digest: str | None = None
    security_digest: str | None = None
    security_revision: int | None = None
    metadata_status: str = "unchecked"
    checked_at: int = 0
    path: str = ""

    def to_dict(self) -> dict:
        return {"schema": SCHEMA + "/result", **asdict(self)}

    def as_requirement(self) -> dict:
        require(
            self.verification == "verified" and self.decision == "allow", self.reason
        )
        return {
            k: getattr(self, k)
            for k in ("skill_id", "version", "manifest_digest", "content_digest")
        }


def _check_security(
    policy: TrustPolicy, publisher: str, root: str, state: dict, now: int
) -> dict:
    require(publisher in policy.security, "metadata_missing")
    env = policy.security[publisher]
    meta = authenticate(env, "security", root)
    fields(
        meta,
        {
            "schema",
            "publisher_id",
            "revision",
            "issued_at",
            "expires_at",
            "revoked_keys",
            "revoked_releases",
            "disabled",
        },
    )
    require(meta["schema"] == SCHEMA + "/security", "unsupported_protocol")
    require(meta["publisher_id"] == publisher, "identity_mismatch")
    integer(meta["revision"])
    integer(meta["issued_at"])
    integer(meta["expires_at"])
    require(meta["issued_at"] < meta["expires_at"])
    require(meta["issued_at"] <= now, "metadata_not_yet_valid")
    require(now < meta["expires_at"], "metadata_expired")
    require(type(meta["disabled"]) is bool)
    for key in ("revoked_keys", "revoked_releases"):
        require(type(meta[key]) is list)
        for item in meta[key]:
            hex_value(item)
    previous = state["revisions"].get(publisher)
    require(
        meta["revision"] >= policy.minimum_revisions[publisher], "metadata_rollback"
    )
    if previous:
        require(meta["revision"] >= previous["revision"], "metadata_rollback")
        require(
            meta["revision"] != previous["revision"]
            or digest(env) == previous["digest"],
            "metadata_equivocation",
        )
    # Accepted authenticated security metadata is retained even when it revokes this release.
    state["revisions"][publisher] = {
        "revision": meta["revision"],
        "digest": digest(env),
    }
    return meta


def inspect_release(
    release: Path,
    *,
    limits: Limits = Limits(),
    now: int | None = None,
    content: Path | None = None,
) -> tuple[dict, str, str]:
    require(release.is_dir() and not release.is_symlink(), "unsupported_file_type")
    layout = {"manifest.json", "authorization.json"} | (
        {"content"} if content is None else set()
    )
    require({p.name for p in release.iterdir()} == layout, "release_layout_mismatch")
    env = load_json(release / "manifest.json")
    manifest = authenticate(env, "manifest")
    fields(
        manifest,
        {
            "schema",
            "skill_id",
            "version",
            "identity_source",
            "files",
            "content_digest",
            "dependencies",
        },
    )
    require(manifest["schema"] == SCHEMA + "/manifest", "unsupported_protocol")
    validate_id(manifest["skill_id"])
    version(manifest["version"])
    root = _authorization(
        load_json(release / "authorization.json"),
        manifest,
        env["public_key"],
        int(time.time()) if now is None else now,
    )
    deps = manifest["dependencies"]
    require(type(deps) is list and len(deps) <= 256)
    for dep in deps:
        requirement(dep)
    require(manifest["identity_source"] in ("config", "external"))
    external = (
        {"skill_id": manifest["skill_id"], "version": manifest["version"]}
        if manifest["identity_source"] == "external"
        else None
    )
    expected = build_manifest(
        release / "content" if content is None else content,
        deps,
        limits=limits,
        external_identity=external,
    )
    if expected != manifest:
        old = (
            {e.get("path"): e for e in manifest["files"] if type(e) is dict}
            if type(manifest["files"]) is list
            else {}
        )
        new = {e["path"]: e for e in expected["files"]}
        for rel in sorted(set(old) | set(new)):
            safe_path(rel)
            if old.get(rel) != new.get(rel):
                raise IdentityError("file_mismatch", rel)
        raise IdentityError("identity_mismatch")
    return manifest, root, env["public_key"]


def verify_release(
    release: Path,
    policy: TrustPolicy,
    *,
    state: dict,
    request: dict | None = None,
    now: int | None = None,
    limits: Limits = Limits(),
    content: Path | None = None,
) -> VerificationResult:
    """Re-read bytes every call. Mutates explicit state; use verify_persisted for durable checks."""
    result = VerificationResult(checked_at=int(time.time()) if now is None else now)
    try:
        integer(result.checked_at)
        policy = TrustPolicy.from_dict(policy.to_dict())
        result.policy_digest = digest(policy.to_dict())
        result.request_digest = digest(request)
        validate_state(state)
        if request is not None:
            requirement(request)
        manifest, root, release_public = inspect_release(
            release, limits=limits, now=result.checked_at, content=content
        )
        result.skill_id = manifest["skill_id"]
        result.version = manifest["version"]
        result.manifest_digest = digest(manifest)
        result.content_digest = manifest["content_digest"]
        if request is not None:
            require(
                all(getattr(result, k) == v for k, v in request.items()),
                "request_mismatch",
            )
        result.verification = "verified"
        result.assurance = "files_verified"
        publisher = publisher_id(root)
        if policy.roots.get(publisher) != root:
            result.decision = "trust_required"
            result.reason = "publisher_untrusted"
            return result
        meta = _check_security(policy, publisher, root, state, result.checked_at)
        result.security_digest = digest(policy.security[publisher])
        result.security_revision = meta["revision"]
        result.metadata_status = (
            "cached_valid" if policy.offline else "locally_supplied_valid"
        )
        require(not meta["disabled"], "publisher_disabled")
        require(
            hashlib.sha256(bytes.fromhex(release_public)).hexdigest()
            not in meta["revoked_keys"],
            "key_revoked",
        )
        require(
            result.manifest_digest not in meta["revoked_releases"], "release_revoked"
        )
        key = result.skill_id + "@" + result.version
        require(
            state["releases"].get(key, result.manifest_digest)
            == result.manifest_digest,
            "release_conflict",
        )
        state["releases"][key] = result.manifest_digest
        result.decision = "allow"
        result.reason = "ok"
    except IdentityError as exc:
        result.reason = exc.code
        result.path = exc.path
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        result.reason = "invalid_metadata"
    return result
