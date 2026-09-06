#!/usr/bin/env python3
"""Check the normalized structure of one or more Agent Skills.

The checker is intentionally dependency-free: it validates frontmatter and
Markdown headings without requiring PyYAML, so it can run before installation.
Report mode is non-blocking for legacy Skills; strict mode is suitable for a
new or migrated Skill and exits non-zero on any finding.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


REQUIRED_TOP_LEVEL = ("目标", "流程", "约束")
REQUIRED_FLOW_HEADINGS = ("输入", "执行步骤", "输出", "输出管理", "校验", "失败与恢复")
CONTROL_KEYS = ("state_roots", "initial_state", "states", "verifiers", "gates", "packs", "control_components")
COMMON_CONSTRAINT_TOKENS = (".bensz-api", "BAC", "隐私", "bensz-collect-bugs")
COMMON_BEGIN = "<!-- BEGIN COMMON CONSTRAINTS -->"
COMMON_END = "<!-- END COMMON CONSTRAINTS -->"
FORBIDDEN_MIGRATION_MARKERS = (
    "## 附录：原有详细规范",
    "迁移前的完整规范",
    "以下内容来自迁移前正文",
    "原文见附录",
)
TEMPLATE_PLACEHOLDERS = (
    "{Skill 标题}",
    "说明 Skill 的用途、触发边界",
    "列出必需输入、可选输入",
    "按依赖顺序描述 Agent、脚本或人工执行的步骤",
)
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
SUBHEADING_RE = re.compile(r"^###\s+(.+?)\s*$")
LINK_RE = re.compile(r"\]\(([^)]+)\)")
HASH_RE = re.compile(r"Source-Hash:\s*sha256:([0-9a-f]{64})", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    skill: str
    severity: str
    code: str
    message: str


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}, text
    values: dict[str, str] = {}
    metadata = False
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("metadata:"):
            metadata = True
            continue
        match = re.match(r"^\s{2,}author:\s*[\"']?([^\"']+?)[\"']?\s*$", line)
        if metadata and match:
            values["metadata.author"] = match.group(1).strip()
            continue
        match = re.match(r"^([A-Za-z][\w.-]*):\s*(.*?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip("\"'")
    return values, "\n".join(lines[end + 1 :])


def _headings(body: str) -> tuple[list[str], dict[str, list[str]]]:
    top: list[str] = []
    flow: list[str] = []
    in_flow = False
    for _line_no, line in _unfenced_lines(body):
        top_match = HEADING_RE.match(line)
        if top_match:
            heading = top_match.group(1).strip()
            top.append(heading)
            in_flow = heading == "流程"
            continue
        if in_flow:
            sub_match = SUBHEADING_RE.match(line)
            if sub_match:
                flow.append(sub_match.group(1).strip())
    return top, {"流程": flow}


def _unfenced_lines(body: str):
    """Yield ``(line_number, line)`` for Markdown lines outside fenced blocks.

    Skill examples commonly contain their own ``##`` headings.  Those headings
    are part of a copyable example, not the Skill's section tree, so structure
    checks must ignore them.  The checker already treats backtick fences as the
    Markdown code-block boundary elsewhere; keep the same intentionally small
    parser here and use it consistently for section discovery and slicing.
    """

    in_fence = False
    for line_number, line in enumerate(body.splitlines()):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield line_number, line


def _expects_control(skill_dir: Path) -> bool:
    config = skill_dir / "config.yaml"
    if not config.is_file():
        return False
    lines = config.read_text(encoding="utf-8", errors="replace").splitlines()
    in_runtime = False
    runtime_indent = 0
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        key_match = re.match(r"^\s*([A-Za-z][\w-]*):", line)
        if key_match and key_match.group(1) == "runtime":
            in_runtime = True
            runtime_indent = indent
            continue
        if in_runtime and indent <= runtime_indent and key_match:
            in_runtime = False
        if in_runtime and key_match and key_match.group(1) in CONTROL_KEYS:
            return True
    return False


def _check_template_copy(
    skill_dir: Path, findings: list[Finding], name: str, template_root: Path | None = None
) -> None:
    references = skill_dir / "references"
    if not references.is_dir():
        return
    source_root = template_root or (Path(__file__).resolve().parents[4] / "docs" / "templates")
    for path in references.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "Template-ID:" not in text or "Source-Hash:" not in text:
            continue
        match = HASH_RE.search(text)
        if not match:
            findings.append(Finding(name, "P1", "template-hash-invalid", f"{path}: Source-Hash 格式无效"))
            continue
        template_id_match = re.search(r"Template-ID:\s*([\w-]+)", text)
        if not template_id_match:
            continue
        source = source_root / f"{template_id_match.group(1)}.md"
        if not source.is_file():
            findings.append(Finding(name, "P1", "template-source-missing", f"{path}: 找不到模板源 {source}"))
            continue
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != match.group(1).lower():
            findings.append(Finding(name, "P1", "template-out-of-sync", f"{path}: Source-Hash 与 docs/templates 不一致"))


def _check_common_block(skill_dir: Path, findings: list[Finding], name: str, template_root: Path | None) -> None:
    path = skill_dir / "SKILL.md"
    text = path.read_text(encoding="utf-8", errors="replace")
    if template_root is None:
        return
    source = template_root / "skill-common-constraints.md"
    if not source.is_file():
        return
    template = source.read_text(encoding="utf-8").strip() + "\n"
    expected_hash = hashlib.sha256(template.encode("utf-8")).hexdigest()
    pattern = re.compile(re.escape(COMMON_BEGIN) + r"\n<!-- Source-Hash: sha256:([0-9a-f]{64}) -->\n(.*?)" + re.escape(COMMON_END), re.S)
    match = pattern.search(text)
    if not match:
        findings.append(Finding(name, "P1", "common-block-missing", "缺少由 docs/templates/skill-common-constraints.md 同步的公共约束块"))
        return
    if match.group(1) != expected_hash or match.group(2) != template:
        findings.append(Finding(name, "P1", "common-block-out-of-sync", "公共约束块与 docs/templates/skill-common-constraints.md 不一致"))


def check_skill(skill_dir: Path, *, template_root: Path | None = None) -> list[Finding]:
    name = skill_dir.name
    path = skill_dir / "SKILL.md"
    findings: list[Finding] = []
    if not path.is_file():
        return [Finding(name, "P0", "missing-skill", "缺少 SKILL.md")]
    text = path.read_text(encoding="utf-8", errors="replace")
    for marker in FORBIDDEN_MIGRATION_MARKERS:
        if marker in text:
            findings.append(Finding(name, "P1", "appendix-migration", f"正文包含禁止的附录托管标记：{marker}"))
    for marker in TEMPLATE_PLACEHOLDERS:
        if marker in text:
            findings.append(Finding(name, "P1", "template-placeholder", f"正文保留模板占位说明：{marker}"))
    frontmatter, body = _frontmatter(text)
    if not frontmatter:
        findings.append(Finding(name, "P0", "frontmatter-missing", "YAML frontmatter 缺失或未闭合"))
    if not frontmatter.get("name"):
        findings.append(Finding(name, "P0", "name-missing", "frontmatter 缺少 name"))
    elif frontmatter["name"] != name:
        findings.append(Finding(name, "P0", "name-mismatch", f"frontmatter name={frontmatter['name']!r} 与目录名不一致"))
    if not frontmatter.get("description"):
        findings.append(Finding(name, "P0", "description-missing", "frontmatter 缺少 description"))
    if frontmatter.get("metadata.author") != "Bensz Conan":
        findings.append(Finding(name, "P0", "author-invalid", "metadata.author 必须为 Bensz Conan"))

    top, sections = _headings(body)
    # Agent profiles under awesome-code are reusable role cards rather than
    # standalone domain Skills; they still require the canonical public block
    # but are not forced into the full domain Skill body skeleton.
    role_card = skill_dir.parent.parent.name == "awesome-code" and skill_dir.parent.name == "agents"
    if role_card:
        _check_common_block(skill_dir, findings, name, template_root)
        _check_template_copy(skill_dir, findings, name, template_root)
        return findings
    positions: list[int] = []
    for required in REQUIRED_TOP_LEVEL:
        if required not in top:
            findings.append(Finding(name, "P1", f"section-{required}", f"缺少一级章节 ## {required}"))
        else:
            positions.append(top.index(required))
    if positions != sorted(positions):
        findings.append(Finding(name, "P1", "section-order", "目标、流程、约束的一级章节顺序不正确"))

    if "流程" in top:
        flow = sections["流程"]
        for required in REQUIRED_FLOW_HEADINGS:
            if required not in flow:
                findings.append(Finding(name, "P1", f"flow-{required}", f"流程缺少三级章节 ### {required}"))
    constraint_start = top.index("约束") if "约束" in top else None
    constraint_text = ""
    if constraint_start is not None:
        # Re-slice by source lines to preserve arbitrary body text.
        lines = body.splitlines()
        starts = [i for i, line in _unfenced_lines(body) if HEADING_RE.match(line)]
        start_line = starts[constraint_start]
        end_line = starts[constraint_start + 1] if constraint_start + 1 < len(starts) else len(lines)
        constraint_text = "\n".join(lines[start_line:end_line])
    _check_common_block(skill_dir, findings, name, template_root)

    expects_control = _expects_control(skill_dir)
    has_control = "控制" in top or any(item.startswith("控制") for item in top)
    if expects_control and not has_control:
        findings.append(Finding(name, "P1", "control-missing", "config.yaml 声明了控制组件，但缺少 ## 控制"))
    if not expects_control and has_control:
        findings.append(Finding(name, "P2", "control-unexpected", "未声明 State/Verifier/Gate/Pack，却出现 ## 控制；请说明显式采用条件"))

    for target in LINK_RE.findall(text):
        target = target.split("#", 1)[0].strip()
        if target.startswith(("http://", "https://", "mailto:", "#")) or not target.startswith("references/"):
            continue
        if not (skill_dir / target).is_file():
            findings.append(Finding(name, "P1", "reference-missing", f"SKILL.md 引用不存在的 references 文件：{target}"))
    _check_template_copy(skill_dir, findings, name, template_root)
    return findings


def discover(project_root: Path, sources: list[str]) -> list[Path]:
    roots = [project_root / "skills" / source for source in sources]
    result: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        result.extend(sorted(path.parent for path in root.rglob("SKILL.md")))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check normalized Agent Skill structure")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--skill-root", help="check one Skill instead of discovering skills/alpha and skills/beta")
    parser.add_argument("--template-root", help="canonical docs/templates directory used for copy hash checks")
    parser.add_argument("--source", action="append", choices=("alpha", "beta"), default=None)
    parser.add_argument("--mode", choices=("report", "strict"), default="report")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    skills = [Path(args.skill_root).expanduser().resolve()] if args.skill_root else discover(project_root, args.source or ["alpha", "beta"])
    template_root = (
        Path(args.template_root).expanduser().resolve()
        if args.template_root
        else (
            (project_root / "docs" / "templates").resolve()
            if (project_root / "docs" / "templates").is_dir()
            else None
        )
    )
    findings = [finding for skill in skills for finding in check_skill(skill, template_root=template_root)]
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    else:
        for item in findings:
            print(f"{item.severity} {item.skill} [{item.code}] {item.message}")
        print(f"checked_skills={len(skills)} findings={len(findings)} mode={args.mode}")
    return 1 if args.mode == "strict" and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
