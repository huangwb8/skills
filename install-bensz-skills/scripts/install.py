#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# 添加 scripts 目录到 Python 路径，以便导入 i18n
_scripts_dir = Path(__file__).parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from i18n import get_translator


@dataclass(frozen=True)
class Target:
    label: str
    root: Path
    legacy_link: Path


@dataclass
class SkillType:
    """技能类型枚举。"""
    AUXILIARY: str = "auxiliary"  # 辅助技能（开发用，不安装）
    NORMAL: str = "normal"        # 普通技能（可安装）
    TEST: str = "test"            # 测试技能（测试用，不安装）


@dataclass
class SkillInfo:
    name: str
    src: Path
    dest: Path
    md5: str
    skill_type: str = SkillType.NORMAL  # 技能类型
    installed: bool = False
    skipped: bool = False
    reason: str = ""


def _now_stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())


def _is_symlink(path: Path) -> bool:
    try:
        return path.is_symlink()
    except OSError:
        return False


def _ignore_patterns():
    return shutil.ignore_patterns(
        ".DS_Store",
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".pytest_cache",
        ".mypy_cache",
        "test",
        "tests",
        "plans",
    )


def _print_skill_table(
    installed_skills: list[SkillInfo],
    skipped_skills: list[SkillInfo],
    t: get_translator().__class__,
) -> None:
    """以表格形式打印 skills 安装结果。

    表格格式：
    ┌──────────────────────────────┬──────────────┬─────────────────────────────────┐
    │ Skill 名称                   │ 状态         │ 原因                             │
    ├──────────────────────────────┼──────────────┼─────────────────────────────────┤
    │ systematic-literature-review │ ✅ 已安装    │ 版本已更新 (MD5: xxx...)        │
    │ knit-rmd-html                │ ⏭️  跳过     │ 版本未变化                      │
    └──────────────────────────────┴──────────────┴─────────────────────────────────┘
    """
    if not installed_skills and not skipped_skills:
        return

    # 获取列标题
    header_skill = t.table_header_skill()
    header_status = t.table_header_status()
    header_reason = t.table_header_reason()

    # 计算列宽（基于内容）
    all_skills = installed_skills + skipped_skills
    max_name_len = max((len(skill.name) for skill in all_skills), default=20)
    # 考虑 emoji 宽度（实际显示宽度约为字符数的2倍）
    name_width = max(max_name_len, len(header_skill)) + 2

    # 计算原因列的最大宽度（考虑中文和英文）
    reason_samples = []
    for skill in all_skills:
        if skill.installed:
            reason_samples.append(t.table_reason_updated(md5=skill.md5[:12]))
        else:
            reason_samples.append(t.table_reason_no_change())

    # 计算实际显示宽度（中文算2个字符宽度）
    def display_width(s: str) -> int:
        return sum(2 if ord(c) > 127 else 1 for c in s)

    max_reason_display = max((display_width(r) for r in reason_samples), default=20)
    reason_width = max(max_reason_display, display_width(header_reason)) + 4

    # 状态列固定宽度
    status_width = 14

    # 构建分隔线
    separator = "─" * name_width + "┬" + "─" * status_width + "┬" + "─" * reason_width
    top_border = "┌" + separator + "┐"
    bottom_border = "└" + separator.replace("┬", "┴") + "┘"
    row_separator = "├" + separator.replace("┬", "┼") + "┤"

    # 打印表格
    print()
    print(top_border)

    # 表头
    print(
        f"│ {header_skill:<{name_width}} │ {header_status:<{status_width}} │ {header_reason:<{reason_width}} │"
    )
    print(row_separator)

    # 按状态排序：已安装的在前，跳过的在后
    sorted_skills = sorted(all_skills, key=lambda s: not s.installed)

    for skill in sorted_skills:
        if skill.installed:
            status = t.table_status_installed()
            reason = t.table_reason_updated(md5=skill.md5[:12])
        else:
            status = t.table_status_skipped()
            reason = t.table_reason_no_change()

        print(
            f"│ {skill.name:<{name_width}} │ {status:<{status_width}} │ {reason:<{reason_width}} │"
        )

    print(bottom_border)


