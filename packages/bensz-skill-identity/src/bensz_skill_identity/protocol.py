"""Bounded parsers and portable content inventory. No Skill code is executed."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import yaml
from yaml.tokens import AliasToken, AnchorToken, TagToken

SCHEMA = "bensz-skill-identity/v1"
MAX_METADATA = 4 * 1024 * 1024


class IdentityError(ValueError):
    def __init__(self, code: str, path: str = ""):
        self.code = code
        self.path = path
        super().__init__(code + (": " + path if path else ""))


def require(condition: bool, code: str = "invalid_metadata") -> None:
    if not condition:
        raise IdentityError(code)


def fields(value: object, keys: set[str]) -> dict:
    require(type(value) is dict and set(value) == keys)
    return value


def integer(value: object, minimum: int = 0) -> int:
    require(type(value) is int and minimum <= value <= 2**63 - 1)
    return value


def hex_value(value: object, length: int = 64) -> str:
    require(
        type(value) is str and re.fullmatch(f"[0-9a-f]{{{length}}}", value) is not None
    )
    return value


def _json_types(value: object, depth: int = 0) -> None:
    require(depth <= 32, "limit_exceeded")
    if type(value) in (str, int, bool) or value is None:
        if type(value) is int:
            require(-(2**63) <= value < 2**63)
        if type(value) is str:
            require(len(value) <= MAX_METADATA, "limit_exceeded")
        return
    require(type(value) in (list, dict))
    require(len(value) <= 20000, "limit_exceeded")
    if type(value) is dict:
        require(all(type(k) is str for k in value))
        value = list(value.values())
    for item in value:
        _json_types(item, depth + 1)


def canonical(value: object) -> bytes:
    _json_types(value)
    try:
        data = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (ValueError, UnicodeError) as exc:
        raise IdentityError("invalid_metadata") from exc
    require(len(data) <= MAX_METADATA, "limit_exceeded")
    return data


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_key")
        result[key] = value
    return result


def load_json(path: Path) -> object:
    data = read_file(path, MAX_METADATA)
    try:
        value = json.loads(data, object_pairs_hook=_pairs)
        _json_types(value)
        return value
    except (ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, IdentityError):
            raise
        raise IdentityError("invalid_json") from exc


def read_file(path: Path, limit: int) -> bytes:
    try:
        before = path.lstat()
        require(
            stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
            "unsupported_file_type",
        )
        require(before.st_size <= limit, "limit_exceeded")
        fd = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
        )
        with os.fdopen(fd, "rb") as stream:
            opened = os.fstat(stream.fileno())
            require(
                (opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino),
                "file_changed",
            )
            data = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
        require(len(data) <= limit, "limit_exceeded")
        require(
            (before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            == (after.st_size, after.st_mtime_ns, after.st_ctime_ns),
            "file_changed",
        )
        return data
    except OSError as exc:
        raise IdentityError("io_error") from exc


class UniqueLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        pairs = []
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            require(type(key) is str, "invalid_yaml")
            pairs.append((key, self.construct_object(value_node, deep=deep)))
        return _pairs(pairs)


def read_config(path: Path) -> dict:
    data = read_file(path, 1024 * 1024)
    try:
        # Aliases, anchors and explicit tags are outside this protocol's YAML subset.
        depth = 0
        for event in yaml.parse(data):
            if isinstance(event, (yaml.MappingStartEvent, yaml.SequenceStartEvent)):
                depth += 1
                require(depth <= 32, "limit_exceeded")
            elif isinstance(event, (yaml.MappingEndEvent, yaml.SequenceEndEvent)):
                depth -= 1
        require(
            not any(
                isinstance(t, (AliasToken, AnchorToken, TagToken))
                for t in yaml.scan(data)
            ),
            "invalid_yaml",
        )
        value = yaml.load(data, Loader=UniqueLoader)
        require(type(value) is dict, "invalid_yaml")
        return value
    except (yaml.YAMLError, UnicodeError, RecursionError) as exc:
        raise IdentityError("invalid_yaml") from exc


def version(value: object) -> str:
    require(
        type(value) is str
        and re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", value)
        is not None,
        "invalid_version",
    )
    require(len(value) <= 64, "invalid_version")
    return value


def skill_key(value: object) -> str:
    require(
        type(value) is str
        and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value) is not None
        and len(value) <= 128,
        "invalid_identity",
    )
    return value


def publisher_id(public_key: str) -> str:
    return "ed25519-" + hashlib.sha256(bytes.fromhex(hex_value(public_key))).hexdigest()


def skill_id(publisher: str, key: str) -> str:
    require(
        type(publisher) is str
        and re.fullmatch(r"ed25519-[0-9a-f]{64}", publisher) is not None,
        "invalid_identity",
    )
    return f"skill://{publisher}/{skill_key(key)}"


def validate_id(value: object) -> str:
    require(type(value) is str and value.startswith("skill://"), "invalid_identity")
    parts = value[8:].split("/")
    require(len(parts) == 2, "invalid_identity")
    require(skill_id(*parts) == value, "invalid_identity")
    return value


def read_identity(path: Path) -> dict | None:
    config = read_config(path)
    info = config.get("skill_info", {})
    require(type(info) is dict, "invalid_identity")
    if "identity" not in info:
        return None
    claim = fields(info["identity"], {"publisher_id", "skill_key"})
    return {
        "skill_id": skill_id(claim["publisher_id"], claim["skill_key"]),
        "version": version(info.get("version")),
    }


def safe_path(value: object) -> str:
    require(
        type(value) is str and 0 < len(value.encode("utf-8")) <= 1024, "unsafe_path"
    )
    require(unicodedata.normalize("NFC", value) == value, "unsafe_path")
    require(
        not any(c in value for c in "\\:\x00")
        and not any(ord(c) < 32 or ord(c) == 127 for c in value),
        "unsafe_path",
    )
    for part in value.split("/"):
        require(
            part not in ("", ".", "..") and not part.endswith((".", " ")), "unsafe_path"
        )
        require(
            part.split(".")[0].upper()
            not in {
                "CON",
                "PRN",
                "AUX",
                "NUL",
                *[f"COM{i}" for i in range(1, 10)],
                *[f"LPT{i}" for i in range(1, 10)],
            },
            "unsafe_path",
        )
        require(not any(c in part for c in '<>"|?*'), "unsafe_path")
    return value


@dataclass(frozen=True)
class Limits:
    files: int = 10000
    file_bytes: int = 64 * 1024 * 1024
    total_bytes: int = 256 * 1024 * 1024


def inventory(root: Path, limits: Limits = Limits()) -> list[dict]:
    require(root.is_dir() and not root.is_symlink(), "unsupported_file_type")
    entries, seen = [], set()
    total = 0

    def visit(directory: Path) -> None:
        nonlocal total
        for path in sorted(directory.iterdir(), key=lambda p: p.name.encode("utf-8")):
            rel = safe_path(path.relative_to(root).as_posix())
            folded = rel.casefold()
            require(folded not in seen, "path_collision")
            seen.add(folded)
            require(len(seen) <= limits.files, "limit_exceeded")
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode):
                entries.append({"path": rel, "type": "directory"})
                visit(path)
            elif stat.S_ISREG(mode):
                data = read_file(path, limits.file_bytes)
                total += len(data)
                require(total <= limits.total_bytes, "limit_exceeded")
                require(
                    not mode & (stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX),
                    "unsupported_file_type",
                )
                entries.append(
                    {
                        "path": rel,
                        "type": "file",
                        "size": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "executable": bool(mode & 0o111),
                    }
                )
            else:
                raise IdentityError("unsupported_file_type", rel)

    try:
        visit(root)
    except OSError as exc:
        raise IdentityError("io_error") from exc
    return sorted(entries, key=lambda e: e["path"].encode("utf-8"))
