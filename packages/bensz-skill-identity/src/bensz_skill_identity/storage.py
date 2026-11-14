"""Local signed installation with same-filesystem staging and recoverable journal.

All cooperating writers must use this lock. This is not a hostile-user sandbox.
"""

from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from .protocol import (
    SCHEMA,
    IdentityError,
    digest,
    fields,
    load_json,
    require,
    skill_key,
)
from .release import inspect_release, verify_release
from .state import atomic_json, file_lock, read_state, state_transaction

CONTROL = ".bensz-skill-identity"


def _control(target: Path, create: bool = False) -> Path:
    require(not target.is_symlink(), "unsafe_path")
    control = target / CONTROL
    require(not control.is_symlink(), "unsafe_path")
    if create:
        target.mkdir(parents=True, exist_ok=True)
        control.mkdir(exist_ok=True)
        require(not (control / "records").is_symlink(), "unsafe_path")
        (control / "records").mkdir(exist_ok=True)
    require(not control.exists() or control.is_dir(), "unsafe_path")
    require(not (control / "records").is_symlink(), "unsafe_path")
    return control


def _recover(target: Path, control: Path) -> None:
    journal = control / "journal.json"
    if not journal.exists() and not journal.is_symlink():
        return
    try:
        data = load_json(journal)
        fields(data, {"schema", "name", "old_record", "new_record", "had_old"})
        require(data["schema"] == SCHEMA + "/transaction", "recovery_required")
        name = skill_key(data["name"])
        require(type(data["had_old"]) is bool, "recovery_required")
        dest, backup = target / name, control / "backup"
        record = control / "records" / (name + ".json")
        # A matching committed record is the transaction's commit point.
        committed = record.exists() and load_json(record) == data["new_record"]
        if committed:
            require(dest.is_dir() and not dest.is_symlink(), "recovery_required")
        else:
            if backup.exists():
                require(
                    not backup.is_symlink() and backup.is_dir(), "recovery_required"
                )
                if dest.exists():
                    require(
                        not dest.is_symlink() and dest.is_dir(), "recovery_required"
                    )
                    shutil.rmtree(dest)
                os.replace(backup, dest)
            elif not data["had_old"] and dest.exists():
                require(not dest.is_symlink() and dest.is_dir(), "recovery_required")
                shutil.rmtree(dest)
            elif data["had_old"]:
                require(dest.is_dir() and not dest.is_symlink(), "recovery_required")
            if data["old_record"] is None:
                record.unlink(missing_ok=True)
            else:
                atomic_json(record, data["old_record"])
        if backup.exists():
            shutil.rmtree(backup)
        stage = control / "staging"
        if stage.exists():
            require(not stage.is_symlink(), "recovery_required")
            shutil.rmtree(stage)
        journal.unlink()
    except (OSError, IdentityError, TypeError, KeyError) as exc:
        raise IdentityError("recovery_required") from exc


def recover_install(target: Path) -> None:
    control = _control(target)
    if not control.exists():
        return
    with file_lock(control / "install.lock"):
        _recover(target, control)


def verify_installation(target: Path, name: str, policy, *, now=None):
    """Reverify actual installed bytes, not the sidecar's previous verdict."""
    name = skill_key(name)
    control = _control(target)
    require(control.is_dir(), "identity_absent")
    with file_lock(control / "install.lock"):
        require(not (control / "journal.json").exists(), "recovery_required")
        record = load_json(control / "records" / (name + ".json"))
        require(
            type(record) is dict
            and record.get("schema") == SCHEMA + "/installation"
            and record.get("name") == name,
            "security_state_invalid",
        )
        from .protocol import hex_value

        md = hex_value(record.get("evidence_digest"))
        wanted = {
            k: record.get(k)
            for k in ("skill_id", "version", "manifest_digest", "content_digest")
        }
        with state_transaction(control / "state.json") as state:
            return verify_release(
                control / "releases" / md,
                policy,
                state=state,
                request=wanted,
                now=now,
                content=target / name,
            )