def _calculate_skill_md5(skill_dir: Path) -> str:
    """计算 skill 目录的 MD5 哈希值。

    优先计算 SKILL.md 的哈希值，因为它是技能的核心定义文件。
    如果需要更精确的版本控制，可以遍历整个目录。
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        # 回退到整个目录的哈希
        hasher = hashlib.md5()
        for file in sorted(skill_dir.rglob("*")):
            if file.is_file() and not any(p.startswith(".") for p in file.relative_to(skill_dir).parts):
                hasher.update(file.read_bytes())
        return hasher.hexdigest()

    content = skill_md.read_text(encoding="utf-8")
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def _get_installed_md5(dest_dir: Path, target: Target) -> str | None:
    """获取已安装 skill 的 MD5 值。

    从平台特定的 manifest 文件读取（如 .skill-manifest.claude.json），
    或回退到计算目录内容的 MD5。

    Args:
        dest_dir: 技能目标目录
        target: 目标平台信息（codex/claude）
    """
    # 平台特定的 manifest 文件名（避免不同平台的版本记录互相干扰）
    manifest_file = dest_dir / f".skill-manifest.{target.label}.json"
    if manifest_file.exists():
        try:
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            return data.get("md5")
        except (json.JSONDecodeError, KeyError):
            pass

    # 回退方案：尝试直接计算目录 MD5
    if dest_dir.exists():
        try:
            return _calculate_skill_md5(dest_dir)
        except Exception:
            pass

    return None


def _save_skill_manifest(dest_dir: Path, md5: str, source: Path, target: Target) -> None:
    """保存 skill 的版本信息到平台特定的 manifest 文件。

    Args:
        dest_dir: 技能目标目录
        md5: 技能内容的 MD5 哈希值
        source: 技能源目录路径
        target: 目标平台信息（codex/claude）
    """
    # 平台特定的 manifest 文件名
    manifest_file = dest_dir / f".skill-manifest.{target.label}.json"
    manifest_data = {
        "md5": md5,
        "source": str(source),
        "installed_at": _now_stamp(),
        "target": target.label,
    }
    manifest_file.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _get_skill_category_from_yaml(skill_dir: Path) -> str | None:
    """从 SKILL.md 的 YAML frontmatter 读取 category 字段。

    Returns:
        category 值（如 "auxiliary", "normal", "test"），如果不存在则返回 None
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None

    try:
        content = skill_md.read_text(encoding="utf-8")
        lines = content.split("\n")
        in_frontmatter = False
        for line in lines[:30]:  # 只检查前30行
            stripped = line.strip()
            if stripped == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    break
                continue
            if in_frontmatter and line.startswith("category:"):
                category = line.split(":", 1)[1].strip().strip('"').strip("'")
                return category.lower()
    except Exception:
        pass

    return None


def _determine_skill_type(skill_dir: Path, skills_root: Path) -> str:
    """确定技能的类型（auxiliary/normal/test）。

    判断优先级：
    1. YAML frontmatter 中的 category 字段（最高优先级）
    2. 基于目录名和路径的启发式规则

    Args:
        skill_dir: 技能目录路径
        skills_root: skills 根目录

    Returns:
        技能类型：SkillType.AUXILIARY, SkillType.NORMAL, 或 SkillType.TEST
    """
    # 优先级1：从 YAML 读取 category（最高优先级，显式声明优先于启发式规则）
    category = _get_skill_category_from_yaml(skill_dir)
    if category:
        if category in {"auxiliary", "dev", "development"}:
            return SkillType.AUXILIARY
        elif category in {"test", "testing"}:
            return SkillType.TEST
        elif category in {"normal", "production"}:
            return SkillType.NORMAL
        # 其他值：继续检查启发式规则（向后兼容）

    # 优先级2：检查是否在 test/ 或 tests/ 目录下
    rel_path = skill_dir.relative_to(skills_root)
    if any(part in {"test", "tests"} for part in rel_path.parts):
        return SkillType.TEST

    # 优先级3：基于目录名的启发式规则
    dir_name = skill_dir.name.lower()

    # 辅助技能识别规则（仅限真正用于开发/维护的辅助工具）
    auxiliary_patterns = {
        "install-bensz-skills",  # 安装器自身
    }
    if dir_name in auxiliary_patterns:
        return SkillType.AUXILIARY

    # 测试技能识别规则（时间戳格式）
    import re
    if re.match(r"^\d{8}_\d{6}$", dir_name):
        return SkillType.TEST

    # 测试技能识别规则（目录名包含 test）
    test_patterns = ["test-", "-test", "_test", "test_"]
    if any(pattern in dir_name for pattern in test_patterns):
        return SkillType.TEST

    # 默认：普通技能
    return SkillType.NORMAL


