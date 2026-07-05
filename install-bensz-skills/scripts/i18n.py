#!/usr/bin/env python3
"""Internationalization (i18n) module for install-bensz-skills.

自动检测用户系统语言并返回相应的本地化消息。
"""
from __future__ import annotations

import locale
import os
from dataclasses import dataclass
from typing import Callable


# 支持的语言列表
SUPPORTED_LANGUAGES = ["en", "zh"]


@dataclass(frozen=True)
class Messages:
    """本地化消息集合。"""

    # 通用消息
    arg_help_description: str
    arg_help_dry_run: str
    arg_help_codex: str
    arg_help_claude: str
    arg_help_force: str
    arg_help_skill: str
    arg_help_remote: str
    arg_help_check: str
    arg_help_auto: str
    arg_help_source_filter: str

    # 错误消息
    error_no_skills_found: str
    error_skill_filter_missing: str
    error_skill_filter_not_installable: str
    error_skill_name_collision: str
    error_source_root_not_found: str

    # 安装过程消息
    installing_to_target: str
    removed_legacy_symlink: str
    removed_legacy_skill: str
    skip_legacy_path: str
    removed_existing: str
    installed: str
    dry_run_prefix: str

    # 表格相关消息
    table_header_skill: str
    table_header_status: str
    table_header_reason: str
    table_status_installed: str
    table_status_skipped: str
    table_reason_no_change: str
    table_reason_updated: str
    table_separator: str

    # 安装报告消息（固定格式）
    report_section_process: str
    report_section_summary: str
    report_section_ignored: str
    report_no_actions: str
    report_statistics: str

    # 安装摘要消息（兼容保留）
    summary_header: str
    summary_installed: str
    summary_skipped: str
    summary_reason: str
    summary_total_header: str
    summary_total_counts: str
    summary_installed_count: str
    summary_skipped_count: str
    summary_new_install: str
    summary_unchanged: str
    summary_manifest_saved: str

    # 其他消息
    manifest_preview: str

    # 远程安装消息
    remote_check_intro: str
    remote_auto_intro: str
    remote_source_prompt: str
    remote_source_prompt_recommended: str
    remote_download_progress: str
    remote_download_complete: str
    remote_download_failed: str
    remote_skills_path_missing: str
    remote_compare_header: str
    remote_compare_new: str
    remote_compare_updated: str
    remote_compare_unchanged: str
    remote_confirm_install: str
    remote_confirm_install_detail: str
    remote_temp_dir: str
    remote_cleanup_complete: str
    remote_no_updates: str
    remote_user_cancelled: str
    remote_git_not_found: str
    remote_config_not_found: str
    remote_config_error: str
    remote_source_filter_selected: str
    remote_source_filter_invalid: str
    remote_source_update_failed: str
    remote_source_stale_cache: str


