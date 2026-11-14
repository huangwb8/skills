"""Explicit durable state transactions; verification never silently resets corrupt state."""

from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .protocol import IdentityError, canonical, load_json, require
from .release import empty_state, validate_state, verify_release


def atomic_json(path: Path, value: dict) -> None:
    require(not path.is_symlink(), "unsafe_path")
    data = canonical(value)
    fd, name = tempfile.mkstemp(prefix=".bsi-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def file_lock(path: Path):
    require(not path.is_symlink(), "unsafe_path")
    fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        try:
            if os.name == "nt":
                import msvcrt

                if os.fstat(fd).st_size == 0:
                    os.write(fd, b"0")
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise IdentityError("state_locked") from exc
        yield
    finally:
        os.close(fd)  # OS releases the lock on normal exit and process death.


def read_state(path: Path) -> dict:
    if not path.exists() and not path.is_symlink():
        return empty_state()
    try:
        state = load_json(path)
        validate_state(state)
        return state
    except (IdentityError, OSError) as exc:
        raise IdentityError("security_state_invalid") from exc


def state_lock_path(path: Path) -> Path:
    return path.with_name(path.name + ".lock")


@contextmanager
def state_transaction(path: Path):
    """Always persist authenticated revision updates, including policy denials."""
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.parent.is_symlink(), "unsafe_path")
    with file_lock(state_lock_path(path)):
        state = read_state(path)
        try:
            yield state
        finally:
            try:
                atomic_json(path, state)
            except OSError as exc:
                raise IdentityError("security_state_commit_failed") from exc


def verify_persisted(
    release: Path, policy, *, state_path: Path, request=None, now=None
):
    """Callers explicitly authorize state_path writes. No automatic root trust."""
    with state_transaction(state_path) as state:
        return verify_release(release, policy, state=state, request=request, now=now)