def _is_test_skill_dir(skill_dir: Path) -> bool:
    """判断是否为测试技能目录（向后兼容）。

    注意：此函数已废弃，请使用 _determine_skill_type() 替代。
    保留此函数是为了向后兼容旧代码。
    """
    return _determine_skill_type(skill_dir, skill_dir.parents[1]) == SkillType.TEST


def _find_skill_dirs(skills_root: Path, exclude_names: set[str]) -> dict[str, list[Path]]:
    """发现所有技能目录并按类型分类。

    Returns:
        包含三个键的字典：
        - "normal": 普通技能列表（可安装）
        - "auxiliary": 辅助技能列表（不安装）
        - "test": 测试技能列表（不安装）
    """
    # 按类型分组的技能目录
    skill_dirs_by_type: dict[str, list[Path]] = {
        SkillType.NORMAL: [],
        SkillType.AUXILIARY: [],
        SkillType.TEST: [],
    }

    for skill_md in sorted(skills_root.rglob("SKILL.md")):
        skill_dir = skill_md.parent
        if skill_dir.name in exclude_names:
            continue
        # Skip hidden dirs just in case.
        if any(part.startswith(".") for part in skill_dir.relative_to(skills_root).parts):
            continue

        # 确定技能类型
        skill_type = _determine_skill_type(skill_dir, skills_root)
        skill_dirs_by_type[skill_type].append(skill_dir)

    # Ensure no basename collisions (we install by directory name).
    # 仅检查普通技能的冲突（因为只有普通技能会被安装）
    by_name: dict[str, list[Path]] = {}
    for d in skill_dirs_by_type[SkillType.NORMAL]:
        by_name.setdefault(d.name, []).append(d)
    collisions = {name: paths for name, paths in by_name.items() if len(paths) > 1}
    if collisions:
        msg = ["检测到 skill 目录名冲突（basename 重复），无法安全安装："]
        for name, paths in sorted(collisions.items()):
            msg.append(f"- {name}: " + ", ".join(str(p) for p in paths))
        raise SystemExit("\n".join(msg))

    return skill_dirs_by_type


@dataclass
class InstallReport:
    """安装报告数据类。"""
    target_label: str
    target_root: Path
    installed_skills: list[SkillInfo]
    skipped_skills: list[SkillInfo]
    auxiliary_skills: list[SkillInfo] = None  # 辅助技能（被忽略）
    test_skills: list[SkillInfo] = None  # 测试技能（被忽略）
    process_messages: list[str] = None  # 安装过程中的消息
    removed_legacy: bool = False
    removed_existing: list[str] = None

    def __post_init__(self):
        if self.auxiliary_skills is None:
            self.auxiliary_skills = []
        if self.test_skills is None:
            self.test_skills = []
        if self.process_messages is None:
            self.process_messages = []
        if self.removed_existing is None:
            self.removed_existing = []

    def to_manifest_dict(self) -> dict:
        """转换为可序列化的字典格式（用于 manifest 文件）。"""
        skills_list = []
        for skill in self.installed_skills:
            skills_list.append({
                "name": skill.name,
                "src": str(skill.src),
                "dest": str(skill.dest),
                "md5": skill.md5,
                "type": skill.skill_type,
                "status": "installed",
                "reason": skill.reason,
            })
        for skill in self.skipped_skills:
            skills_list.append({
                "name": skill.name,
                "src": str(skill.src),
                "dest": str(skill.dest),
                "md5": skill.md5,
                "type": skill.skill_type,
                "status": "skipped",
                "reason": skill.reason,
            })

        return {
            "installed_at": _now_stamp(),
            "target": self.target_label,
            "target_root": str(self.target_root),
            "installed_count": len(self.installed_skills),
            "skipped_count": len(self.skipped_skills),
            "auxiliary_count": len(self.auxiliary_skills),
            "test_count": len(self.test_skills),
            "skills": skills_list,
        }