# 英文消息
MESSAGES_EN = Messages(
    arg_help_description="Install all skills from this repo to Codex/Claude Code user-level skills directories (copy-based, with MD5 versioning).",
    arg_help_dry_run="Print actions without writing anything.",
    arg_help_codex="Install to Codex only (default: both Codex and Claude Code).",
    arg_help_claude="Install to Claude Code only (default: both Codex and Claude Code).",
    arg_help_force="Force re-install all skills, ignoring MD5 check.",
    arg_help_skill="Install/update only the named skill. Can be repeated or comma-separated.",
    arg_help_remote="Enable remote installation mode (download skills from GitHub).",
    arg_help_check="Check mode (interactive confirmation before installing).",
    arg_help_auto="Auto mode (force install without confirmation).",
    arg_help_source_filter="Filter remote sources by ID (e.g., --general, --research).",
    error_no_skills_found="No installable skills found (scanned root: {root})",
    error_skill_filter_missing="Requested skill(s) not found: {skills}",
    error_skill_filter_not_installable="Requested skill(s) are not installable normal skills: {skills}",
    error_skill_name_collision="Detected skill directory name conflicts (basename duplicated), cannot install safely:",
    error_source_root_not_found="Failed to auto-detect skills source root. Run this script inside a project that contains ./pipelines/skills or ./skills (or the skills root itself), or pass --source explicitly.",
    installing_to_target="Installing to {TARGET}: {root}",
    removed_legacy_symlink="removed legacy symlink: {path}",
    removed_legacy_skill="removed legacy skill: {path}",
    skip_legacy_path="skip legacy path (not a symlink): {path}",
    removed_existing="removed: {dest}",
    installed="installed: {dest}",
    dry_run_prefix="[dry-run] ",
    # 表格相关
    table_header_skill="Skill Name",
    table_header_status="Status",
    table_header_reason="Reason",
    table_status_installed="✅ Installed",
    table_status_skipped="⏭️  Skipped",
    table_reason_no_change="No version change",
    table_reason_updated="Version updated (MD5: {md5})",
    table_separator="├─",
    # 安装报告消息（固定格式）
    report_section_process="\n【Installation Process】",
    report_section_summary="\n【Installation Summary】",
    report_section_ignored="Ignored Directories (test/ and tests/)",
    report_no_actions="No actions taken (all skills up-to-date)",
    report_statistics="📊 Statistics: {installed} installed, {skipped} skipped",
    # 安装摘要消息（兼容保留）
    summary_header="\n📊 Installation Summary - {TARGET}",
    summary_installed="\n✅ Installed/Updated ({count} skills):",
    summary_skipped="\n⏭️  Skipped ({count} skills):",
    summary_reason="     Reason: {reason}",
    summary_total_header="\n🎯 Overall Installation Summary",
    summary_total_counts="\nTotal counts:",
    summary_installed_count="  • Installed/Updated: {count} skills",
    summary_skipped_count="  • Skipped: {count} skills",
    summary_new_install="  New install: {skills}",
    summary_unchanged="  Unchanged: {skills}",
    summary_manifest_saved="📝 Installation manifest saved: {path}",
    manifest_preview="[dry-run] manifest preview:",
    # 远程安装消息
    remote_check_intro="\n🌐 Remote Check Mode: Download and compare remote skills before installation.",
    remote_auto_intro="\n🌐 Remote Auto Mode: Automatically download and install remote skills.",
    remote_source_prompt="Do you want to install skills from '{name}'? ({description}) [y/N]: ",
    remote_source_prompt_recommended="Do you want to install skills from '{name}'? ({description}) [Recommended] [Y/n]: ",
    remote_download_progress="Downloading {name} from {url}...",
    remote_download_complete="Download complete: {name}",
    remote_download_failed="Download failed: {name} - {error}",
    remote_skills_path_missing="Download complete but skills_path not found: {name} - {path}",
    remote_compare_header="\n【Remote Skills Comparison Report】",
    remote_compare_new="🟢 New Skills ({count})",
    remote_compare_updated="🟡 Updatable Skills ({count})",
    remote_compare_unchanged="⚪ Latest Skills ({count})",
    remote_confirm_install="Confirm to install/update these skills? [y/N]: ",
    remote_confirm_install_detail="  New: {new_count}, Updated: {updated_count}, Unchanged: {unchanged_count}",
    remote_temp_dir="Temporary directory: {path}",
    remote_cleanup_complete="Temporary directory cleaned up.",
    remote_no_updates="No updates available.",
    remote_user_cancelled="User cancelled.",
    remote_git_not_found="Error: Git command not found. Please install Git first.",
    remote_config_not_found="Error: Config file not found: {path}",
    remote_config_error="Error: Failed to load config file: {error}",
    remote_source_filter_selected="Selected sources: {sources}",
    remote_source_filter_invalid="Warning: Invalid source ID(s) ignored: {invalid_ids}",
    remote_source_update_failed="Remote source update failed: {sources}",
    remote_source_stale_cache="Remote source freshness was not verified; used existing cache: {sources}",
)

