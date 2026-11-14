"""Opt-in local publisher initialization; secrets never enter results or logs."""

from __future__ import annotations

import os
import re
import shlex
import stat
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    load_pem_private_key,
)

from .crypto import public_hex
from .protocol import SCHEMA, publisher_id, read_file, require
from .state import file_lock

ENV_NAMES = (
    "BSI_PUBLISHER_ID",
    "BSI_ROOT_PUBLIC_KEY",
    "BSI_RELEASE_PUBLIC_KEY",
    "BSI_ROOT_PRIVATE_KEY_FILE",
    "BSI_RELEASE_PRIVATE_KEY_FILE",
)
MAX_ENV_BYTES = 1024 * 1024


def _directory(path: Path) -> None:
    require(not path.is_symlink(), "unsafe_path")
    if not path.exists():
        _directory(path.parent)
        try:
            path.mkdir(mode=0o700)
            path.chmod(0o700)
        except FileExistsError:
            pass  # Another initializer may have created the directory.
    require(path.is_dir() and not path.is_symlink(), "unsafe_path")


def _private_permissions(path: Path) -> None:
    info = path.lstat()
    require(
        stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
        "unsupported_file_type",
    )
    if os.name != "nt":
        require(
            info.st_uid == os.getuid() and not info.st_mode & 0o7077,
            "publisher_permissions_invalid",
        )


def _environment(path: Path) -> tuple[bytes | None, dict[str, str]]:
    require(not path.is_symlink(), "unsafe_path")
    if not path.exists():
        return None, {}
    raw = read_file(path, MAX_ENV_BYTES)
    try:
        text = raw.decode("utf-8")
    except UnicodeError:
        require(False, "publisher_config_invalid")
    values = {}
    for line in text.splitlines():
        match = re.match(r"^[ \t]*(?:export[ \t]+)?(BSI_\w+)\b(.*)$", line)
        if match is None or match[1] not in ENV_NAMES:
            continue
        name, tail = match.groups()
        tail = tail.lstrip(" \t")
        require(name not in values and tail.startswith("="), "publisher_config_invalid")
        try:
            parts = shlex.split(tail[1:], comments=True)
        except ValueError:
            require(False, "publisher_config_invalid")
        require(len(parts) == 1 and "\0" not in parts[0], "publisher_config_invalid")
        values[name] = parts[0]
    require(not values or set(values) == set(ENV_NAMES), "publisher_config_invalid")
    return raw, values


def _load_private(path: Path) -> Ed25519PrivateKey:
    _private_permissions(path)
    try:
        key = load_pem_private_key(read_file(path, 16384), password=None)
    except (ValueError, TypeError):
        require(False, "invalid_key")
    require(isinstance(key, Ed25519PrivateKey), "invalid_key")
    return key


def _write_private(path: Path, key: Ed25519PrivateKey) -> None:
    data = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    with os.fdopen(_create_file(path), "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _create_file(path: Path) -> int:
    fd = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600
    )
    try:
        if os.name != "nt":
            os.fchmod(fd, 0o600)
    except BaseException:
        os.close(fd)
        raise
    return fd


def _configure(path: Path, original: bytes | None, values: dict[str, str]) -> None:
    addition = "\n# BSI publisher identity\n" + "".join(
        f"{name}={shlex.quote(value)}\n" for name, value in values.items()
    )
    data = original or b""
    if data and not data.endswith(b"\n"):
        data += b"\n"
    data += addition.encode("utf-8")
    require(len(data) <= MAX_ENV_BYTES, "limit_exceeded")
    fd, temporary = tempfile.mkstemp(prefix=".bsi-env-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            if os.name != "nt":
                os.fchmod(stream.fileno(), 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        current, _ = _environment(path)
        require(current == original, "publisher_config_changed")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def initialize_publisher(config_dir: Path | None = None) -> dict:
    """Create or revalidate a local publisher. Never rotate, trust or authorize it.

    A complete existing key pair can restore missing public configuration. An
    incomplete pair requires manual recovery; existing private bytes are kept.
    Returns public identity and state only, never local paths or PEM material.
    """
    selected = (
        Path.home() / ".bensz-skills" / "config"
        if config_dir is None
        else Path(config_dir).expanduser()
    )
    directory = Path(os.path.abspath(selected))
    require(not any(c in str(directory) for c in "\0\r\n"), "unsafe_path")
    _directory(directory)
    lock = directory / ".bsi-init.lock"
    try:
        os.close(_create_file(lock))
    except FileExistsError:
        _private_permissions(lock)
    with file_lock(lock):
        env = directory / "remote.env"
        original, existing = _environment(env)
        keys = directory / "bsi-keys"
        require(not keys.is_symlink(), "unsafe_path")
        created = False
        if not keys.exists():
            require(not existing, "publisher_incomplete")
            keys.mkdir(mode=0o700)
            keys.chmod(0o700)
            created = True
            # Keep partial material on failure: retries must never change identity.
            _write_private(keys / "root.pem", Ed25519PrivateKey.generate())
            _write_private(keys / "release.pem", Ed25519PrivateKey.generate())
        require(keys.is_dir(), "unsafe_path")
        if os.name != "nt":
            info = keys.stat()
            require(
                info.st_uid == os.getuid() and not info.st_mode & 0o7077,
                "publisher_permissions_invalid",
            )
        for name in ("root.pem", "release.pem"):
            require(not (keys / name).is_symlink(), "unsafe_path")
            require((keys / name).exists(), "publisher_incomplete")
        root = public_hex(_load_private(keys / "root.pem"))
        release = public_hex(_load_private(keys / "release.pem"))
        require(root != release, "invalid_key")
        publisher = publisher_id(root)
        values = dict(
            zip(
                ENV_NAMES,
                (
                    publisher,
                    root,
                    release,
                    str(keys / "root.pem"),
                    str(keys / "release.pem"),
                ),
            )
        )
        if existing:
            require(existing == values, "publisher_identity_mismatch")
            _private_permissions(env)
            state = "reused"
        else:
            _configure(env, original, values)
            state = "created" if created else "recovered"
        return {
            "schema": SCHEMA + "/publisher",
            "reason": "ok",
            "state": state,
            "publisher_id": publisher,
            "root_public_key": root,
            "release_public_key": release,
        }