def _print_skill_list_by_type(skills: list[SkillInfo], title: str, t: get_translator().__class__) -> None:
    """打印指定类型的技能列表。

    Args:
        skills: 技能列表
        title: 类别标题（如"辅助技能"、"测试技能"）
        t: 翻译器实例
    """
    if not skills:
        return

    print()
    print(f"【{title}】({len(skills)} 个)")
    for skill in sorted(skills, key=lambda s: s.name):
        status_icon = "✅" if skill.installed else "⏭️"
        status_text = "已安装" if skill.installed else "跳过"
        print(f"   • {skill.name} {status_icon} {status_text}")
        if skill.reason:
            print(f"     原因: {skill.reason}")


def _print_report(report: InstallReport, t: get_translator().__class__) -> None:
    """以固定格式打印安装报告。

    新的报告格式（v4.0）：
    ┌────────────────────────────────────────┐
    │ 【安装过程】                           │
    │ ✅ installed: ...                      │
    │ ⏭️  skipped: ...                       │
    │                                        │
    │ 【普通技能】(可安装)                   │
    │ ┌─ 表格 ─┐                            │
    │                                        │
    │ 【辅助技能】(已忽略，开发用)           │
    │ • auto-test-skill                      │
    │ • install-bensz-skills                 │
    │                                        │
    │ 【测试技能】(已忽略，测试用)           │
    │ • v202601021343                        │
    │                                        │
    │ 📊 统计：...                          │
    └────────────────────────────────────────┘
    """
    print()
    print(t.report_section_process())
    print("─" * 60)

    # 输出过程消息
    for msg in report.process_messages:
        print(msg)

    if not report.process_messages:
        print(t.report_no_actions())

    # 输出普通技能的安装摘要表格（只有普通技能会被安装）
    print()
    print(t.report_section_summary())
    print("─" * 60)
    _print_skill_table(report.installed_skills, report.skipped_skills, t)

    # 输出辅助技能列表（被忽略）
    _print_skill_list_by_type(
        report.auxiliary_skills,
        "辅助技能（已忽略，仅用于开发）",
        t
    )

    # 输出测试技能列表（被忽略）
    _print_skill_list_by_type(
        report.test_skills,
        "测试技能（已忽略，仅用于测试）",
        t
    )

    # 输出统计
    total_installed = len(report.installed_skills)
    total_skipped = len(report.skipped_skills)
    total_auxiliary = len(report.auxiliary_skills)
    total_test = len(report.test_skills)

    print()
    print("─" * 60)
    print("📊 统计")
    print("─" * 60)
    print(f"普通技能: {total_installed} 个已安装, {total_skipped} 个跳过")
    if total_auxiliary > 0:
        print(f"辅助技能: {total_auxiliary} 个已忽略（开发用，不安装）")
    if total_test > 0:
        print(f"测试技能: {total_test} 个已忽略（测试用，不安装）")


def _remove_existing(dest: Path, dry_run: bool, t: get_translator().__class__) -> str:
    """直接删除已存在的 skill 目录或文件。

    Returns:
        操作消息
    """
    if not dest.exists() and not dest.is_symlink():
        return ""

    if dry_run:
        return f"{t.get('dry_run_prefix')}remove existing: {dest}"

    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    else:
        shutil.rmtree(dest)

    return t.removed_existing(dest=dest)


def _copy_fresh(src: Path, dest: Path, dry_run: bool, t: get_translator().__class__) -> str:
    """复制 skill 目录到目标位置。

    Returns:
        操作消息
    """
    if dry_run:
        return f"{t.get('dry_run_prefix')}install: {src} -> {dest}"
    shutil.copytree(src, dest, symlinks=False, dirs_exist_ok=False, ignore=_ignore_patterns())
    return t.installed(dest=dest)


