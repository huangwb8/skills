"""Public helper regressions; artifacts/caches are configured by the caller."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/alpha/humanization/scripts/check_revision.py"
spec = importlib.util.spec_from_file_location("humanization_protection", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


SOURCE = (
    "已有结果仅提示关联\\cite[见][第2页]{demo2026}，未确定因果关系。\n"
    "若拒答率超过 $0.8$，则暂停扩展；分母为全部纳入样本。"
    "结果仅在 \\texttt{RELEASE} 状态下进入 H_0 与 H+A 分层。 % 保留注释\n"
)


def test_natural_rewording_preserves_protected_spans():
    revised = SOURCE.replace("已有结果仅提示关联", "现有结果只提示关联")
    assert checker.compare(SOURCE, revised)["status"] == "pass"


@pytest.mark.parametrize("before,after", [
    ("demo2026", "other2026"),
    ("第2页", "第3页"),
    ("$0.8$", "$0.9$"),
    ("RELEASE", "ABSTAIN"),
    ("H_0", "H_1"),
    ("H+A", "A-only"),
    ("保留注释", "修改注释"),
    ("\\cite[见]", "\\ref[见]"),
])
def test_detects_protected_mutations(before, after):
    assert checker.compare(SOURCE, SOURCE.replace(before, after))["status"] == "fail"


@pytest.mark.parametrize("text,revised", [
    ("一段。\n\n下一段。", "一段。\n过渡。\n下一段。"),
    ("  第一行。\n", "第一行。\n"),
    ("- 第一项。\n", "第一项。\n"),
    ("第一行。\r\n", "第一行。\n"),
    ("第一行。\n", "第一行。"),
])
def test_detects_line_structure_changes(text, revised):
    assert "line_structure_changed" in checker.compare(text, revised)["differences"]


@pytest.mark.parametrize("token", [
    r"\caption{中文{嵌套}说明}",
    r"\cite[说明{含]括号}]{key}",
    "\\caption\n{中文说明}",
    r"\(a+b\)",
    r"\[x^2\]",
    "$$a+b$$",
    "`x=1`",
    "```python\nx=1\n```",
    r"\%",
    "https://example.org/a",
    "10 mg",
    "5天",
])
def test_capture_and_detect_each_literal_span(token):
    protected = checker.protected_tokens(token)
    assert protected
    assert checker.compare(token, token)["status"] == "pass"
    assert checker.compare(token, "说明")["status"] == "fail"


def test_plain_reflow_requires_explicit_mode():
    before, after = "背景。\n\n问题。", "背景。问题。"
    assert checker.compare(before, after)["status"] == "fail"
    assert checker.compare(before, after, "reflow_plain")["status"] == "pass"


@pytest.mark.parametrize("text", [r"内容\cite{key}", "- 步骤。", "# 标题", "| 字段 | 值 |", "$0.8$", r"\(x\)", "`Export`",
                                  "标题\n===", "标题\n---", "    code", "\tcode", "换行\\\\\n继续。"])
def test_reflow_rejects_protected_markup(text):
    with pytest.raises(checker.UnsupportedInput, match="reflow_requires_plain"):
        checker.compare(text, text, "reflow_plain")


@pytest.mark.parametrize("text", [r"\cite{broken", "$unclosed", r"\verb|code|", "~~~code~~~"])
def test_uncertain_parse_cannot_pass(text):
    with pytest.raises(checker.UnsupportedInput):
        checker.compare(text, text)


def test_lexical_pass_does_not_prove_semantics():
    # Same literals, wrong threshold operator and denominator: semantic review must catch it.
    revised = SOURCE.replace("超过", "达到").replace("全部纳入样本", "可评分样本")
    result = checker.compare(SOURCE, revised)
    assert result["status"] == "pass"
    assert result["semantic_review"] == "required"


def test_cli_from_other_directory_and_private_error_output(tmp_path):
    original, revised = tmp_path / "original.txt", tmp_path / "revised.txt"
    original.write_bytes(SOURCE.encode())
    revised.write_bytes(SOURCE.encode())
    command = [sys.executable, str(SCRIPT), str(original), str(revised)]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "pass"
    revised.write_text(SOURCE.replace("0.8", "0.9"), encoding="utf-8")
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1
    assert "demo2026" not in result.stdout
    revised.unlink()
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 2
    assert "FileNotFoundError" in result.stdout
    assert str(tmp_path) not in result.stdout
