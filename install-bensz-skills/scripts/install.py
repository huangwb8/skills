#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# 设置 UTF-8 编码，解决 Windows GBK 环境下的 emoji 显示问题
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加 scripts 目录到 Python 路径，以便导入 i18n
_scripts_dir = Path(__file__).parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from i18n import get_translator
from remove_legacy_skills import (
    load_legacy_skill_names as _load_legacy_skill_names,
    remove_legacy_skills as _remove_legacy_skills,
)

_INSTALLATION_ROOT_PARTS = (".bensz-skills", "installation")


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


@dataclass
class SkillComparison:
    """技能对比结果。"""
    name: str
    remote_md5: str
    local_md5: str | None
    status: str  # "new", "updated", "unchanged"
    remote_path: Path
    local_path: Path | None


def _now_stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())


def _is_symlink(path: Path) -> bool:
    try:
        return path.is_symlink()
    except OSError:
        return False


def _get_installation_root() -> Path:
    """返回 install-bensz-skills 的统一工作根目录。"""
    return Path.home().joinpath(*_INSTALLATION_ROOT_PARTS)


def _get_installation_root_label() -> str:
    """返回相对用户主目录的工作根目录标签。"""
    return str(Path(*_INSTALLATION_ROOT_PARTS))


_IGNORE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "test",
    "tests",
    "plans",
}
_IGNORE_FILE_NAMES = {".DS_Store"}
_IGNORE_ROOT_FILE_NAMES = {"readme.md", "changelog.md"}
_IGNORE_GLOBS = ("*.pyc", "*.pyo")


def _copytree_ignore(src_root: Path):
    """Return a copytree ignore callback based on installable relative paths."""

    def _ignore(current_dir: str, names: list[str]) -> list[str]:
        current_path = Path(current_dir)
        ignored: list[str] = []
        for name in names:
            try:
                rel_path = (current_path / name).relative_to(src_root)
            except ValueError:
                continue
            if _should_ignore_rel_path(rel_path):
                ignored.append(name)
        return ignored

    return _ignore


def _should_ignore_rel_path(rel_path: Path) -> bool:
    if len(rel_path.parts) == 1 and rel_path.name.lower() in _IGNORE_ROOT_FILE_NAMES:
        return True
    if any(part.startswith(".") for part in rel_path.parts):
        return True
    if any(part in _IGNORE_DIR_NAMES for part in rel_path.parts):
        return True
    if rel_path.name in _IGNORE_FILE_NAMES:
        return True
    if any(fnmatch.fnmatch(rel_path.name, pattern) for pattern in _IGNORE_GLOBS):
        return True
    return False


def _path_is_within(path: Path, root: Path) -> bool:
    """Return True if path is root or inside root (after resolve)."""
    try:
        path = path.resolve()
        root = root.resolve()
    except OSError:
        return False
    return path == root or root in path.parents


def _looks_like_skills_root(root: Path) -> bool:
    """Heuristic: a skills root contains at least one immediate subdir with SKILL.md."""
    try:
        if not root.exists() or not root.is_dir():
            return False
        for child in root.iterdir():
            if child.is_dir() and (child / "SKILL.md").is_file():
                return True
    except OSError:
        return False
    return False


