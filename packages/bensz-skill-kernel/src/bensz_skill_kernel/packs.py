"""Shared filesystem Pack infrastructure used by States and Verifiers.

State and Verifier packs intentionally keep different semantic adapters, but
their on-disk contract is the same: a package directory contains one Markdown
contract, optional metadata in ``index.json`` and an optional local entrypoint.
This module owns only that storage and process boundary.  It does not decide
what a state transition or a verification result means.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import signal
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Type


PACK_INDEX_PROTOCOL = "bensz-pack-index-v1"
_DIRECTORY_SENTINELS = frozenset({"", ".", ".."})


def version_key(version: str) -> tuple[tuple[int, Any], ...]:
    """Sort semantic-ish versions numerically while tolerating labels."""
    return tuple((0, int(part)) if part.isdigit() else (1, part) for part in re.split(r"[.-]", version))


def _raise(error_type: Type[Exception], message: str) -> None:
    raise error_type(message)


def load_pack_entries(
    root: str | os.PathLike[str],
    *,
    package_kind: str,
    contract_name: str,
    error_type: Type[Exception] = ValueError,
    recursive_without_index: bool = False,
) -> list[tuple[Path, Mapping[str, Any]]]:
    """Load and validate a Pack index, returning ``(contract, entry)`` pairs.

    The indexed form is authoritative when present.  It validates direct-child
    package names, keeps contracts inside their package directory, and rejects
    stale or missing entries.  Legacy roots without an index remain supported.
    """

    base = Path(root).expanduser().resolve()
    if not base.is_dir():
        return []

    index_path = base / "index.json"
    if index_path.is_file():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            _raise(error_type, f"invalid {package_kind} index: {exc.msg}")
        if (
            not isinstance(index, Mapping)
            or index.get("protocol") != PACK_INDEX_PROTOCOL
            or index.get("package_kind") != package_kind
            or not isinstance(index.get("entries"), list)
        ):
            _raise(error_type, f"{package_kind} index must use {PACK_INDEX_PROTOCOL} and contain entries")

        indexed: list[tuple[Path, Mapping[str, Any]]] = []
        declared: set[str] = set()
        for entry in index["entries"]:
            if not isinstance(entry, Mapping):
                _raise(error_type, f"{package_kind} index entries must be objects")
            directory = entry.get("directory")
            if (
                not isinstance(directory, str)
                or directory in _DIRECTORY_SENTINELS
                or "/" in directory
                or "\\" in directory
            ):
                _raise(error_type, f"{package_kind} index directories must be direct child names")
            if directory in declared:
                _raise(error_type, f"duplicate {package_kind} index directory: {directory}")
            declared.add(directory)
            package_root = (base / directory).resolve()
            if base not in package_root.parents:
                _raise(error_type, f"{package_kind} index package directory must stay inside its root")
            contract = (package_root / str(entry.get("contract", contract_name))).resolve()
            if package_root not in contract.parents:
                _raise(error_type, f"{package_kind} index contract must stay inside its package directory")
            indexed.append((contract, entry))

        actual = {
            child.name
            for child in base.iterdir()
            if child.is_dir() and (child / contract_name).is_file()
        }
        if declared != actual:
            _raise(
                error_type,
                f"{package_kind} index/directory mismatch: "
                f"missing={sorted(actual - declared)}, stale={sorted(declared - actual)}",
            )
        return indexed

    if recursive_without_index:
        return [(path, {}) for path in sorted(base.rglob(contract_name))]
    return [
        (child / contract_name, {})
        for child in sorted(base.iterdir(), key=lambda item: item.name)
        if child.is_dir() and (child / contract_name).is_file()
    ]


def resolve_entrypoint(
    root: str | os.PathLike[str],
    entrypoint: Any,
    *,
    error_type: Type[Exception] = ValueError,
    label: str = "Pack",
) -> str | None:
    """Validate an entrypoint and return its normalized relative path."""

    if not entrypoint:
        return None
    base = Path(root).expanduser().resolve()
    candidate = (base / str(entrypoint)).resolve()
    if base not in candidate.parents or not candidate.is_file():
        _raise(error_type, f"{label} entrypoint must be a file inside its directory: {entrypoint}")
    return str(candidate.relative_to(base))


@dataclass(frozen=True)
class StdioExecution:
    """Raw result of running a local Pack entrypoint."""

    status: str
    value: Any = None
    detail: str = ""


MAX_STDIO_INPUT = 2 * 1024 * 1024
MAX_STDIO_OUTPUT = 4 * 1024 * 1024
MAX_STDIO_ERROR = 64 * 1024


def run_stdio(
    root: str | os.PathLike[str],
    entrypoint: str,
    payload: Mapping[str, Any],
    *,
    timeout: int,
    max_input_bytes: int = MAX_STDIO_INPUT,
    max_output_bytes: int = MAX_STDIO_OUTPUT,
    max_stderr_bytes: int = MAX_STDIO_ERROR,
    env_allowlist: tuple[str, ...] = ("PATH", "PYTHONPATH", "SYSTEMROOT", "WINDIR", "PYTHONPYCACHEPREFIX", "PYTHONDONTWRITEBYTECODE"),
    trusted: bool = True,
    allow_side_effects: bool = False,
) -> StdioExecution:
    """Run a Pack helper from its own directory and decode stdout JSON.

    Semantic adapters decide whether malformed output is an exception or an
    ``error``/``unchecked`` result; this function only reports the boundary
    outcome in a small, shared shape.
    """

    if not trusted:
        return StdioExecution("denied", detail="untrusted Pack execution is disabled")
    base = Path(root).expanduser().resolve()
    target = (base / entrypoint).resolve()
    if base not in target.parents or not target.is_file():
        return StdioExecution("error", detail=f"Pack entrypoint must be a file inside its directory: {entrypoint}")
    try:
        request = json.dumps(dict(payload), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        return StdioExecution("invalid_input", detail=f"invalid helper input: {type(exc).__name__}")
    if len(request.encode("utf-8")) > max_input_bytes:
        return StdioExecution("input_too_large", detail="Pack helper input exceeds configured limit")
    command = [sys.executable, str(target)] if target.suffix == ".py" else [str(target)]
    env = {key: os.environ[key] for key in env_allowlist if key in os.environ}
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    env["BENSZ_ALLOW_SIDE_EFFECTS"] = "1" if allow_side_effects else "0"
    try:
        with tempfile.TemporaryFile(mode="w+b") as stdout_file, tempfile.TemporaryFile(mode="w+b") as stderr_file:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout_file, stderr=stderr_file, text=True, cwd=base, env=env, start_new_session=(os.name != "nt"))
            try:
                process.communicate(request, timeout=timeout)
            except subprocess.TimeoutExpired:
                if os.name != "nt":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
                process.wait(timeout=1)
                return StdioExecution("timed_out", detail=f"Pack helper exceeded {timeout} seconds.")
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read(max_output_bytes + 1).decode("utf-8", errors="replace")
            stderr = stderr_file.read(max_stderr_bytes + 1).decode("utf-8", errors="replace")
            stdout_file.seek(0, 2)
            stderr_file.seek(0, 2)
            stdout_size, stderr_size = stdout_file.tell(), stderr_file.tell()
    except OSError as exc:
        return StdioExecution("error", detail=f"Pack helper could not start ({type(exc).__name__})")
    if process.returncode:
        return StdioExecution("error", detail=f"Pack helper exited with code {process.returncode}")
    if stdout_size > max_output_bytes:
        return StdioExecution("output_too_large", detail="Pack helper stdout exceeds configured limit")
    if stderr_size > max_stderr_bytes:
        return StdioExecution("error", detail="Pack helper stderr exceeds configured limit")
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return StdioExecution("invalid_json", detail=f"Pack helper must emit one JSON object: {exc.msg}")
    return StdioExecution("completed", value=value)