def _safe_remove_legacy_symlink(path: Path, dry_run: bool, t: get_translator().__class__) -> str:
    """移除旧的软链接（pipeline-skills）。

    Returns:
        操作消息（如果没有操作则返回空字符串）
    """
    if not path.exists() and not path.is_symlink():
        return ""
    if _is_symlink(path):
        if dry_run:
            return f"{t.get('dry_run_prefix')}remove legacy symlink: {path}"
        else:
            path.unlink()
            return t.removed_legacy_symlink(path=path)
    return t.skip_legacy_path(path=path)


def _install_to_target(
    *,
    target: Target,
    skills_root: Path,
    skill_dirs_by_type: dict[str, list[Path]],
    dry_run: bool,
    force: bool = False,
    t: get_translator().__class__,
) -> InstallReport:
    """安装 skills 到指定目标，返回安装报告。

    仅安装普通技能（normal），辅助技能和测试技能将被记录但不安装。

    Args:
        target: 目标平台配置
        skills_root: skills 根目录
        skill_dirs_by_type: 按类型分组的技能目录字典
        dry_run: 预览模式
        force: 强制重装
        t: 翻译器

    Returns:
        InstallReport 包含所有类型的技能信息
    """
    process_messages: list[str] = []
    installed_skills: list[SkillInfo] = []
    skipped_skills: list[SkillInfo] = []
    auxiliary_skills: list[SkillInfo] = []
    test_skills: list[SkillInfo] = []

    # 处理旧的软链接
    legacy_msg = _safe_remove_legacy_symlink(target.legacy_link, dry_run=dry_run, t=t)
    if legacy_msg:
        process_messages.append(legacy_msg)

    target.root.mkdir(parents=True, exist_ok=True)

    # 仅处理普通技能（安装或跳过）
    for src_dir in skill_dirs_by_type[SkillType.NORMAL]:
        dest_dir = target.root / src_dir.name
        src_md5 = _calculate_skill_md5(src_dir)
        # force 模式下忽略已安装的 MD5，强制重新安装
        installed_md5 = None if force else _get_installed_md5(dest_dir, target)

        skill_info = SkillInfo(
            name=src_dir.name,
            src=src_dir,
            dest=dest_dir,
            md5=src_md5,
            skill_type=SkillType.NORMAL,
        )

        # 检查是否需要安装
        if installed_md5 == src_md5:
            reason_msg = t.table_reason_no_change()
            skill_info.skipped = True
            skill_info.reason = reason_msg
            skipped_skills.append(skill_info)
            continue

        # 需要安装：直接删除旧版本，不再备份
        remove_msg = _remove_existing(dest_dir, dry_run=dry_run, t=t)
        if remove_msg:
            process_messages.append(remove_msg)

        copy_msg = _copy_fresh(src_dir, dest=dest_dir, dry_run=dry_run, t=t)
        if copy_msg:
            process_messages.append(copy_msg)

        if not dry_run:
            _save_skill_manifest(dest_dir, src_md5, src_dir, target)

        reason_msg = t.table_reason_updated(md5=src_md5)
        skill_info.installed = True
        skill_info.reason = reason_msg
        installed_skills.append(skill_info)

    # 记录辅助技能（不安装）
    for src_dir in skill_dirs_by_type[SkillType.AUXILIARY]:
        skill_info = SkillInfo(
            name=src_dir.name,
            src=src_dir,
            dest=target.root / src_dir.name,  # 虚拟目标，不会实际安装
            md5=_calculate_skill_md5(src_dir),
            skill_type=SkillType.AUXILIARY,
            skipped=True,
            reason="辅助技能（开发用，不安装到生产环境）",
        )
        auxiliary_skills.append(skill_info)

    # 记录测试技能（不安装）
    for src_dir in skill_dirs_by_type[SkillType.TEST]:
        skill_info = SkillInfo(
            name=src_dir.name,
            src=src_dir,
            dest=target.root / src_dir.name,  # 虚拟目标，不会实际安装
            md5=_calculate_skill_md5(src_dir),
            skill_type=SkillType.TEST,
            skipped=True,
            reason="测试技能（测试用，不安装到生产环境）",
        )
        test_skills.append(skill_info)

    # 构建报告
    report = InstallReport(
        target_label=target.label,
        target_root=target.root,
        installed_skills=installed_skills,
        skipped_skills=skipped_skills,
        auxiliary_skills=auxiliary_skills,
        test_skills=test_skills,
        process_messages=process_messages,
    )

    return report