def _detect_default_source_roots(script_path: Path) -> list[Path]:
    """Detect a sensible default source root for local install.

    Goal: allow running this installer from a system-installed location (e.g. ~/.codex/skills)
    while still installing skills from the *current project* (cwd).
    """
    cwd = Path.cwd().resolve()
    candidates: list[Path] = []

    # Common layouts:
    # - monorepo: {repo}/pipelines/skills
    # - repo: {repo}/skills
    # - already in skills root: {repo}/(skill dirs...)
    for p in (cwd / "pipelines" / "skills", cwd / "skills", cwd):
        if _looks_like_skills_root(p):
            candidates.append(p)
            break

    # Fallback to "repo-local" layout when this script lives in the same checkout.
    repo_candidate = script_path.parents[2]  # .../pipelines/skills/ (in this repo)
    installed_roots = [
        Path.home() / ".codex" / "skills",
        Path.home() / ".claude" / "skills",
    ]
    if not any(_path_is_within(repo_candidate, r) for r in installed_roots):
        if _looks_like_skills_root(repo_candidate):
            candidates.append(repo_candidate)

    # De-dup while keeping order.
    deduped: list[Path] = []
    seen: set[Path] = set()
    for p in candidates:
        try:
            rp = p.resolve()
        except OSError:
            continue
        if rp not in seen:
            deduped.append(rp)
            seen.add(rp)
    return deduped


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

    # 计算实际显示宽度（中文/emoji 以双宽估算）
    def display_width(s: str) -> int:
        return sum(2 if ord(c) > 127 else 1 for c in s)

    def pad_display(s: str, width: int) -> str:
        padding = width - display_width(s)
        return s + (" " * max(padding, 0))

    # 计算列宽（基于显示宽度）
    all_skills = installed_skills + skipped_skills
    max_name_display = max((display_width(skill.name) for skill in all_skills), default=20)
    name_width = max(max_name_display, display_width(header_skill)) + 2

    # 计算原因列的最大宽度（考虑中文和英文）
    reason_samples = []
    for skill in all_skills:
        if skill.installed:
            reason_samples.append(t.table_reason_updated(md5=skill.md5[:12]))
        else:
            reason_samples.append(t.table_reason_no_change())

    max_reason_display = max((display_width(r) for r in reason_samples), default=20)
    reason_width = max(max_reason_display, display_width(header_reason)) + 4

    # 状态列宽度（考虑 emoji）
    status_samples = [header_status, t.table_status_installed(), t.table_status_skipped()]
    status_width = max(display_width(s) for s in status_samples) + 2

    # 构建分隔线
    separator = "─" * name_width + "┬" + "─" * status_width + "┬" + "─" * reason_width
    top_border = "┌" + separator + "┐"
    bottom_border = "└" + separator.replace("┬", "┴") + "┘"
    row_separator = "├" + separator.replace("┬", "┼") + "┤"

    # 打印表格
    print()
    print(top_border)

    # 表头
    print(f"│ {pad_display(header_skill, name_width)} │ {pad_display(header_status, status_width)} │ {pad_display(header_reason, reason_width)} │")
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

        print(f"│ {pad_display(skill.name, name_width)} │ {pad_display(status, status_width)} │ {pad_display(reason, reason_width)} │")

    print(bottom_border)


