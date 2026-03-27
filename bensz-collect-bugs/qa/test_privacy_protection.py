from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import common  # noqa: E402


class PrivacyProtectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = common.load_config()

    def test_sanitize_user_text_redacts_common_sensitive_values(self) -> None:
        text = (
            "Authorization: Bearer sk-1234567890abcdefghijklmn "
            "email alice@example.com "
            "phone +1 415-555-1234 "
            "card 4111 1111 1111 1111 "
            "id 123-45-6789 "
            "path /Users/alice/private/project"
        )

        sanitized = common.sanitize_user_text(text, self.config)

        for forbidden in (
            "sk-1234567890abcdefghijklmn",
            "alice@example.com",
            "+1 415-555-1234",
            "4111 1111 1111 1111",
            "123-45-6789",
            "/Users/alice/private/project",
        ):
            self.assertNotIn(forbidden, sanitized)

        for marker in (
            "[redacted:secret]",
            "[redacted:email]",
            "[redacted:phone]",
            "[redacted:credit-card]",
            "[redacted:identity]",
            "[redacted:private-path]",
        ):
            self.assertIn(marker, sanitized)

    def test_sanitized_public_context_redacts_legacy_private_fields(self) -> None:
        context = {
            "bug_hash": "hash",
            "skill": {
                "name": "bensz-collect-bugs",
                "author": "Bensz Conan",
                "source_path": "/Users/alice/dev/skill",
                "source_repo": "https://github.com/example/repo",
            },
            "reporter": {
                "display_name": "Alice",
                "github_username": "octocat",
                "local_username": "alice",
            },
            "bug": {
                "summary": "password=super-secret",
                "severity": "important",
                "expected_behavior": "do x",
                "actual_behavior": "call me at +1 415-555-1234",
                "reproduction_steps": ["open /Users/alice/dev/skill"],
                "evidence": ["email alice@example.com"],
                "workaround": None,
                "impact": "important",
                "additional_notes": None,
                "is_skill_design_defect": True,
            },
            "environment": {
                "device": {"type": "laptop", "hostname": "alice-mbp"},
                "runtime": {
                    "agent_runtime": "codex-cli",
                    "shell": "/bin/zsh",
                    "cwd": "/Users/alice/dev/skill",
                    "hostname": "alice-mbp",
                    "local_username": "alice",
                },
                "software_versions": {"custom": "token=ghp_1234567890abcdefghijklmnop"},
                "os": {"family": "Darwin", "release": "24.0.0", "machine": "arm64"},
            },
            "tracking": {
                "collected_at": "2026-03-27T00:00:00Z",
                "first_seen_at": "2026-03-27T00:00:00Z",
                "last_seen_at": "2026-03-27T00:00:00Z",
                "occurrence_count": 1,
                "public_reported": False,
                "public_repo": None,
                "public_path": None,
                "reported_at": None,
                "local_path": "/Users/alice/.bensz-skills/bugs/x",
            },
            "deduplication": {
                "fingerprint_payload": {
                    "skill": {"name": "bensz-collect-bugs", "author": "Bensz Conan"},
                    "bug": {
                        "summary": "password=super-secret",
                        "expected_behavior": "do x",
                        "actual_behavior": "phone +1 415-555-1234",
                    },
                    "environment": {
                        "agent_runtime": "codex-cli",
                        "software_versions": {"custom": "alice@example.com"},
                    },
                }
            },
        }

        public_context = common.sanitized_public_context(context, self.config, placeholder="redacted")
        rendered = json.dumps(public_context, ensure_ascii=False)

        for forbidden in (
            "alice@example.com",
            "+1 415-555-1234",
            "super-secret",
            "/Users/alice",
            "alice-mbp",
        ):
            self.assertNotIn(forbidden, rendered)

        self.assertEqual(public_context["reporter"]["display_name"], "octocat")
        self.assertEqual(public_context["reporter"]["local_username"], "redacted")
        self.assertEqual(public_context["skill"]["source_path"], "redacted")

    def test_deduplication_payload_respects_stable_fields_config(self) -> None:
        config = deepcopy(self.config)
        config["hashing"]["stable_fields"] = [
            "skill.name",
            "environment.runtime.agent_runtime",
        ]
        payload = common.deduplication_payload(
            config=config,
            skill_name="demo-skill",
            skill_author="Bensz Conan",
            summary="summary should be ignored",
            expected_behavior="expected should be ignored",
            actual_behavior="actual should be ignored",
            environment={
                "os": {"family": "Darwin"},
                "runtime": {"agent_runtime": "codex-cli"},
                "software_versions": {"python3": "Python 3.12.0"},
            },
        )

        self.assertEqual(
            payload,
            {
                "skill": {"name": "demo-skill"},
                "environment": {"runtime": {"agent_runtime": "codex-cli"}},
            },
        )

    def test_build_bug_directory_respects_path_pattern(self) -> None:
        config = deepcopy(self.config)
        config["storage"]["path_pattern"] = "{reporter}/issues/{skill_name}/{bug_hash}"
        root = Path("/tmp/bugs")

        bug_dir = common.build_bug_directory(
            config,
            root,
            "Demo Skill",
            "octocat",
            "abc123",
        )

        self.assertEqual(bug_dir, Path("/tmp/bugs/octocat/issues/demo-skill/abc123"))

    def test_bug_report_markdown_uses_configured_privacy_notice(self) -> None:
        config = deepcopy(self.config)
        config["reporting"]["privacy_notice"] = "自定义隐私提示"
        template = "Privacy: {privacy_notice}\nSkill: {skill_name}\n"
        context = {
            "bug_hash": "hash",
            "skill": {"name": "demo-skill", "author": "Bensz Conan", "source_path": None, "source_repo": None},
            "reporter": {"github_username": "octocat"},
            "bug": {
                "severity": "important",
                "summary": "x",
                "expected_behavior": "y",
                "actual_behavior": "z",
                "reproduction_steps": [],
                "evidence": [],
                "impact": "i",
                "workaround": None,
                "additional_notes": None,
            },
            "environment": {"device": {}, "runtime": {}, "software_versions": {}, "os": {}},
            "tracking": {"occurrence_count": 1, "collected_at": "2026-03-27T00:00:00Z"},
        }

        rendered = common.bug_report_markdown(template, context, config)

        self.assertIn("自定义隐私提示", rendered)

    def test_collect_bug_script_writes_sanitized_local_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            command = [
                sys.executable,
                str(SCRIPTS_DIR / "collect_bug.py"),
                "--skill-name",
                "demo-skill",
                "--skill-author",
                "Bensz Conan",
                "--bug-summary",
                "Authorization: Bearer sk-1234567890abcdefghijklmn",
                "--expected-behavior",
                "Should not leak alice@example.com",
                "--actual-behavior",
                "Logs show +1 415-555-1234",
                "--reproduction-step",
                "Open /Users/alice/private/project",
                "--evidence",
                "Card 4111 1111 1111 1111 exposed",
                "--skill-source-path",
                "/Users/alice/private/project",
                "--reporter-github",
                "octocat",
                "--bug-root",
                tmpdir,
                "--print-json",
            ]
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            payload = json.loads(result.stdout)

            context_path = Path(payload["context_path"])
            report_path = Path(payload["report_path"])
            context = json.loads(context_path.read_text(encoding="utf-8"))
            report = report_path.read_text(encoding="utf-8")
            rendered_context = json.dumps(context, ensure_ascii=False)

            for forbidden in (
                "sk-1234567890abcdefghijklmn",
                "alice@example.com",
                "+1 415-555-1234",
                "4111 1111 1111 1111",
                "/Users/alice/private/project",
            ):
                self.assertNotIn(forbidden, rendered_context)
                self.assertNotIn(forbidden, report)

            self.assertIsNone(context["reporter"]["local_username"])
            self.assertIsNone(context["environment"]["runtime"]["cwd"])
            self.assertIsNone(context["environment"]["runtime"]["hostname"])
            self.assertIsNone(context["tracking"]["local_path"])
            self.assertIn("[redacted:secret]", report)
            self.assertIn("[redacted:private-path]", report)


if __name__ == "__main__":
    unittest.main()
