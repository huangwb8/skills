from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "缺少 PyYAML 依赖，无法读取 config.yaml。请先执行 `python3 -m pip install pyyaml`。"
    ) from exc


SENSITIVE_TEXT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "secret",
        re.compile(
            r"(?i)\b(?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|client[_ -]?secret|"
            r"authorization|password|passwd|pwd|secret)\b\s*[:=]\s*(?:bearer\s+)?[^\s,;]+"
        ),
    ),
    ("secret", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]{8,}\b")),
    (
        "private-key",
        re.compile(
            r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----"
        ),
    ),
    (
        "token",
        re.compile(
            r"\b(?:sk-[A-Za-z0-9-]{16,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
            r"xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z\-_]{20,})\b"
        ),
    ),
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    ("identity", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("identity", re.compile(r"\b\d{17}[\dXx]\b")),
)

PRIVATE_PATH_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-path", re.compile(r"(?<!\w)(?:/Users|/home)/[^/\s]+(?:/[^\s]*)*")),
    ("private-path", re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+(?:\\[^\s]*)*")),
)

PHONE_CANDIDATE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d().\-\s]{8,}\d)")
CARD_CANDIDATE_PATTERN = re.compile(r"(?<!\w)(?:\d[ -]?){13,19}(?!\w)")


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_config() -> dict[str, Any]:
    config_path = skill_root() / "config.yaml"
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"配置文件格式错误：{config_path}")
    return data


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def expand_path(path_text: str) -> Path:
    return Path(path_text).expanduser()


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"JSON 结构错误：{path}")
    return data


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().split())


def normalize_list(values: list[str]) -> list[str]:
    normalized = [normalize_text(item) for item in values if normalize_text(item)]
    return normalized


def privacy_settings(config: dict[str, Any]) -> dict[str, Any]:
    settings = config.get("privacy", {})
    return settings if isinstance(settings, dict) else {}


def reporting_settings(config: dict[str, Any]) -> dict[str, Any]:
    settings = config.get("reporting", {})
    return settings if isinstance(settings, dict) else {}


def redaction_token(config: dict[str, Any], kind: str) -> str:
    template = privacy_settings(config).get("redaction_placeholder", "[redacted:{kind}]")
    return str(template).format(kind=kind)


