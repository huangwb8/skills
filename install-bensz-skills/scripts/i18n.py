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

    # 错误消息
    error_no_skills_found: str
    error_skill_name_collision: str

    # 安装过程消息
    installing_to_target: str
    removed_legacy_symlink: str
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


# 英文消息
MESSAGES_EN = Messages(
    arg_help_description="Install all skills from this repo to Codex/Claude Code user-level skills directories (copy-based, with MD5 versioning).",
    arg_help_dry_run="Print actions without writing anything.",
    arg_help_codex="Install to Codex only.",
    arg_help_claude="Install to Claude Code only.",
    arg_help_force="Force re-install all skills, ignoring MD5 check.",
    error_no_skills_found="No installable skills found (scanned root: {root})",
    error_skill_name_collision="Detected skill directory name conflicts (basename duplicated), cannot install safely:",
    installing_to_target="Installing to {TARGET}: {root}",
    removed_legacy_symlink="removed legacy symlink: {path}",
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
)

# 中文消息
MESSAGES_ZH = Messages(
    arg_help_description="将本仓库的所有 skills 安装到 Codex/Claude Code 用户级 skills 目录（基于复制，使用 MD5 版本控制）。",
    arg_help_dry_run="打印操作但不写入任何内容。",
    arg_help_codex="仅安装到 Codex。",
    arg_help_claude="仅安装到 Claude Code。",
    arg_help_force="强制重新安装所有 skills，忽略 MD5 检查。",
    error_no_skills_found="未发现可安装的 skills（扫描根目录：{root}）",
    error_skill_name_collision="检测到 skill 目录名冲突（basename 重复），无法安全安装：",
    installing_to_target="正在安装到 {TARGET}: {root}",
    removed_legacy_symlink="removed legacy symlink: {path}",
    skip_legacy_path="skip legacy path (not a symlink): {path}",
    removed_existing="removed: {dest}",
    installed="installed: {dest}",
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