def _calculate_skill_md5(skill_dir: Path) -> str:
    """计算 skill 目录的 MD5 哈希值。

    基于可安装文件生成稳定哈希，排除 tests/plans 等不参与安装的内容。
    """
    hasher = hashlib.md5()
    for file in sorted(skill_dir.rglob("*")):
        if not file.is_file():
            continue
        rel_path = file.relative_to(skill_dir)
        if _should_ignore_rel_path(rel_path):
            continue
        hasher.update(str(rel_path).encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(file.read_bytes())
    return hasher.hexdigest()


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


def _save_skill_manifest(dest_dir: Path, md5: str, source: str | Path, target: Target) -> None:
    """保存 skill 的版本信息到平台特定的 manifest 文件。

    Args:
        dest_dir: 技能目标目录
        md5: 技能内容的 MD5 哈希值
        source: 技能源目录路径或稳定来源标识
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
        if not lines or lines[0].strip() != "---":
            return None

        in_frontmatter = False
        for line in lines:
            stripped = line.strip()
            if stripped == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                break
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

    # 辅助技能识别规则（基于目录名，不包含特殊排除）
    # 技能类型应优先通过 YAML frontmatter 中的 category 字段控制
    # 此处仅作为后备识别规则

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

    只扫描顶级 skill 目录（即 skills_root 的直接子目录），跳过子目录中的 skill。
    例如：awesome-code/agents/xxx 中的 SKILL.md 会被跳过。

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

    # 只扫描顶级目录（skills_root 的直接子目录）
    for skill_dir in sorted(skills_root.iterdir()):
        # 跳过排除的目录名
        if skill_dir.name in exclude_names:
            continue
        # 跳过隐藏目录
        if skill_dir.name.startswith("."):
            continue
        # 跳过非目录
        if not skill_dir.is_dir():
            continue

        # 检查是否是 skill 目录（包含 SKILL.md）
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        # 跳过隐藏路径（以防万一）
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


# ============================================================================
# 远程安装相关函数
# ============================================================================

def _load_config(config_path: Path) -> dict:
    """加载配置文件。

    Returns:
        配置字典
    """
    if not config_path.exists():
        raise FileNotFoundError(config_path)

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("缺少 PyYAML 依赖，请先运行 `python3 -m pip install pyyaml`") from exc

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:
        raise RuntimeError(f"配置文件解析失败: {exc}") from exc


def _check_git_available() -> bool:
    """检查 Git 命令是否可用。"""
    try:
        subprocess.run(
            ["git", "--version"],
            capture_output=True,
            check=True,
            text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _create_temp_dir() -> Path:
    """创建临时目录。

    Returns:
        临时目录路径
    """
    temp_dir = _get_installation_root() / "tmp-remote-install"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def _cleanup_temp_dir(temp_dir: Path) -> None:
    """清理临时目录。"""
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


def _sanitize_source_name(name: str, url: str) -> str:
    """生成安全且稳定的临时目录名。"""
    sanitized = name.strip()
    for sep in (os.sep, os.altsep, "/", "\\"):
        if sep:
            sanitized = sanitized.replace(sep, "-")
    sanitized = sanitized.replace(" ", "-").strip(".-")
    sanitized = "-".join(part for part in sanitized.split("-") if part)
    if not sanitized:
        sanitized = "source"
    suffix = hashlib.md5(url.encode("utf-8")).hexdigest()[:8] if url else "local"
    return f"{sanitized}-{suffix}"


def _format_remote_source_label(source_config: dict) -> str:
    """生成可写入 manifest 的稳定来源标识。"""
    name = source_config.get("name", "unknown")
    url = source_config.get("url", "")
    branch = source_config.get("branch", "main")
    skills_path = source_config.get("skills_path", "skills")
    if url:
        return f"{name} ({url}@{branch}:{skills_path})"
    return f"{name} (@{branch}:{skills_path})"


def _resolve_remote_skills_root(repo_root: Path, skills_path: str | None) -> Path | None:
    """解析远程仓库中的 skills 根目录。

    优先使用配置中的 skills_path；如果该路径不存在，但仓库根目录本身
    就是一个 skills 根目录，则回退到仓库根目录。
    """
    raw_path = (skills_path or "").strip()
    requested_path = repo_root if raw_path in {"", "."} else (repo_root / raw_path)

    if requested_path.exists() and _looks_like_skills_root(requested_path):
        return requested_path

    if repo_root != requested_path and _looks_like_skills_root(repo_root):
        return repo_root

    return None


def _download_remote_source(
    source_config: dict,
    temp_dir: Path,
    t: get_translator().__class__,
) -> Path | None:
    """从 GitHub 下载远程技能源到临时目录。

    Args:
        source_config: 源配置字典
        temp_dir: 临时目录
        t: 翻译器

    Returns:
        下载后的技能根目录路径，失败返回 None
    """
    name = source_config.get("name", "unknown")
    url = source_config.get("url", "")
    branch = source_config.get("branch", "main")
    skills_path = source_config.get("skills_path", "skills")

    print(t.remote_download_progress(name=name, url=url))

    # 创建子目录用于克隆
    clone_dir = temp_dir / _sanitize_source_name(name, url)
    clone_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 使用 git clone --depth 1 浅克隆
        subprocess.run(
            [
                "git", "clone",
                "--depth", "1",
                "--branch", branch,
                "--single-branch",
                url,
                str(clone_dir / "repo")
            ],
            capture_output=True,
            check=True,
            text=True,
            timeout=300  # 5分钟超时
        )
    except subprocess.TimeoutExpired:
        print(t.remote_download_failed(name=name, error="timeout"))
        return None
    except subprocess.CalledProcessError as e:
        print(t.remote_download_failed(name=name, error=e.stderr.strip()))
        return None
    except Exception as e:
        print(t.remote_download_failed(name=name, error=str(e)))
        return None

    print(t.remote_download_complete(name=name))

    # 返回技能目录路径
    repo_root = clone_dir / "repo"
    skills_dir = _resolve_remote_skills_root(repo_root, skills_path)
    if skills_dir is None:
        print(t.remote_skills_path_missing(name=name, path=skills_path))
        return None

    return skills_dir


def _compare_remote_skills(
    remote_skills_dir: Path,
    local_target: Path,
    target: Target,
    t: get_translator().__class__,
) -> list[SkillComparison]:
    """对比远程技能与本地已安装技能。

    Args:
        remote_skills_dir: 远程技能目录
        local_target: 本地目标目录（如 ~/.claude/skills）
        target: 目标平台信息
        t: 翻译器

    Returns:
        技能对比结果列表
    """
    comparisons: list[SkillComparison] = []

    # 发现远程技能
    remote_skill_dirs = _find_skill_dirs(remote_skills_dir, exclude_names=set())

    for remote_skill_dir in remote_skill_dirs.get(SkillType.NORMAL, []):
        skill_name = remote_skill_dir.name
        remote_md5 = _calculate_skill_md5(remote_skill_dir)
        local_skill_dir = local_target / skill_name

        if local_skill_dir.exists():
            # 技能已存在，检查是否需要更新
            local_md5 = _get_installed_md5(local_skill_dir, target)
            if local_md5 != remote_md5:
                status = "updated"
            else:
                status = "unchanged"
        else:
            # 新技能
            local_md5 = None
            status = "new"

        comparisons.append(SkillComparison(
            name=skill_name,
            remote_md5=remote_md5,
            local_md5=local_md5,
            status=status,
            remote_path=remote_skill_dir,
            local_path=local_skill_dir if local_skill_dir.exists() else None,
        ))

    return comparisons


def _print_comparison_report(
    comparisons: list[SkillComparison],
    t: get_translator().__class__,
) -> None:
    """打印远程技能对比报告。

    Args:
        comparisons: 技能对比结果列表
        t: 翻译器
    """
    print()
    print(t.remote_compare_header())
    print("─" * 60)

    # 按状态分组
    new_skills = [c for c in comparisons if c.status == "new"]
    updated_skills = [c for c in comparisons if c.status == "updated"]
    unchanged_skills = [c for c in comparisons if c.status == "unchanged"]

    # 打印新增技能
    if new_skills:
        print()
        print(t.remote_compare_new(count=len(new_skills)))
        for skill in new_skills:
            print(f"   • {skill.name}")

    # 打印可更新技能
    if updated_skills:
        print()
        print(t.remote_compare_updated(count=len(updated_skills)))
        for skill in updated_skills:
            print(f"   • {skill.name}")

    # 打印最新技能
    if unchanged_skills:
        print()
        print(t.remote_compare_unchanged(count=len(unchanged_skills)))
        for skill in unchanged_skills:
            print(f"   • {skill.name}")


def _prompt_user_install(
    comparisons: list[SkillComparison],
    source_name: str,
    t: get_translator().__class__,
) -> bool:
    """询问用户是否确认安装/更新远程技能。

    Args:
        comparisons: 技能对比结果列表
        source_name: 源名称
        t: 翻译器

    Returns:
        True 表示用户确认，False 表示取消
    """
    new_count = len([c for c in comparisons if c.status == "new"])
    updated_count = len([c for c in comparisons if c.status == "updated"])
    unchanged_count = len([c for c in comparisons if c.status == "unchanged"])

    # 如果没有需要安装或更新的技能，跳过
    if new_count == 0 and updated_count == 0:
        print(t.remote_no_updates())
        return False

    print()
    print(t.remote_confirm_install_detail(
        new_count=new_count,
        updated_count=updated_count,
        unchanged_count=unchanged_count,
    ))
    response = input(t.remote_confirm_install()).strip().lower()

    return response in ("y", "yes", "是")


def _prompt_source_install(
    source_config: dict,
    t: get_translator().__class__,
) -> bool:
    """询问用户是否安装某个源。

    Args:
        source_config: 源配置
        t: 翻译器

    Returns:
        True 表示用户确认，False 表示跳过
    """
    name = source_config.get("name", "")
    description = source_config.get("description", "")
    recommended = source_config.get("recommended", False)

    if recommended:
        prompt = t.remote_source_prompt_recommended(name=name, description=description)
        default = "y"
    else:
        prompt = t.remote_source_prompt(name=name, description=description)
        default = "n"

    response = input(prompt).strip().lower()
    if not response:
        return default == "y"

    return response in ("y", "yes", "是")


def _install_remote_skills(
    comparisons: list[SkillComparison],
    target: Target,
    force: bool,
    source_label: str,
    legacy_skill_names: list[str],
    t: get_translator().__class__,
) -> InstallReport:
    """安装远程技能。

    Args:
        comparisons: 技能对比结果列表
        target: 目标平台
        force: 是否强制安装
        source_label: 远程来源标识（用于 manifest）
        t: 翻译器

    Returns:
        安装报告
    """
    installed_skills: list[SkillInfo] = []
    skipped_skills: list[SkillInfo] = []
    process_messages: list[str] = []

    # 处理旧的软链接
    legacy_msg = _safe_remove_legacy_symlink(target.legacy_link, dry_run=False, t=t)
    if legacy_msg:
        process_messages.append(legacy_msg)

    target.root.mkdir(parents=True, exist_ok=True)
    process_messages.extend(
        _remove_legacy_skills(
            target_root=target.root,
            legacy_skill_names=legacy_skill_names,
            dry_run=False,
            active_skill_names={comparison.name for comparison in comparisons},
        )
    )

    for comparison in comparisons:
        if comparison.status == "unchanged" and not force:
            skipped_skills.append(SkillInfo(
                name=comparison.name,
                src=comparison.remote_path,
                dest=target.root / comparison.name,
                md5=comparison.remote_md5,
                skill_type=SkillType.NORMAL,
                skipped=True,
                reason=t.table_reason_no_change(),
            ))
            continue

        # 删除旧版本
        dest_dir = target.root / comparison.name
        remove_msg = _remove_existing(dest_dir, dry_run=False, t=t)
        if remove_msg:
            process_messages.append(remove_msg)

        # 复制新版本
        copy_msg = _copy_fresh(comparison.remote_path, dest=dest_dir, dry_run=False, t=t)
        if copy_msg:
            process_messages.append(copy_msg)

        _save_skill_manifest(dest_dir, comparison.remote_md5, source_label, target)

        reason_msg = t.table_reason_updated(md5=comparison.remote_md5[:12])
        installed_skills.append(SkillInfo(
            name=comparison.name,
            src=comparison.remote_path,
            dest=dest_dir,
            md5=comparison.remote_md5,
            skill_type=SkillType.NORMAL,
            installed=True,
            reason=reason_msg,
        ))

    return InstallReport(
        target_label=target.label,
        target_root=target.root,
        installed_skills=installed_skills,
        skipped_skills=skipped_skills,
        auxiliary_skills=[],
        test_skills=[],
        process_messages=process_messages,
    )


def _remote_install_main(
    *,
    auto_mode: bool,
    install_codex: bool,
    install_claude: bool,
    source_filter: list[str] | None = None,
    available_source_ids: list[str] | None = None,
    legacy_skill_names: list[str] | None = None,
    t: get_translator().__class__,
) -> int:
    """远程安装主流程。

    Args:
        auto_mode: 是否自动模式（无需确认）
        install_codex: 是否安装到 Codex
        install_claude: 是否安装到 Claude Code
        source_filter: 要安装的源 ID 列表（None 表示安装所有源）
        available_source_ids: 配置中可用的源 ID 列表
        t: 翻译器

    Returns:
        退出代码
    """
    # 打印介绍
    if auto_mode:
        print(t.remote_auto_intro())
    else:
        print(t.remote_check_intro())

    # 检查 Git
    if not _check_git_available():
        print(t.remote_git_not_found())
        return 1

    # 加载配置
    config_path = Path(__file__).parents[1] / "config.yaml"
    try:
        config = _load_config(config_path)
    except FileNotFoundError:
        print(t.remote_config_not_found(path=config_path))
        return 1
    except RuntimeError as exc:
        print(t.remote_config_error(error=str(exc)))
        return 1

    remote_sources = config.get("remote_sources", [])
    if not remote_sources:
        print(t.remote_config_error(error=f"未配置 remote_sources: {config_path}"))
        return 1

    # 应用源过滤
    if source_filter:
        # 检查无效的源 ID
        valid_ids = {s.get("id", "") for s in remote_sources if s.get("id")}
        invalid_ids = [sid for sid in source_filter if sid not in valid_ids]
        if invalid_ids:
            print(t.remote_source_filter_invalid(invalid_ids=", ".join(invalid_ids)))

        # 过滤源
        filtered_sources = [s for s in remote_sources if s.get("id") in source_filter]
        if not filtered_sources:
            print(t.remote_config_error(error=f"没有找到匹配的源，请检查源 ID: {', '.join(source_filter)}"))
            return 1

        remote_sources = filtered_sources
        print(t.remote_source_filter_selected(sources=", ".join(s.get("name", s.get("id", "")) for s in remote_sources)))

    # 创建临时目录
    temp_dir = _create_temp_dir()
    print(t.remote_temp_dir(path=temp_dir.relative_to(Path.home())))

    # 确定目标
    targets: list[Target] = []
    home = Path.home()
    if install_codex:
        targets.append(Target(
            label="codex",
            root=home / ".codex/skills",
            legacy_link=home / ".codex/skills/pipeline-skills",
        ))
    if install_claude:
        targets.append(Target(
            label="claude",
            root=home / ".claude/skills",
            legacy_link=home / ".claude/skills/pipeline-skills",
        ))

    all_reports: list[InstallReport] = []

    try:
        # 遍历每个远程源
        for source in remote_sources:
            source_name = source.get("name", "unknown")
            source_label = _format_remote_source_label(source)

            # 询问用户是否安装（check 模式）
            if not auto_mode:
                if not _prompt_source_install(source, t):
                    print(t.remote_user_cancelled())
                    continue

            # 下载远程源
            remote_skills_dir = _download_remote_source(source, temp_dir, t)
            if remote_skills_dir is None:
                continue

            # 对每个目标进行处理
            for target in targets:
                print(f"\n{'=' * 60}")
                print(f"📦 {t.installing_to_target(TARGET=target.label.upper(), root=target.root)}")
                print(f"{'=' * 60}")

                # 对比远程与本地技能
                comparisons = _compare_remote_skills(remote_skills_dir, target.root, target, t)

                if not comparisons:
                    print(t.error_no_skills_found(root=remote_skills_dir))
                    continue

                # 打印对比报告（check 模式）
                if not auto_mode:
                    _print_comparison_report(comparisons, t)

                    # 询问用户是否确认安装
                    if not _prompt_user_install(comparisons, source_name, t):
                        print(t.remote_user_cancelled())
                        continue

                # 安装技能
                report = _install_remote_skills(
                    comparisons,
                    target,
                    force=auto_mode,
                    source_label=source_label,
                    legacy_skill_names=legacy_skill_names,
                    t=t,
                )
                all_reports.append(report)

                # 打印报告
                _print_report(report, t)

    finally:
        # 清理临时目录
        _cleanup_temp_dir(temp_dir)
        print()
        print(t.remote_cleanup_complete())

    # 输出总体摘要
    if all_reports:
        print(f"\n{'=' * 60}")
        print(t.summary_total_header())
        print(f"{'=' * 60}")

        installed_skill_names = {s.name for r in all_reports for s in r.installed_skills}
        skipped_skill_names = {s.name for r in all_reports for s in r.skipped_skills}
        total_installed = len(installed_skill_names)
        total_skipped = len(skipped_skill_names)

        print(t.summary_total_counts())
        print(t.summary_installed_count(count=total_installed))
        print(t.summary_skipped_count(count=total_skipped))

        print(f"{'=' * 60}\n")

    return 0


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
    shutil.copytree(
        src,
        dest,
        symlinks=False,
        dirs_exist_ok=False,
        ignore=_copytree_ignore(src),
    )
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
    legacy_skill_names: list[str] | None = None,
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

    process_messages.extend(
        _remove_legacy_skills(
            target_root=target.root,
            legacy_skill_names=legacy_skill_names or [],
            dry_run=dry_run,
            active_skill_names={src_dir.name for src_dir in skill_dirs_by_type[SkillType.NORMAL]},
        )
    )

    if not dry_run:
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

    目录位置：~/.bensz-skills/installation/manifests/

    Returns:
        manifest 存储目录路径
    """
    manifest_dir = _get_installation_root() / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    return manifest_dir


def _migrate_old_manifests() -> list[str]:
    """迁移旧位置的 manifest 文件到新目录。

    旧位置：~/.bensz-skills-install-manifest.*.json
    新位置：~/.bensz-skills/installation/manifests/

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
    parser.add_argument("--remote", action="store_true", help=t.get("arg_help_remote"))
    parser.add_argument("--check", action="store_true", help=t.get("arg_help_check"))
    parser.add_argument("--auto", action="store_true", help=t.get("arg_help_auto"))

    # 加载配置以获取可用的源 ID（用于动态添加 --<id> 参数）
    config_path = Path(__file__).parents[1] / "config.yaml"
    available_source_ids: list[str] = []
    legacy_skill_names: list[str] = []
    if config_path.exists():
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            remote_sources = config.get("remote_sources", [])
            available_source_ids = [s.get("id", "") for s in remote_sources if s.get("id")]
            legacy_skill_names = _load_legacy_skill_names(config_path)
        except Exception:
            pass  # 如果加载失败，跳过动态参数

    # 为每个可用的源 ID 添加布尔参数
    for source_id in available_source_ids:
        parser.add_argument(
            f"--{source_id}",
            action="store_true",
            help=f"仅安装来自 '{source_id}' 的远程源",
            default=False,
        )

    args = parser.parse_args(argv)

    # 远程安装模式
    if args.remote:
        # 验证参数组合
        if args.check and args.auto:
            print("错误: --check 和 --auto 不能同时使用")
            return 1
        if not args.check and not args.auto:
            print("错误: --remote 需要指定 --check 或 --auto")
            return 1

        # 收集用户选择的源 ID
        selected_source_ids: list[str] = []
        for source_id in available_source_ids:
            if hasattr(args, source_id) and getattr(args, source_id):
                selected_source_ids.append(source_id)

        install_codex = args.codex or (not args.codex and not args.claude)
        install_claude = args.claude or (not args.codex and not args.claude)

        return _remote_install_main(
            auto_mode=args.auto,
            install_codex=install_codex,
            install_claude=install_claude,
            source_filter=selected_source_ids if selected_source_ids else None,
            available_source_ids=available_source_ids,
            legacy_skill_names=legacy_skill_names,
            t=t,
        )

    # 本地安装模式（原有逻辑）
    install_codex = args.codex or (not args.codex and not args.claude)
    install_claude = args.claude or (not args.codex and not args.claude)

    script_path = Path(__file__).resolve()

    # 处理源目录：可以是单个目录或多个目录（用逗号分隔）
    if args.source:
        # 支持逗号分隔的多个源目录
        source_paths = [Path(p).resolve() for p in args.source.split(",")]
        # 使用第一个指定的源目录作为主目录（用于版本控制等）
        skills_root = source_paths[0]
    else:
        detected = _detect_default_source_roots(script_path)
        if not detected:
            print(t.get("error_source_root_not_found"))
            return 1
        skills_root = detected[0]
        source_paths = [skills_root]

    # 按类型发现技能目录（支持多个源目录）
    # 不再硬编码排除任何技能——技能类型由 SKILL.md 中的 category 控制

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
        skill_dirs_by_type = _find_skill_dirs(source_root, exclude_names=set())
        for skill_type in [SkillType.NORMAL, SkillType.AUXILIARY, SkillType.TEST]:
            merged_skill_dirs_by_type[skill_type].extend(skill_dirs_by_type[skill_type])

    normal_skill_dirs = merged_skill_dirs_by_type[SkillType.NORMAL]

    name_collisions: dict[str, list[Path]] = {}
    for skill_dir in normal_skill_dirs:
        name_collisions.setdefault(skill_dir.name, []).append(skill_dir)
    collisions = {name: paths for name, paths in name_collisions.items() if len(paths) > 1}
    if collisions:
        msg = [t.error_skill_name_collision()]
        for name, paths in sorted(collisions.items()):
            msg.append(f"- {name}: " + ", ".join(str(p) for p in paths))
        raise SystemExit("\n".join(msg))

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
            legacy_skill_names=legacy_skill_names,
            t=t,
        )
        reports.append(report)

        # 打印该目标的报告
        _print_report(report, t)

    # 输出总体摘要
    print(f"\n{'=' * 60}")
    print(t.summary_total_header())
    print(f"{'=' * 60}")

    # 技能个数统计（去重）：基于唯一技能名称，而非安装次数
    # 使用 set 去重，确保同一个技能在多个平台安装时只计数一次
    installed_skill_names = {s.name for r in reports for s in r.installed_skills}
    skipped_skill_names = {s.name for r in reports for s in r.skipped_skills}
    total_installed = len(installed_skill_names)
    total_skipped = len(skipped_skill_names)
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

    # 迁移旧位置的 manifest 文件
    migrated_files = _migrate_old_manifests()
    if migrated_files:
        print(f"📦 迁移旧 manifest 文件到 {_get_installation_root_label() + '/manifests/'}:")
        for migration in migrated_files:
            print(f"   • {migration}")

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
