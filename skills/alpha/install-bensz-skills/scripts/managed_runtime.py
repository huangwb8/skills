#!/usr/bin/env python3
"""Manage the Bensz-owned Conda runtime without shell activation.

This module intentionally uses only the Python 3.8 standard library so the
bootstrap installer can use it before the managed Python is available.
"""

from __future__ import print_function

import argparse
import contextlib
import json
import os
import shutil
import stat
import subprocess
import time
from pathlib import Path


CONFIG_NAME = "managed-runtime.json"
STATE_SCHEMA_VERSION = 1
LOCK_TIMEOUT_SECONDS = 30
STALE_LOCK_SECONDS = 30 * 60


class ManagedRuntimeError(RuntimeError):
    """A stable, user-actionable managed-runtime failure."""


def _config_path():
    return Path(__file__).resolve().with_name(CONFIG_NAME)


def load_config(path=None):
    source = Path(path) if path is not None else _config_path()
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ManagedRuntimeError("cannot load managed runtime configuration") from exc
    if data.get("schema_version") != 1:
        raise ManagedRuntimeError("unsupported managed runtime configuration schema")
    environment = data.get("environment")
    packages = data.get("packages")
    if not isinstance(environment, dict) or not isinstance(packages, list) or not packages:
        raise ManagedRuntimeError("managed runtime configuration is incomplete")
    return data


def runtime_prefix(config, home=None):
    root = Path(home) if home is not None else Path.home()
    configured = config["environment"].get("prefix", ".bensz-skills/envs/benszapi")
    path = Path(str(configured))
    if path.is_absolute():
        raise ManagedRuntimeError("managed runtime prefix must be relative to the user home")
    resolved = (root / path).resolve()
    home_resolved = root.resolve()
    try:
        resolved.relative_to(home_resolved)
    except ValueError as exc:
        raise ManagedRuntimeError("managed runtime prefix escapes the user home") from exc
    return resolved


def runtime_python(prefix):
    if os.name == "nt":
        return prefix / "python.exe"
    return prefix / "bin" / "python"


def runtime_command(prefix, command):
    if os.name == "nt":
        scripts = prefix / "Scripts"
        for suffix in (".exe", ".cmd", ".bat", ""):
            candidate = scripts / (command + suffix)
            if candidate.exists():
                return candidate
        return scripts / (command + ".exe")
    return prefix / "bin" / command


def state_path(home=None):
    root = Path(home) if home is not None else Path.home()
    return root / ".bensz-skills" / "installation" / "state" / "managed-runtime.json"


