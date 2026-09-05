from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
import hashlib
from pathlib import Path


CHECKER = Path(__file__).parents[1] / "skills/alpha/auto-test-project/scripts/check_skill_structure.py"
SPEC = importlib.util.spec_from_file_location("check_skill_structure", CHECKER)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
sys.modules["check_skill_structure"] = checker
SPEC.loader.exec_module(checker)


BODY = """# Demo

## 目标
用途、边界和不负责范围。

## 流程
### 输入
输入。
### 执行步骤
步骤。
### 输出
输出。
### 输出管理
管理。
### 校验
校验。
### 失败与恢复
恢复。

## 约束
遵守 .bensz-api、BAC、隐私和 bensz-collect-bugs。
"""


class SkillStructureCheckerTest(unittest.TestCase):
    def _write_skill(self, root: Path, body: str = BODY) -> Path:
        skill = root / "demo"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: demo\ndescription: demo\nmetadata:\n  author: Bensz Conan\n---\n" + body,
            encoding="utf-8",
        )
        return skill

    def test_normalized_skill_passes(self) -> None:
        template = Path(__file__).parents[1] / "docs/templates/skill-common-constraints.md"
        canonical = template.read_text(encoding="utf-8").strip() + "\n"
        block = (
            "<!-- BEGIN COMMON CONSTRAINTS -->\n"
            f"<!-- Source-Hash: sha256:{hashlib.sha256(canonical.encode()).hexdigest()} -->\n"
            f"{canonical}<!-- END COMMON CONSTRAINTS -->\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            findings = checker.check_skill(self._write_skill(Path(tmp), BODY.replace("遵守 .bensz-api、BAC、隐私和 bensz-collect-bugs。", block)))
        self.assertEqual(findings, [])

    def test_missing_flow_heading_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = self._write_skill(Path(tmp), BODY.replace("### 校验\n校验。\n", ""))
            findings = checker.check_skill(skill)
        self.assertTrue(any(item.code == "flow-校验" for item in findings))

    def test_control_is_required_for_runtime_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = self._write_skill(Path(tmp))
            (skill / "config.yaml").write_text("runtime:\n  states:\n    - demo.state\n", encoding="utf-8")
            findings = checker.check_skill(skill)
        self.assertTrue(any(item.code == "control-missing" for item in findings))

    def test_headings_inside_fenced_examples_are_ignored(self) -> None:
        body = BODY.replace(
            "## 约束\n",
            "```markdown\n## 示例标题\n### 示例子标题\n```\n\n## 约束\n",
        )
        with tempfile.TemporaryDirectory() as tmp:
            findings = checker.check_skill(self._write_skill(Path(tmp), body))
        self.assertEqual(findings, [])

    def test_recursive_discovery_includes_nested_role_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills" / "alpha" / "awesome-code" / "agents" / "demo"
            root.mkdir(parents=True)
            (root / "SKILL.md").write_text(
                "---\nname: demo\ndescription: demo\nmetadata:\n  author: Bensz Conan\n---\n"
                "# Demo\n\n## 约束\n\n<!-- BEGIN COMMON CONSTRAINTS -->\n",
                encoding="utf-8",
            )
            self.assertIn(root, checker.discover(Path(tmp), ["alpha"]))


if __name__ == "__main__":
    unittest.main()