def _get_manifest_dir() -> Path:
    """获取 manifest 文件的专用存储目录。

    目录位置：~/.install-bensz-skills/manifests/

    Returns:
        manifest 存储目录路径
    """
    manifest_dir = Path.home() / ".install-bensz-skills" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    return manifest_dir


def _migrate_old_manifests() -> list[str]:
    """迁移旧位置的 manifest 文件到新目录。

    旧位置：~/.bensz-skills-install-manifest.*.json
    新位置：~/.install-bensz-skills/manifests/

    Returns:
        迁移的文件列表
    """
    home = Path.home()
    manifest_dir = _get_manifest_dir()
    migrated: list[str] = []

    # 查找所有旧位置的 manifest 文件
    old_pattern = ".bensz-skills-install-manifest.*.json"
    for old_file in home.glob(old_pattern):
        if old_file.is_file():
            # 提取时间戳部分作为新文件名
            stem = old_file.stem  # .bensz-skills-install-manifest.20250112-160600
            timestamp = stem.split(".")[-1] if "." in stem else _now_stamp()
            new_file = manifest_dir / f"install-manifest.{timestamp}.json"

            try:
                shutil.move(str(old_file), str(new_file))
                migrated.append(f"{old_file.name} -> {new_file.relative_to(home)}")
            except Exception as e:
                # 迁移失败时跳过，不影响安装流程
                print(f"⚠️  迁移失败: {old_file} -> {e}")

    return migrated