# 中文消息
MESSAGES_ZH = Messages(
    arg_help_description="将本仓库的所有 skills 安装到 Codex/Claude Code 用户级 skills 目录（基于复制，使用 MD5 版本控制）。",
    arg_help_dry_run="打印操作但不写入任何内容。",
    arg_help_codex="仅安装到 Codex（默认：同时安装到 Codex 和 Claude Code）。",
    arg_help_claude="仅安装到 Claude Code（默认：同时安装到 Codex 和 Claude Code）。",
    arg_help_force="强制重新安装所有 skills，忽略 MD5 检查。",
    arg_help_skill="仅安装/更新指定 skill。可重复传入，也可用逗号分隔。",
    arg_help_remote="启用远程安装模式（从 GitHub 下载技能）。",
    arg_help_check="检查模式（安装前交互式确认）。",
    arg_help_auto="自动模式（强制安装，无需确认）。",
    arg_help_source_filter="按 ID 过滤远程源（如 --general、--research）。",
    error_no_skills_found="未发现可安装的 skills（扫描根目录：{root}）",
    error_skill_filter_missing="未找到指定 skill：{skills}",
    error_skill_filter_not_installable="指定 skill 不是可安装的普通技能：{skills}",
    error_skill_name_collision="检测到 skill 目录名冲突（basename 重复），无法安全安装：",
    error_source_root_not_found="未能自动识别 skills 源目录：请在包含 ./pipelines/skills 或 ./skills（或 skills 根目录本身）的项目目录中运行，或使用 --source 显式指定。",
    installing_to_target="正在安装到 {TARGET}: {root}",
    removed_legacy_symlink="已移除旧软链接: {path}",
    removed_legacy_skill="已移除 legacy 技能: {path}",
    skip_legacy_path="跳过旧路径（非软链接）: {path}",
    removed_existing="已删除: {dest}",
    installed="已安装: {dest}",
    dry_run_prefix="[dry-run] ",
    # 表格相关
    table_header_skill="Skill 名称",
    table_header_status="状态",
    table_header_reason="原因",
    table_status_installed="✅ 已安装",
    table_status_skipped="⏭️  跳过",
    table_reason_no_change="版本未变化",
    table_reason_updated="版本已更新 (MD5: {md5})",
    table_separator="├─",
    # 安装报告消息（固定格式）
    report_section_process="\n【安装过程】",
    report_section_summary="\n【安装摘要】",
    report_section_ignored="已忽略的目录 (test/ 和 tests/)",
    report_no_actions="无需操作（所有 skills 均为最新版本）",
    report_statistics="📊 统计：已安装 {installed} 个，跳过 {skipped} 个",
    # 安装摘要消息（兼容保留）
    summary_header="\n📊 安装摘要 - {TARGET}",
    summary_installed="\n✅ 已安装/更新 ({count} 个):",
    summary_skipped="\n⏭️  跳过 ({count} 个):",
    summary_reason="     原因: {reason}",
    summary_total_header="\n🎯 总体安装摘要",
    summary_total_counts="\n总计数:",
    summary_installed_count="  • 已安装/更新: {count} 个",
    summary_skipped_count="  • 跳过: {count} 个",
    summary_new_install="  新安装: {skills}",
    summary_unchanged="  未变化: {skills}",
    summary_manifest_saved="📝 安装清单已保存: {path}",
    manifest_preview="[dry-run] manifest preview:",
    # 远程安装消息
    remote_check_intro="\n🌐 远程检查模式：下载并对比远程技能后再安装。",
    remote_auto_intro="\n🌐 远程自动模式：自动下载并安装远程技能。",
    remote_source_prompt="是否要安装来自 '{name}' 的技能？({description}) [y/N]: ",
    remote_source_prompt_recommended="是否要安装来自 '{name}' 的技能？({description}) [推荐] [Y/n]: ",
    remote_download_progress="正在从 {url} 下载 {name}...",
    remote_download_complete="下载完成: {name}",
    remote_download_failed="下载失败: {name} - {error}",
    remote_skills_path_missing="下载完成但未找到 skills_path: {name} - {path}",
    remote_compare_header="\n【远程技能对比报告】",
    remote_compare_new="🟢 新增技能 ({count}个)",
    remote_compare_updated="🟡 可更新技能 ({count}个)",
    remote_compare_unchanged="⚪ 最新技能 ({count}个)",
    remote_confirm_install="确认安装/更新这些技能？ [y/N]: ",
    remote_confirm_install_detail="  新增: {new_count}个, 更新: {updated_count}个, 最新: {unchanged_count}个",
    remote_temp_dir="临时目录: {path}",
    remote_cleanup_complete="临时目录已清理。",
    remote_no_updates="没有可用的更新。",
    remote_user_cancelled="用户取消。",
    remote_git_not_found="错误: 未找到 Git 命令。请先安装 Git。",
    remote_config_not_found="错误: 配置文件不存在: {path}",
    remote_config_error="错误: 加载配置文件失败: {error}",
    remote_source_filter_selected="已选择源: {sources}",
    remote_source_filter_invalid="警告: 无效的源 ID 已忽略: {invalid_ids}",
    remote_source_update_failed="远程源更新失败: {sources}",
    remote_source_stale_cache="远程源未确认最新，已使用旧缓存: {sources}",
)


