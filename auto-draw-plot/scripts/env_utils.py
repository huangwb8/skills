from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Optional


DEFAULT_REMOTE_ENV = Path.home() / ".bensz-skills" / "config" / "remote.env"
_LINE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


def find_remote_env(preferred: Optional[Path] = None) -> Optional[Path]:
    if preferred is not None and preferred.exists() and preferred.is_file():
        return preferred
    if DEFAULT_REMOTE_ENV.exists() and DEFAULT_REMOTE_ENV.is_file():
        return DEFAULT_REMOTE_ENV
    return None


def _strip_inline_comment(value: str) -> str:
    val = value.strip()
    if not val:
        return ""
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return val[1:-1]
    if "#" in val:
        return val.split("#", 1)[0].rstrip()
    return val


def parse_dotenv(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            raw_line = line[len("export ") :]
        m = _LINE_RE.match(raw_line)
        if not m:
            continue
        out[m.group(1)] = _strip_inline_comment(m.group(2))
    return out


def load_dotenv(path: Path) -> Dict[str, str]:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = path.read_text(encoding="utf-8", errors="replace")
    return parse_dotenv(raw)


def merged_env(dotenv_path: Optional[Path]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if dotenv_path is not None and dotenv_path.exists():
        out.update(load_dotenv(dotenv_path))
    out.update({k: v for k, v in os.environ.items() if isinstance(v, str)})
    return out


def mask_secret(secret: str, *, keep: int = 4) -> str:
    text = str(secret or "")
    if not text:
        return ""
    if len(text) <= keep:
        return "*" * len(text)
    return "*" * max(8, len(text) - keep) + text[-keep:]