def main(argv: list[str]) -> int:
    # 初始化翻译器
    t = get_translator()

    parser = argparse.ArgumentParser(description=t.get("arg_help_description"))
    parser.add_argument("--dry-run", action="store_true", help=t.get("arg_help_dry_run"))
    parser.add_argument("--codex", action="store_true", help=t.get("arg_help_codex"))
    parser.add_argument("--claude", action="store_true", help=t.get("arg_help_claude"))
    parser.add_argument("--force", action="store_true", help=t.get("arg_help_force"))
    parser.add_argument("--source", type=str, default=None, help="指定额外的 skills 源目录路径")
    args = parser.parse_args(argv)

    install_codex = args.codex or (not args.codex and not args.claude)
    install_claude = args.claude or (not args.codex and not args.claude)

    script_path = Path(__file__).resolve()
    default_skills_root = script_path.parents[2]  # .../pipelines/skills/

    # 处理源目录：可以是单个目录或多个目录（用逗号分隔）
    if args.source:
        # 支持逗号分隔的多个源目录
        source_paths = [Path(p).resolve() for p in args.source.split(",")]
        # 使用第一个指定的源目录作为主目录（用于版本控制等）
        skills_root = source_paths[0]
    else:
        source_paths = [default_skills_root]
        skills_root = default_skills_root

    # 按类型发现技能目录（支持多个源目录）
    exclude = {"install-bensz-skills"}

    # 合并所有源目录的技能
    merged_skill_dirs_by_type: dict[str, list[Path]] = {
        SkillType.NORMAL: [],
        SkillType.AUXILIARY: [],
        SkillType.TEST: [],
    }

    for source_root in source_paths:
        if not source_root.exists():
            print(f"⚠️  警告: 源目录不存在，跳过: {source_root}")
            continue
        print(f"🔍 扫描源目录: {source_root}")
        skill_dirs_by_type = _find_skill_dirs(source_root, exclude_names=exclude)
        for skill_type in [SkillType.NORMAL, SkillType.AUXILIARY, SkillType.TEST]:
            merged_skill_dirs_by_type[skill_type].extend(skill_dirs_by_type[skill_type])

    normal_skill_dirs = merged_skill_dirs_by_type[SkillType.NORMAL]

    if not normal_skill_dirs:
        print(t.error_no_skills_found(root=skills_root))
        return 1

    targets: list[Target] = []
    home = Path.home()
    if install_codex:
        targets.append(
            Target(
                label="codex",
                root=home / ".codex/skills",
                legacy_link=home / ".codex/skills/pipeline-skills",
            )
        )
    if install_claude:
        targets.append(
            Target(
                label="claude",
                root=home / ".claude/skills",
                legacy_link=home / ".claude/skills/pipeline-skills",
            )
        )

    reports: list[InstallReport] = []
    for target in targets:
        print(f"\n{'=' * 60}")
        print(f"📦 {t.installing_to_target(TARGET=target.label.upper(), root=target.root)}")
        print(f"{'=' * 60}")

        # 如果是 force 模式，清除平台特定的 manifest 文件
        if args.force:
            for skill_dir in normal_skill_dirs:
                dest_dir = target.root / skill_dir.name
                # 删除旧版通用 manifest（向后兼容清理）
                old_manifest = dest_dir / ".skill-manifest.json"
                if old_manifest.exists():
                    old_manifest.unlink()
                # 删除新版平台特定 manifest
                new_manifest = dest_dir / f".skill-manifest.{target.label}.json"
                if new_manifest.exists():
                    new_manifest.unlink()

        # 执行安装并获取报告
        report = _install_to_target(
            target=target,
            skills_root=skills_root,
            skill_dirs_by_type=merged_skill_dirs_by_type,
            dry_run=args.dry_run,
            force=args.force,
            t=t,
        )
        reports.append(report)

        # 打印该目标的报告
        _print_report(report, t)

    # 输出总体摘要
    print(f"\n{'=' * 60}")
    print(t.summary_total_header())
    print(f"{'=' * 60}")

    total_installed = sum(len(r.installed_skills) for r in reports)
    total_skipped = sum(len(r.skipped_skills) for r in reports)
    total_auxiliary = len(merged_skill_dirs_by_type[SkillType.AUXILIARY])
    total_test = len(merged_skill_dirs_by_type[SkillType.TEST])

    print(t.summary_total_counts())
    print(t.summary_installed_count(count=total_installed))
    print(t.summary_skipped_count(count=total_skipped))
    if total_auxiliary > 0:
        print(f"辅助技能: {total_auxiliary} 个已忽略（开发用）")
    if total_test > 0:
        print(f"测试技能: {total_test} 个已忽略（测试用）")

    # 按目标分类汇总
    for report in reports:
        target_name = report.target_label
        installed = report.installed_skills
        skipped = report.skipped_skills

        print(f"\n{target_name.upper()}:")
        if installed:
            print(t.summary_new_install(skills=', '.join(s.name for s in installed)))
        if skipped:
            print(t.summary_unchanged(skills=', '.join(s.name for s in skipped)))

    print(f"{'=' * 60}\n")

    # 迁移旧位置的 manifest 文件
    migrated_files = _migrate_old_manifests()
    if migrated_files:
        print(f"📦 迁移旧 manifest 文件到 {'.install-bensz-skills/manifests/'}:")
        for migration in migrated_files:
            print(f"   • {migration}")

    # Write one manifest per run for traceability.
    # 将 reports 转换为可序列化的格式
    manifests_for_save = [r.to_manifest_dict() for r in reports]
    manifests_for_save.append({
        "skills_source_roots": [str(p) for p in source_paths],
        "skill_type_counts": {
            "normal": len(merged_skill_dirs_by_type[SkillType.NORMAL]),
            "auxiliary": len(merged_skill_dirs_by_type[SkillType.AUXILIARY]),
            "test": len(merged_skill_dirs_by_type[SkillType.TEST]),
        }
    })

    if args.dry_run:
        print(t.manifest_preview())
        print(json.dumps({"runs": manifests_for_save}, ensure_ascii=False, indent=2))
        return 0

    # 使用专用目录存储 manifest 文件
    manifest_dir = _get_manifest_dir()
    stamp = _now_stamp()
    manifest_path = manifest_dir / f"install-manifest.{stamp}.json"
    manifest_path.write_text(json.dumps({"runs": manifests_for_save}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 显示相对路径（更简洁）
    print(t.summary_manifest_saved(path=manifest_path.relative_to(Path.home())))

    # 显示提示：如何清理旧 manifest
    print(f"💡 提示: 历史记录保存在 {manifest_path.relative_to(Path.home()).parent}/")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