def detect_system_language() -> str:
    """检测系统语言设置。

    优先级：
    1. LC_ALL 环境变量
    2. LANG 环境变量
    3. locale.getdefaultlocale() 结果
    4. 默认英语

    Returns:
        语言代码（'zh' 或 'en'）
    """
    # 尝试从环境变量获取
    for var in ["LC_ALL", "LANG"]:
        lang = os.environ.get(var, "")
        if lang:
            # 提取语言代码（如 'zh_CN.UTF-8' -> 'zh'）
            code = lang.split("_")[0].split(".")[0].lower()
            if code in SUPPORTED_LANGUAGES:
                return code
            # 处理 'zh' 的变体
            if code.startswith("zh"):
                return "zh"

    # 尝试从 locale 获取
    try:
        default_locale = locale.getdefaultlocale()
        if default_locale and default_locale[0]:
            lang_code = default_locale[0].split("_")[0].lower()
            if lang_code in SUPPORTED_LANGUAGES:
                return lang_code
            if lang_code.startswith("zh"):
                return "zh"
    except (ValueError, AttributeError):
        pass

    # 默认返回英语
    return "en"


class Translator:
    """翻译器，提供统一的本地化消息访问接口。"""

    def __init__(self, lang_code: str | None = None) -> None:
        """初始化翻译器。

        Args:
            lang_code: 语言代码，如果为 None 则自动检测
        """
        if lang_code is None:
            lang_code = detect_system_language()

        # 确保语言代码受支持
        if lang_code not in SUPPORTED_LANGUAGES:
            lang_code = "en"

        self._lang_code = lang_code
        self._messages = MESSAGES_ZH if lang_code == "zh" else MESSAGES_EN

    @property
    def lang_code(self) -> str:
        """返回当前语言代码。"""
        return self._lang_code

    def get(self, attr: str, *args, **kwargs) -> str:
        """获取本地化消息。

        Args:
            attr: Messages 数据类的属性名
            *args: format() 的位置参数
            **kwargs: format() 的关键字参数

        Returns:
            格式化后的本地化消息
        """
        template = getattr(self._messages, attr)
        if args or kwargs:
            return template.format(*args, **kwargs)
        return template

    def __getattr__(self, name: str) -> Callable[..., str]:
        """提供统一的消息访问方法。

        所有消息都作为可调用对象返回，无论是否需要参数。
        不带参数调用: t.message()
        带参数调用: t.message(key=value)

        例如：
            t.arg_help_description()  # 返回字符串
            t.summary_header(TARGET='TEST')  # 返回格式化字符串
        """
        # 首先尝试从 _messages 获取原始值
        if hasattr(self._messages, name):
            value = getattr(self._messages, name)
            # 返回一个可调用对象，无论是否包含占位符
            return lambda *args, **kwargs: value.format(*args, **kwargs) if (args or kwargs) else value
        # 如果找不到，抛出 AttributeError
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


# 全局翻译器实例（延迟初始化）
_global_translator: Translator | None = None


def get_translator() -> Translator:
    """获取全局翻译器实例（单例模式）。"""
    global _global_translator
    if _global_translator is None:
        _global_translator = Translator()
    return _global_translator


def set_language(lang_code: str) -> None:
    """设置全局语言（用于测试）。"""
    global _global_translator
    _global_translator = Translator(lang_code)
