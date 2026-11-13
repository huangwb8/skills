from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "check_interpretation_quality.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_interpretation_quality", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MetricExplanationProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checker = load_checker()

    def test_required_metric_explanation_is_not_flagged_as_teaching_tone(self) -> None:
        text = (
            "该指标用于评估预测概率与实际发生率的一致程度，"
            "反映模型的校准关系；当数值接近参考点时可以认为偏差较小。"
        )
        result = self.checker.scan_text(text)
        self.assertEqual(result["teaching_hits"], [])

    def test_template_teaching_prompt_is_still_flagged(self) -> None:
        result = self.checker.scan_text("提示：这个图用于快速判断模型是否可靠。")
        self.assertTrue(result["teaching_hits"])

    def test_protocol_reference_contains_first_and_later_mention_rules(self) -> None:
        text = (SKILL_ROOT / "references" / "metric_explanation_protocol.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## 首次出现协议", text)
        self.assertIn("## 后续出现协议", text)
        self.assertIn("## 指标导读表", text)


if __name__ == "__main__":
    unittest.main()
