#!/usr/bin/env python3
"""
PDF 验证脚本
"""
import sys
from pathlib import Path
from typing import Tuple


def verify_pdf(path: Path, require_pypdf2: bool = False) -> Tuple[bool, str]:
    """验证 PDF 文件完整性"""
    if not path.exists():
        return False, "文件不存在"

    file_size = path.stat().st_size

    if file_size == 0:
        return False, "文件大小为 0"

    # 检查文件大小范围
    max_size = 100_000_000  # 100 MB
    min_size = 1024  # 1 KB

    if file_size > max_size:
        return False, f"文件过大: {file_size} bytes"

    if file_size < min_size:
        return False, f"文件过小: {file_size} bytes，可能是错误页面"

    # 检查 PDF 文件头
    try:
        with open(path, "rb") as f:
            header = f.read(5)
            if header != b"%PDF-":
                # 检查是否是 HTML 错误页面
                f.seek(0)
                content_start = f.read(100).decode("utf-8", errors="ignore")
                if "<html" in content_start.lower() or "<!doctype" in content_start.lower():
                    return False, "文件是 HTML 页面，非 PDF"
                return False, "无效的 PDF 文件头"
    except Exception as e:
        return False, f"读取文件头失败: {str(e)}"

    # 尝试用 PyPDF2 解析
    try:
        import PyPDF2
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            # 检查页数
            if len(reader.pages) == 0:
                return False, "PDF 无页面"
        return True, f"有效 PDF ({len(reader.pages)} 页)"
    except ImportError:
        if require_pypdf2:
            return False, "未安装 PyPDF2，无法深度验证"
        return True, "有效 PDF（未安装 PyPDF2，跳过深度验证）"
    except Exception as e:
        return False, f"PDF 解析失败: {str(e)}"


def main():
    if len(sys.argv) < 2:
        print("用法: python verify_pdf.py <pdf_path> [--require-pypdf2]", file=sys.stderr)
        sys.exit(1)

    pdf_path = Path(sys.argv[1]).expanduser().resolve()
    require_pypdf2 = "--require-pypdf2" in sys.argv

    is_valid, message = verify_pdf(pdf_path, require_pypdf2)

    if is_valid:
        print(f"VALID:{message}")
        return 0
    else:
        print(f"INVALID:{message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
