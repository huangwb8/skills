"""Shared signing fixtures stay in memory; publisher tests clean disposable PEMs."""

import time
import sys
import os
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bensz_skill_identity import (
    TrustPolicy,
    authorize,
    build_release,
    public_hex,
    publisher_id,
    security_metadata,
)


@pytest.fixture
def sample(tmp_path):
    now = int(time.time())
    root = Ed25519PrivateKey.generate()
    key = Ed25519PrivateKey.generate()
    publisher = publisher_id(public_hex(root))
    content = tmp_path / "source"
    content.mkdir()
    (content / "config.yaml").write_text(
        f'skill_info:\n  name: display-name\n  version: "0.1.0"\n  identity:\n    publisher_id: {publisher}\n    skill_key: sample\n',
        encoding="utf-8",
    )
    for name in (
        "SKILL.md",
        "README.md",
        ".asset",
        "scripts/helper.py",
        "references/reference.md",
        "agents/reviewer/SKILL.md",
    ):
        path = content / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Public synthetic fixture: " + name + "\n", encoding="utf-8")
    auth = authorize(
        root, public_hex(key), ["sample"], not_before=now - 60, expires_at=now + 3600
    )
    security = security_metadata(
        root, revision=1, issued_at=now - 60, expires_at=now + 3600
    )
    policy = TrustPolicy(
        {publisher: public_hex(root)}, {publisher: security}, {publisher: 1}
    )
    release = tmp_path / "release"
    wanted = build_release(content, release, key, auth, history={}, now=now)
    return {
        "root": root,
        "key": key,
        "publisher": publisher,
        "content": content,
        "release": release,
        "policy": policy,
        "now": now,
        "auth": auth,
        "wanted": wanted,
    }


@pytest.fixture(autouse=True)
def source_subprocess_environment(monkeypatch):
    source = str(Path(__file__).resolve().parents[1] / "src")
    previous = os.environ.get("PYTHONPATH")
    monkeypatch.setenv(
        "PYTHONPATH", source + (os.pathsep + previous if previous else "")
    )