def install_release(
    release: Path,
    target: Path,
    policy,
    *,
    request: dict | None = None,
    dry_run: bool = False,
    now=None,
    _checkpoint=None,
) -> dict:
    """Install by stable skill_key. Same name with another identity is rejected.

    _checkpoint is a fault injection hook for transaction tests, never Skill code.
    """
    control = _control(target)
    prior = read_state(control / "state.json")
    import copy

    probe = copy.deepcopy(prior)
    initial = verify_release(release, policy, state=probe, request=request, now=now)
    if dry_run:
        require(initial.decision == "allow", initial.reason)
        name = skill_key(initial.skill_id.rsplit("/", 1)[1])
        require(not (control / "journal.json").exists(), "recovery_required")
        _check_existing(target, control, name, initial)
        return initial.to_dict()
    # Invalid/untrusted input with no accepted security observation stays read-only.
    if initial.decision != "allow" and probe["revisions"] == prior["revisions"]:
        raise IdentityError(initial.reason)
    control = _control(target, create=True)
    with file_lock(control / "install.lock"):
        _recover(target, control)
        with state_transaction(control / "state.json") as state:
            initial = verify_release(
                release, policy, state=state, request=request, now=now
            )
        require(initial.decision == "allow", initial.reason)
        name = skill_key(initial.skill_id.rsplit("/", 1)[1])
        _check_existing(target, control, name, initial)
        stage = control / "staging"
        require(not stage.is_symlink(), "unsafe_path")
        if stage.exists():
            shutil.rmtree(stage)
        # Both metadata and content are copied; no installation filters.
        inspect_release(release, now=now)
        shutil.copytree(release, stage, symlinks=True)
        with state_transaction(control / "state.json") as state:
            result = verify_release(
                stage, policy, state=state, request=request, now=now
            )
            require(result.decision == "allow", result.reason)
            require(result.as_requirement() == initial.as_requirement(), "file_changed")
            dest, backup = target / name, control / "backup"
            require(
                not backup.exists() and not backup.is_symlink(), "recovery_required"
            )
            record = control / "records" / (name + ".json")
            old_record = load_json(record) if record.exists() else None
            evidence = {
                file: load_json(stage / file)
                for file in ("manifest.json", "authorization.json")
            }
            evidence_digest = digest(evidence)
            new_record = {
                "schema": SCHEMA + "/installation",
                "name": name,
                **result.as_requirement(),
                "policy_digest": result.policy_digest,
                "security_revision": result.security_revision,
                "transaction_id": uuid.uuid4().hex,
                "evidence_digest": evidence_digest,
            }
            journal = {
                "schema": SCHEMA + "/transaction",
                "name": name,
                "had_old": dest.exists(),
                "old_record": old_record,
                "new_record": new_record,
            }
            atomic_json(control / "journal.json", journal)

            def checkpoint(phase):
                if _checkpoint:
                    _checkpoint(phase)

            try:
                checkpoint("prepared")
                if dest.exists():
                    require(dest.is_dir() and not dest.is_symlink(), "unsafe_path")
                    os.replace(dest, backup)
                checkpoint("old_moved")
                os.replace(stage / "content", dest)
                checkpoint("new_moved")
                # Metadata lives outside the signed content and survives recovery.
                metadata = control / "releases" / evidence_digest
                require(not metadata.parent.is_symlink(), "unsafe_path")
                metadata.parent.mkdir(exist_ok=True)
                require(not metadata.is_symlink(), "unsafe_path")
                ready = stage / "metadata"
                ready.mkdir()
                for file, envelope in evidence.items():
                    atomic_json(ready / file, envelope)
                    checkpoint("metadata_" + file)
                require(
                    digest({file: load_json(ready / file) for file in evidence})
                    == evidence_digest,
                    "file_changed",
                )
                if metadata.exists():
                    valid = {p.name for p in metadata.iterdir()} == set(evidence)
                    if valid:
                        try:
                            valid = (
                                digest(
                                    {
                                        file: load_json(metadata / file)
                                        for file in evidence
                                    }
                                )
                                == evidence_digest
                            )
                        except IdentityError:
                            valid = False
                    if not valid:
                        require(
                            not old_record
                            or old_record.get("evidence_digest") != evidence_digest,
                            "recovery_required",
                        )
                        shutil.rmtree(metadata)
                        os.replace(ready, metadata)
                else:
                    os.replace(ready, metadata)
                atomic_json(record, new_record)
                checkpoint("committed")
            except BaseException:
                _recover(target, control)
                raise
            _recover(target, control)
            return result.to_dict()


def _check_existing(target, control, name, result):
    dest = target / name
    require(not dest.is_symlink(), "unsafe_path")
    record = control / "records" / (name + ".json")
    require(not record.is_symlink(), "unsafe_path")
    if record.exists():
        old = load_json(record)
        require(
            type(old) is dict
            and old.get("schema") == SCHEMA + "/installation"
            and old.get("name") == name,
            "security_state_invalid",
        )
        require(old.get("skill_id") == result.skill_id, "identity_mismatch")
        if old.get("version") == result.version:
            require(
                old.get("manifest_digest") == result.manifest_digest, "release_conflict"
            )


def snapshot_release(
    release: Path, store: Path, policy, *, state: dict, now=None
) -> Path:
    """Explicit immutable-by-convention snapshot. No cleanup or host binding claim."""
    result = verify_release(release, policy, state=state, now=now)
    require(result.decision == "allow", result.reason)
    dest = store / digest(result.skill_id) / result.manifest_digest
    dest.parent.mkdir(parents=True, exist_ok=True)
    with file_lock(dest.parent / "snapshot.lock"):
        if not dest.exists():
            shutil.copytree(release, dest, symlinks=True)
        checked = verify_release(
            dest, policy, state=state, request=result.as_requirement(), now=now
        )
        require(checked.decision == "allow", checked.reason)
    return dest