def luhn_checksum_valid(number: str) -> bool:
    digits = [int(ch) for ch in number]
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def redact_phone_candidates(text: str, config: dict[str, Any]) -> str:
    def replacer(match: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        if 10 <= len(digits) <= 15:
            return redaction_token(config, "phone")
        return match.group(0)

    return PHONE_CANDIDATE_PATTERN.sub(replacer, text)


def redact_card_candidates(text: str, config: dict[str, Any]) -> str:
    def replacer(match: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 19 and luhn_checksum_valid(digits):
            return redaction_token(config, "credit-card")
        return match.group(0)

    return CARD_CANDIDATE_PATTERN.sub(replacer, text)


def sanitize_user_text(value: str | None, config: dict[str, Any]) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    if not privacy_settings(config).get("auto_redact_sensitive_text", True):
        return text

    for kind, pattern in SENSITIVE_TEXT_PATTERNS + PRIVATE_PATH_PATTERNS:
        text = pattern.sub(redaction_token(config, kind), text)
    text = redact_phone_candidates(text, config)
    text = redact_card_candidates(text, config)
    return text


def sanitize_user_list(values: list[str], config: dict[str, Any]) -> list[str]:
    sanitized = [sanitize_user_text(item, config) for item in values]
    return [item for item in sanitized if item]


def merge_unique(existing: list[str], incoming: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for item in normalize_list(existing) + normalize_list(incoming):
        if item in seen:
            continue
        merged.append(item)
        seen.add(item)
    return merged


def slugify(value: str, fallback: str = "unknown") -> str:
    text = normalize_text(value).lower()
    text = re.sub(r"[^a-z0-9._-]+", "-", text)
    text = text.strip("-._")
    return text or fallback


def command_exists(program: str) -> bool:
    return shutil.which(program) is not None


def run_command(command: list[str], timeout: int = 8) -> str | None:
    if not command:
        return None
    if not command_exists(command[0]):
        return None
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = (result.stdout or result.stderr or "").strip()
    if not output:
        return None
    return output.splitlines()[0].strip()


def current_local_username() -> str | None:
    try:
        return getpass.getuser()
    except Exception:  # pragma: no cover
        return None


def current_github_username(explicit: str | None = None) -> str | None:
    if explicit:
        return normalize_text(explicit)
    output = run_command(["gh", "api", "user", "-q", ".login"])
    return normalize_text(output) or None


def gh_auth_ok() -> bool:
    if not command_exists("gh"):
        return False
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def parse_software_pairs(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in values:
        if "=" not in item:
            raise SystemExit(f"`--software` 参数格式错误，应为 key=value：{item}")
        key, value = item.split("=", 1)
        key = slugify(key, fallback="")
        if not key:
            raise SystemExit(f"`--software` 参数键为空：{item}")
        parsed[key] = normalize_text(value)
    return parsed


def detect_os_details() -> dict[str, Any]:
    uname = platform.uname()
    details: dict[str, Any] = {
        "family": uname.system or platform.system(),
        "release": uname.release or platform.release(),
        "version": uname.version or platform.version(),
        "machine": uname.machine or platform.machine(),
        "processor": uname.processor or platform.processor(),
    }

    if details["family"] == "Darwin":
        sw_vers = {
            "product_name": run_command(["sw_vers", "-productName"]),
            "product_version": run_command(["sw_vers", "-productVersion"]),
            "build_version": run_command(["sw_vers", "-buildVersion"]),
        }
        details["macos"] = sw_vers
    elif details["family"] == "Linux":
        os_release = Path("/etc/os-release")
        if os_release.exists():
            parsed: dict[str, str] = {}
            for line in os_release.read_text(encoding="utf-8").splitlines():
                if "=" not in line or line.startswith("#"):
                    continue
                key, value = line.split("=", 1)
                parsed[key] = value.strip().strip('"')
            details["linux_distribution"] = parsed

    return details


def detect_runtime(config: dict[str, Any], agent_runtime: str | None) -> dict[str, Any]:
    privacy = privacy_settings(config)
    return {
        "agent_runtime": sanitize_user_text(agent_runtime, config) or "unknown",
        "shell": os.environ.get("SHELL") or None,
        "cwd": str(Path.cwd()) if privacy.get("collect_working_directory", False) else None,
        "hostname": platform.node() or None if privacy.get("collect_hostnames", False) else None,
        "local_username": (
            current_local_username() if privacy.get("collect_local_username", False) else None
        ),
        "python_runtime": platform.python_version(),
    }


def detect_device(config: dict[str, Any], device_type: str | None) -> dict[str, Any]:
    privacy = privacy_settings(config)
    return {
        "type": sanitize_user_text(device_type, config) or "unknown",
        "architecture": platform.machine() or None,
        "hostname": platform.node() or None if privacy.get("collect_hostnames", False) else None,
    }


def detect_software_versions(config: dict[str, Any], extra_versions: dict[str, str]) -> dict[str, Any]:
    detected: dict[str, Any] = {}
    commands = config.get("environment", {}).get("version_commands", [])
    for entry in commands:
        key = entry.get("key")
        command = entry.get("command")
        if not key or not isinstance(command, list):
            continue
        detected[key] = sanitize_user_text(run_command([str(item) for item in command]), config) or None
    for key, value in extra_versions.items():
        detected[key] = sanitize_user_text(value, config) or None
    return detected


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def get_nested_value(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def set_nested_value(payload: dict[str, Any], path: str, value: Any) -> None:
    current = payload
    parts = path.split(".")
    for part in parts[:-1]:
        nested = current.get(part)
        if not isinstance(nested, dict):
            nested = {}
            current[part] = nested
        current = nested
    current[parts[-1]] = json.loads(json.dumps(value, ensure_ascii=False))


def compute_bug_hash(payload: dict[str, Any], algorithm: str) -> str:
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as exc:  # pragma: no cover
        raise SystemExit(f"不支持的哈希算法：{algorithm}") from exc
    hasher.update(canonical_json(payload).encode("utf-8"))
    return hasher.hexdigest()


def deduplication_payload(
    config: dict[str, Any],
    skill_name: str,
    skill_author: str,
    summary: str,
    expected_behavior: str,
    actual_behavior: str,
    environment: dict[str, Any],
) -> dict[str, Any]:
    software_versions = environment.get("software_versions", {})
    canonical_payload = {
        "skill": {
            "name": normalize_text(skill_name),
            "author": normalize_text(skill_author),
        },
        "bug": {
            "summary": normalize_text(summary),
            "expected_behavior": normalize_text(expected_behavior),
            "actual_behavior": normalize_text(actual_behavior),
        },
        "environment": {
            "os": environment.get("os", {}),
            "runtime": {
                "agent_runtime": environment.get("runtime", {}).get("agent_runtime"),
            },
            "software_versions": software_versions,
        },
    }
    stable_fields = config.get("hashing", {}).get("stable_fields", [])
    normalized_fields = [normalize_text(str(field)) for field in stable_fields if normalize_text(str(field))]
    if not normalized_fields:
        return canonical_payload

    selected_payload: dict[str, Any] = {}
    for field in normalized_fields:
        value = get_nested_value(canonical_payload, field)
        if value is None:
            continue
        set_nested_value(selected_payload, field, value)
    return selected_payload or canonical_payload


def skill_storage_root(config: dict[str, Any], override: str | None = None) -> Path:
    root_text = override or config["storage"]["local_root"]
    return expand_path(root_text)


def reporter_folder_name(config: dict[str, Any], github_username: str | None) -> str:
    fallback = config.get("defaults", {}).get("reporter_fallback", "unknown-reporter")
    return slugify(github_username or fallback, fallback=fallback)


def build_bug_directory(
    config: dict[str, Any],
    root: Path,
    skill_name: str,
    reporter_folder: str,
    bug_hash: str,
) -> Path:
    path_pattern = config.get("storage", {}).get("path_pattern") or "{skill_name}/{reporter}/{bug_hash}"
    try:
        relative_path = path_pattern.format(
            skill_name=slugify(skill_name),
            reporter=slugify(reporter_folder),
            bug_hash=normalize_text(bug_hash),
        )
    except KeyError as exc:
        raise SystemExit(f"storage.path_pattern 包含不支持的占位符：{exc}") from exc

    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit(f"storage.path_pattern 解析后越界：{relative_path}")
    return root / path


def format_list_block(values: list[str], empty_text: str = "- None") -> str:
    normalized = normalize_list(values)
    if not normalized:
        return empty_text
    return "\n".join(f"- {item}" for item in normalized)


def format_software_block(versions: dict[str, Any]) -> str:
    lines = []
    for key in sorted(versions):
        value = versions[key]
        lines.append(f"  - {key}: {value or 'unavailable'}")
    return "\n".join(lines) if lines else "  - unavailable"


def os_summary(environment: dict[str, Any]) -> str:
    os_info = environment.get("os", {})
    family = os_info.get("family") or "unknown"
    release = os_info.get("release") or ""
    machine = os_info.get("machine") or ""
    parts = [part for part in [family, release, machine] if part]
    return " / ".join(parts) if parts else "unknown"


def sanitized_local_context(context: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    sanitized = json.loads(json.dumps(context))
    privacy = privacy_settings(config)

    skill = sanitized.setdefault("skill", {})
    for key in ("name", "author", "source_path", "source_repo"):
        if isinstance(skill.get(key), str):
            skill[key] = sanitize_user_text(skill[key], config)

    reporter = sanitized.setdefault("reporter", {})
    github_username = reporter.get("github_username")
    reporter["display_name"] = github_username or config.get("defaults", {}).get(
        "anonymous_reporter", "anonymous-reporter"
    )
    if not privacy.get("collect_local_username", False):
        reporter["local_username"] = None

    bug = sanitized.setdefault("bug", {})
    for key in (
        "summary",
        "severity",
        "expected_behavior",
        "actual_behavior",
        "workaround",
        "impact",
        "additional_notes",
    ):
        if isinstance(bug.get(key), str):
            bug[key] = sanitize_user_text(bug[key], config)
    bug["reproduction_steps"] = sanitize_user_list(bug.get("reproduction_steps", []), config)
    bug["evidence"] = sanitize_user_list(bug.get("evidence", []), config)

    environment = sanitized.setdefault("environment", {})
    device = environment.setdefault("device", {})
    runtime = environment.setdefault("runtime", {})
    software_versions = environment.setdefault("software_versions", {})

    if isinstance(device.get("type"), str):
        device["type"] = sanitize_user_text(device["type"], config) or "unknown"
    if not privacy.get("collect_hostnames", False):
        device["hostname"] = None
    elif isinstance(device.get("hostname"), str):
        device["hostname"] = sanitize_user_text(device["hostname"], config)

    if isinstance(runtime.get("agent_runtime"), str):
        runtime["agent_runtime"] = sanitize_user_text(runtime["agent_runtime"], config) or "unknown"
    if isinstance(runtime.get("shell"), str):
        runtime["shell"] = sanitize_user_text(runtime["shell"], config)
    if not privacy.get("collect_working_directory", False):
        runtime["cwd"] = None
    elif isinstance(runtime.get("cwd"), str):
        runtime["cwd"] = sanitize_user_text(runtime["cwd"], config)
    if not privacy.get("collect_hostnames", False):
        runtime["hostname"] = None
    elif isinstance(runtime.get("hostname"), str):
        runtime["hostname"] = sanitize_user_text(runtime["hostname"], config)
    if not privacy.get("collect_local_username", False):
        runtime["local_username"] = None
    elif isinstance(runtime.get("local_username"), str):
        runtime["local_username"] = sanitize_user_text(runtime["local_username"], config)

    for key, value in list(software_versions.items()):
        if isinstance(value, str):
            software_versions[key] = sanitize_user_text(value, config)

    tracking = sanitized.setdefault("tracking", {})
    if not privacy.get("store_local_path", False):
        tracking["local_path"] = None
    elif isinstance(tracking.get("local_path"), str):
        tracking["local_path"] = sanitize_user_text(tracking["local_path"], config)

    deduplication = sanitized.get("deduplication", {})
    fingerprint_payload = deduplication.get("fingerprint_payload")
    if isinstance(fingerprint_payload, dict):
        fingerprint_skill = fingerprint_payload.get("skill", {})
        fingerprint_bug = fingerprint_payload.get("bug", {})
        fingerprint_environment = fingerprint_payload.get("environment", {})
        for key in ("name", "author"):
            if isinstance(fingerprint_skill.get(key), str):
                fingerprint_skill[key] = sanitize_user_text(fingerprint_skill[key], config)
        for key in ("summary", "expected_behavior", "actual_behavior"):
            if isinstance(fingerprint_bug.get(key), str):
                fingerprint_bug[key] = sanitize_user_text(fingerprint_bug[key], config)
        if isinstance(fingerprint_environment.get("agent_runtime"), str):
            fingerprint_environment["agent_runtime"] = sanitize_user_text(
                fingerprint_environment["agent_runtime"],
                config,
            )
        nested_runtime = fingerprint_environment.get("runtime", {})
        if isinstance(nested_runtime, dict) and isinstance(nested_runtime.get("agent_runtime"), str):
            nested_runtime["agent_runtime"] = sanitize_user_text(
                nested_runtime["agent_runtime"],
                config,
            )
        software = fingerprint_environment.get("software_versions", {})
        if isinstance(software, dict):
            for key, value in list(software.items()):
                if isinstance(value, str):
                    software[key] = sanitize_user_text(value, config)

    return sanitized


def bug_report_markdown(template_text: str, context: dict[str, Any], config: dict[str, Any]) -> str:
    bug = context["bug"]
    environment = context["environment"]
    tracking = context["tracking"]
    reporter = context["reporter"]
    replacements = {
        "skill_name": context["skill"]["name"],
        "skill_author": context["skill"]["author"],
        "reporter_github": reporter.get("github_username") or "unknown",
        "bug_hash": context["bug_hash"],
        "severity": bug.get("severity") or "important",
        "occurrence_count": tracking.get("occurrence_count") or 1,
        "first_seen_at": tracking.get("first_seen_at") or tracking.get("collected_at") or "unknown",
        "last_seen_at": tracking.get("last_seen_at") or tracking.get("collected_at") or "unknown",
        "privacy_notice": reporting_settings(config).get(
            "privacy_notice",
            "Sensitive user data is auto-redacted before storage and public reporting.",
        ),
        "summary": bug.get("summary") or "",
        "expected_behavior": bug.get("expected_behavior") or "",
        "actual_behavior": bug.get("actual_behavior") or "",
        "reproduction_steps_block": format_list_block(bug.get("reproduction_steps", [])),
        "evidence_block": format_list_block(bug.get("evidence", [])),
        "skill_source_path": context["skill"].get("source_path") or "None",
        "skill_source_repo": context["skill"].get("source_repo") or "None",
        "device_type": environment.get("device", {}).get("type") or "unknown",
        "os_summary": os_summary(environment),
        "shell": environment.get("runtime", {}).get("shell") or "unknown",
        "agent_runtime": environment.get("runtime", {}).get("agent_runtime") or "unknown",
        "software_versions_block": format_software_block(environment.get("software_versions", {})),
        "impact": bug.get("impact") or "该问题会削弱 skill 在真实环境中的稳定性与可预期性，属于需要跟踪修复的设计缺陷。",
        "workaround": bug.get("workaround") or "None",
        "additional_notes": bug.get("additional_notes") or "None",
    }
    return template_text.format(**replacements)


def add_common_collection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--skill-name", required=True)
    parser.add_argument("--skill-author", required=True)
    parser.add_argument("--bug-summary", required=True)
    parser.add_argument("--expected-behavior", required=True)
    parser.add_argument("--actual-behavior", required=True)
    parser.add_argument("--reproduction-step", action="append", default=[])
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--workaround")
    parser.add_argument("--severity")
    parser.add_argument("--device-type")
    parser.add_argument("--agent-runtime")
    parser.add_argument("--skill-source-path")
    parser.add_argument("--skill-source-repo")
    parser.add_argument("--reporter-display-name", help="已弃用；为保护隐私，此参数当前会被忽略")
    parser.add_argument("--reporter-github")
    parser.add_argument("--additional-note")
    parser.add_argument("--software", action="append", default=[])
    parser.add_argument("--bug-root")
    parser.add_argument("--print-json", action="store_true")


def find_context_files(root: Path, filename: str) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob(filename))


def validate_storage_root(path: Path) -> Path:
    if path.exists() and not path.is_dir():
        raise SystemExit(f"bug 根目录不是文件夹：{path}")
    if path.is_symlink():
        raise SystemExit(f"拒绝使用符号链接作为 bug 根目录：{path}")
    return path.resolve()


def sanitized_public_context(
    context: dict[str, Any],
    config: dict[str, Any],
    placeholder: str = "redacted",
) -> dict[str, Any]:
    sanitized = sanitized_local_context(context, config)
    sanitized["reporter"]["display_name"] = sanitized["reporter"].get("github_username") or placeholder
    sanitized["reporter"]["local_username"] = placeholder

    skill_block = sanitized.get("skill", {})
    if skill_block.get("source_path"):
        skill_block["source_path"] = placeholder

    environment = sanitized.get("environment", {})
    device = environment.get("device", {})
    runtime = environment.get("runtime", {})
    device["hostname"] = placeholder if device.get("hostname") else None
    runtime["hostname"] = placeholder if runtime.get("hostname") else None
    runtime["cwd"] = placeholder if runtime.get("cwd") else None
    runtime["local_username"] = placeholder if runtime.get("local_username") else None

    tracking = sanitized.get("tracking", {})
    if tracking.get("local_path"):
        tracking["local_path"] = placeholder
    return sanitized
