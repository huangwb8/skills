#!/usr/bin/env python3
"""
输入验证与规范化脚本
"""
import sys
import re
from pathlib import Path


def normalize_doi(doi: str) -> str:
    """规范化 DOI 格式"""
    doi = doi.strip()

    # 移除常见前缀
    if doi.lower().startswith("doi:"):
        doi = doi[4:].strip()

    # 移除 URL 前缀
    if "doi.org/" in doi:
        doi = doi.split("doi.org/")[-1].strip()

    # 确保以 10. 开头（DOI 标准格式）
    if not doi.startswith("10."):
        # 尝试补全
        if "." in doi:
            doi = f"10.{doi}"

    return doi


def validate_output_path(path: str, default_filename: str = "paper.pdf", config: dict = None) -> Path:
    """验证输出路径，确保路径在当前工作目录范围内（防止路径遍历攻击）"""
    path = Path(path).expanduser().resolve()
    cwd = Path.cwd().resolve()

    # 安全检查：确保路径在当前工作目录或其子目录内（防止路径遍历）
    try:
        path.relative_to(cwd)
    except ValueError:
        raise ValueError(f"输出路径必须在当前工作目录范围内: {path}")

    if path.exists() and path.is_dir():
        # 目录：自动生成文件名
        return path / default_filename

    # 检查是否允许创建目录（从配置读取）
    output_config = config or {}
    create_dirs = output_config.get("create_missing_dirs", True)

    if path.parent.exists():
        # 完整路径：确保父目录可写
        return path

    if not create_dirs:
        raise ValueError(f"父目录不存在且 create_missing_dirs=false: {path.parent}")

    # 父目录不存在，尝试创建
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    except Exception as e:
        raise ValueError(f"无法创建输出目录: {e}")


def main():
    if len(sys.argv) < 3:
        print("用法: python validate_input.py <doi> <output_path>", file=sys.stderr)
        sys.exit(1)

    doi = normalize_doi(sys.argv[1])
    output_path = validate_output_path(sys.argv[2])

    # 输出格式化结果（供 AI 解析）
    print(f"DOI:{doi}")
    print(f"OUTPUT:{output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
