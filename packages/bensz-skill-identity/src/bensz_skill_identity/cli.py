from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from .crypto import authorize, security_metadata
from .dependencies import resolve_lock, verify_lock
from .protocol import SCHEMA, IdentityError, canonical, load_json, read_file, require
from .publisher import initialize_publisher
from .release import TrustPolicy, build_release
from .state import state_transaction, verify_persisted
from .storage import install_release, recover_install


def _private(path: Path):
    try:
        key = load_pem_private_key(read_file(path, 16384), password=None)
        require(isinstance(key, Ed25519PrivateKey), "invalid_key")
        return key
    except (ValueError, TypeError) as exc:
        raise IdentityError("invalid_key") from exc


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Signed Skill releases; file verification only"
    )
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("capabilities")
    p = sub.add_parser("init", help="Create or validate the standard local publisher identity")
    p.add_argument(
        "--config-dir", type=Path,
        help="Override ~/.bensz-skills/config; keep the standard filenames",
    )
    for command in ("authorize", "security"):
        p = sub.add_parser(command)
        p.add_argument("--private-key", type=Path, required=True)
        p.add_argument("--output", type=Path, required=True)
        p.add_argument("--expires-at", type=int, required=True)
        if command == "authorize":
            p.add_argument("--release-public-key", required=True)
            p.add_argument("--skill-key", action="append", required=True)
            p.add_argument("--not-before", type=int, default=0)
        else:
            p.add_argument("--revision", type=int, required=True)
            p.add_argument("--issued-at", type=int, required=True)
            p.add_argument("--revoked-key", action="append", default=[])
            p.add_argument("--revoked-release", action="append", default=[])
            p.add_argument("--disabled", action="store_true")
    p = sub.add_parser("build")
    p.add_argument("--content", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--private-key", type=Path, required=True)
    p.add_argument("--authorization", type=Path, required=True)
    p.add_argument("--dependencies", type=Path)
    p.add_argument(
        "--external-identity",
        type=Path,
        help="Explicit distributor identity for content without config.yaml",
    )
    p.add_argument("--history", type=Path, required=True)
    for command in ("verify", "lock", "verify-lock", "install"):
        p = sub.add_parser(command)
        p.add_argument("--trust-store", type=Path, required=True)
        if command in ("verify", "lock", "verify-lock"):
            p.add_argument("--state", type=Path, required=True)
        if command in ("verify", "install"):
            p.add_argument("--release", type=Path, required=True)
            p.add_argument("--request", type=Path)
        if command in ("lock", "verify-lock"):
            p.add_argument("--candidate", type=Path, action="append", required=True)
            p.add_argument("--input", type=Path, required=True)
        if command == "install":
            p.add_argument("--target", type=Path, required=True)
            p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("recover")
    p.add_argument("--target", type=Path, required=True)
    return result


def execute(args) -> tuple[dict, int]:
    command = args.command
    if command == "init":
        return initialize_publisher(args.config_dir), 0
    if command == "capabilities":
        return {
            "schema": SCHEMA + "/capabilities",
            "protocol": 1,
            "assurance": "files_verified",
            "strict_install": True,
            "host_binding": False,
        }, 0
    if command in ("authorize", "security"):
        require(
            not args.output.exists() and not args.output.is_symlink(), "output_exists"
        )
        if command == "authorize":
            value = authorize(
                _private(args.private_key),
                args.release_public_key,
                args.skill_key,
                not_before=args.not_before,
                expires_at=args.expires_at,
            )
        else:
            value = security_metadata(
                _private(args.private_key),
                revision=args.revision,
                issued_at=args.issued_at,
                expires_at=args.expires_at,
                revoked_keys=args.revoked_key,
                revoked_releases=args.revoked_release,
                disabled=args.disabled,
            )
        with args.output.open("xb") as stream:
            stream.write(canonical(value))
        return {"schema": SCHEMA + "/operation", "reason": "ok"}, 0
    if command == "build":
        created = False
        try:
            with state_transaction(args.history) as history:
                value = build_release(
                    args.content,
                    args.output,
                    _private(args.private_key),
                    load_json(args.authorization),
                    dependencies=load_json(args.dependencies)
                    if args.dependencies
                    else [],
                    history=history["releases"],
                    external_identity=load_json(args.external_identity)
                    if args.external_identity
                    else None,
                )
                created = True
        except BaseException:
            if created:
                shutil.rmtree(args.output)
            raise
        return {"schema": SCHEMA + "/operation", "reason": "ok", **value}, 0
    if command == "recover":
        recover_install(args.target)
        return {"schema": SCHEMA + "/operation", "reason": "ok"}, 0
    policy = TrustPolicy.from_dict(load_json(args.trust_store))
    if command == "install":
        value = install_release(
            args.release,
            args.target,
            policy,
            request=load_json(args.request) if args.request else None,
            dry_run=args.dry_run,
        )
        return value, 0
    if command == "verify":
        result = verify_persisted(
            args.release,
            policy,
            state_path=args.state,
            request=load_json(args.request) if args.request else None,
        )
        return (
            result.to_dict(),
            0
            if result.decision == "allow"
            else 2
            if result.decision == "trust_required"
            else 3,
        )
    with state_transaction(args.state) as state:
        fn = resolve_lock if command == "lock" else verify_lock
        value = fn(load_json(args.input), args.candidate, policy, state=state)
    return value, 0


def main(argv=None) -> int:
    try:
        value, code = execute(parser().parse_args(argv))
    except IdentityError as exc:
        value, code = (
            {"schema": SCHEMA + "/error", "reason": exc.code, "path": exc.path},
            3,
        )
    except (OSError, ValueError, TypeError, KeyError):
        value, code = {"schema": SCHEMA + "/error", "reason": "io_or_input_error"}, 4
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return code
