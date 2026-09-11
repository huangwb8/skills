"""Integration checks for the verifier-state-architect hosting validator."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import yaml

from bensz_skill_kernel import __version__


CHECKER = (
    Path(__file__).parents[1]
    / "skills"
    / "alpha"
    / "verifier-state-architect"
    / "scripts"
    / "check_integration.py"
)
SPEC = importlib.util.spec_from_file_location("verifier_state_architect_check_integration", CHECKER)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def test_verifier_only_skill_with_explicit_root_passes_integration_check(tmp_path: Path) -> None:
    skill = tmp_path / "demo-skill"
    pack_root = skill / "references" / "verifiers"
    pack = pack_root / "demo-check"
    script = pack / "scripts" / "verify.py"
    script.parent.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Demo\n\n## 控制\n\nRun the declared Verifier.\n", encoding="utf-8")
    (skill / "config.yaml").write_text(
        "runtime:\n"
        "  kernel:\n"
        "    name: bensz-skill-kernel\n"
        f"    version: {__version__}\n"
        "  verifier_roots:\n"
        "    - references/verifiers\n"
        "  verifiers:\n"
        "    - id: test.demo.integration\n"
        "      version: 1.0.0\n"
        "      required: true\n",
        encoding="utf-8",
    )
    (pack / "VERIFIER.md").write_text(
        "# Demo integration Verifier\n\n"
        "## Verification target\nTarget.\n\n"
        "## Inputs and evidence\nInput.\n\n"
        "## Execution\nExecute.\n\n"
        "## Output and verdicts\nOutput.\n\n"
        "## Failure and boundaries\nBoundaries.\n",
        encoding="utf-8",
    )
    script.write_text(
        "import json, sys\njson.load(sys.stdin)\njson.dump({'verdict': 'pass'}, sys.stdout)\n",
        encoding="utf-8",
    )
    (pack_root / "index.json").write_text(
        json.dumps(
            {
                "protocol": "bensz-pack-index-v1",
                "package_kind": "verifier",
                "entries": [
                    {
                        "directory": "demo-check",
                        "id": "test.demo.integration",
                        "version": "1.0.0",
                        "classification": "domain",
                        "tags": ["demo"],
                        "aliases": [],
                        "contract": "VERIFIER.md",
                        "mode": "rule",
                        "assurance_tier": "deterministic",
                        "components": [
                            {
                                "id": "check",
                                "type": "script",
                                "entrypoint": "scripts/verify.py",
                                "required": True,
                                "assurance": "deterministic",
                                "side_effects": "none",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert checker.check(skill, yaml) == {
        "status": "pass",
        "execution": "unchecked",
        "scope": "hosting_and_loader_only",
        "verifiers": 1,
        "states": 0,
    }