def _read_state(home=None):
    try:
        value = json.loads(state_path(home).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _write_state(payload, home=None):
    path = state_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(".%s.%s.tmp" % (path.name, os.getpid()))
    data = dict(payload)
    data["schema_version"] = STATE_SCHEMA_VERSION
    try:
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(str(temporary), str(path))
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


@contextlib.contextmanager
def _runtime_lock(home=None):
    path = state_path(home).with_name("managed-runtime.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    token = "%s:%s" % (os.getpid(), time.time_ns())
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    acquired = False
    while time.monotonic() < deadline:
        try:
            descriptor = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(token)
            acquired = True
            break
        except FileExistsError:
            try:
                if time.time() - path.stat().st_mtime > STALE_LOCK_SECONDS:
                    path.unlink()
                    continue
            except FileNotFoundError:
                continue
            time.sleep(0.1)
    if not acquired:
        raise ManagedRuntimeError("managed runtime is being updated by another process")
    try:
        yield
    finally:
        try:
            if path.read_text(encoding="utf-8") == token:
                path.unlink()
        except FileNotFoundError:
            pass


def _path_label(path, home=None):
    root = (Path(home) if home is not None else Path.home()).resolve()
    try:
        return "~/" + str(Path(path).resolve().relative_to(root))
    except ValueError:
        return "<external>"


def find_conda():
    explicit = os.environ.get("BENSZ_CONDA_EXE") or os.environ.get("CONDA_EXE")
    if explicit:
        candidate = Path(explicit).expanduser()
        if candidate.is_file():
            return str(candidate)
    for name in ("conda", "mamba", "micromamba"):
        candidate = shutil.which(name)
        if candidate:
            return candidate
    raise ManagedRuntimeError(
        "Conda, Mamba, or Micromamba was not found; install one or set BENSZ_CONDA_EXE"
    )


def _run(command, timeout=300):
    try:
        return subprocess.run(
            [str(part) for part in command],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ManagedRuntimeError("managed runtime command could not be executed") from exc


def _checked_run(command, label, timeout=300):
    result = _run(command, timeout=timeout)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        suffix = (": " + _redact_detail(detail[-1])[:300]) if detail else ""
        raise ManagedRuntimeError(label + " failed" + suffix)
    return result


def _redact_detail(value):
    return str(value).replace(str(Path.home()), "~")


def _package_versions(python, packages):
    names = [str(item["distribution"]) for item in packages]
    script = (
        "import importlib.metadata as m,json; "
        "print(json.dumps({n:m.version(n) for n in %r},sort_keys=True))" % names
    )
    result = _checked_run([python, "-c", script], "managed package version check", timeout=30)
    try:
        value = json.loads(result.stdout)
    except ValueError as exc:
        raise ManagedRuntimeError("managed package version check returned invalid JSON") from exc
    return value


def _health_check(prefix, config):
    python = runtime_python(prefix)
    if not python.is_file():
        raise ManagedRuntimeError("managed Conda environment has no Python interpreter")
    versions = _package_versions(python, config["packages"])
    for package in config["packages"]:
        executable = runtime_command(prefix, str(package["command"]))
        if not executable.exists():
            raise ManagedRuntimeError("managed command is missing: " + str(package["command"]))
        for arguments in package.get("health_checks", []):
            _checked_run([executable] + list(arguments), "health check for " + str(package["id"]), timeout=60)
    return versions


def _needs_update(config, home=None, force=False):
    if force:
        return True
    state = _read_state(home)
    if state.get("schema_version") != STATE_SCHEMA_VERSION:
        return True
    completed = state.get("last_check_completed_at")
    ttl = int(config.get("update_ttl_hours", 72)) * 60 * 60
    return not isinstance(completed, (int, float)) or time.time() - completed >= ttl


def _has_package_drift(packages, home=None):
    recorded = _read_state(home).get("packages")
    return not isinstance(recorded, dict) or recorded != packages


def _write_posix_launcher(path, target):
    content = "#!/bin/sh\nexec %s \"$@\"\n" % _shell_quote(str(target))
    temporary = path.with_name(".%s.%s.tmp" % (path.name, os.getpid()))
    temporary.write_text(content, encoding="utf-8")
    temporary.chmod(temporary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    os.replace(str(temporary), str(path))


def _shell_quote(value):
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _install_launchers(prefix, config, home=None):
    root = Path(home) if home is not None else Path.home()
    bin_dir = root / ".bensz-skills" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    installed = {}
    for package in config["packages"]:
        command = str(package["command"])
        target = runtime_command(prefix, command)
        if os.name == "nt":
            launcher = bin_dir / (command + ".cmd")
            launcher.write_text('@echo off\r\n"%s" %%*\r\n' % target, encoding="utf-8")
        else:
            launcher = bin_dir / command
            _write_posix_launcher(launcher, target)
        installed[command] = _path_label(launcher, home)
    return installed


def status(config=None, home=None):
    config = config or load_config()
    prefix = runtime_prefix(config, home)
    result = {
        "schema_version": STATE_SCHEMA_VERSION,
        "environment": str(config["environment"].get("name", "benszapi")),
        "prefix": _path_label(prefix, home),
        "ready": False,
        "packages": {},
    }
    try:
        result["packages"] = _health_check(prefix, config)
        result["ready"] = True
    except ManagedRuntimeError as exc:
        result["reason"] = str(exc)
    return result


def _ensure_unlocked(config, home=None, force_update=False):
    prefix = runtime_prefix(config, home)
    python = runtime_python(prefix)
    created = False
    updated = False

    if not python.is_file():
        if prefix.exists() and (not prefix.is_dir() or any(prefix.iterdir())):
            raise ManagedRuntimeError(
                "managed runtime prefix exists but is not a valid Conda environment: "
                + _path_label(prefix, home)
            )
        conda = find_conda()
        create_command = [
            conda,
            "create",
            "--yes",
            "--prefix",
            str(prefix),
            "python=" + str(config["environment"].get("python", "3.12")),
            "pip",
        ]
        prefix.parent.mkdir(parents=True, exist_ok=True)
        _checked_run(create_command, "managed Conda environment creation", timeout=900)
        if not python.is_file():
            raise ManagedRuntimeError("Conda reported success but the managed Python is missing")
        created = True

    current = status(config, home)
    healthy = current.get("ready", False)
    drifted = healthy and _has_package_drift(current.get("packages", {}), home)
    if created or not healthy or drifted or _needs_update(config, home, force_update):
        specs = [str(item["distribution"]) for item in config["packages"]]
        _checked_run(
            [python, "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--upgrade"] + specs,
            "managed package update",
            timeout=900,
        )
        updated = True

    versions = _health_check(prefix, config)
    launchers = _install_launchers(prefix, config, home)
    now = int(time.time())
    payload = {
        "last_check_completed_at": now,
        "last_check_completed_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "last_result": "success",
        "environment": str(config["environment"].get("name", "benszapi")),
        "prefix": _path_label(prefix, home),
        "packages": versions,
        "launchers": launchers,
    }
    _write_state(payload, home)
    return dict(payload, ready=True, created=created, updated=updated)


def ensure(config=None, home=None, force_update=False, dry_run=False):
    config = config or load_config()
    prefix = runtime_prefix(config, home)
    current = status(config, home)
    if dry_run:
        return {
            "ready": current.get("ready", False),
            "dry_run": True,
            "would_create": None if runtime_python(prefix).is_file() else _path_label(prefix, home),
            "would_update": (
                force_update
                or not current.get("ready", False)
                or _has_package_drift(current.get("packages", {}), home)
                or _needs_update(config, home)
            ),
            "would_install": [item["distribution"] for item in config["packages"]],
        }
    with _runtime_lock(home):
        return _ensure_unlocked(config, home, force_update)


def build_parser():
    parser = argparse.ArgumentParser(description="Manage the Bensz-owned Conda runtime")
    commands = parser.add_subparsers(dest="command", required=True)
    ensure_parser = commands.add_parser("ensure", help="create, update, and validate the runtime")
    ensure_parser.add_argument("--force-update", action="store_true")
    ensure_parser.add_argument("--dry-run", action="store_true")
    commands.add_parser("status", help="inspect the runtime without modifying it")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        result = ensure(force_update=args.force_update, dry_run=args.dry_run) if args.command == "ensure" else status()
    except ManagedRuntimeError as exc:
        print(json.dumps({"ready": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ready") or result.get("dry_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
