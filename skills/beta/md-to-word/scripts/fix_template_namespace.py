#!/usr/bin/env python3
"""
修复 Word 模板的命名空间问题

将非标准的 ns0: 命名空间前缀替换为标准的 w: 前缀
解决 Pandoc 使用 --reference-doc 时导致的 Word 警告问题
"""
import argparse
import zipfile
import sys
from pathlib import Path


def fix_template_namespace(input_docx: Path, output_docx: Path) -> tuple[bool, bool]:
    """
    修复模板文件的命名空间

    Args:
        input_docx: 输入模板路径
        output_docx: 输出模板路径

    Returns:
        (是否成功修复, 是否需要修复)
    """
    try:
        with zipfile.ZipFile(input_docx, 'r') as z_in:
            with zipfile.ZipFile(output_docx, 'w', zipfile.ZIP_DEFLATED) as z_out:
                fixed_count = 0
                needs_fix = False

                for item in z_in.infolist():
                    content = z_in.read(item.filename)

                    # 修复 styles.xml 的命名空间
                    if item.filename == 'word/styles.xml':
                        content_str = content.decode('utf-8')

                        # 检查是否需要修复
                        if 'ns0:' not in content_str:
                            print(f"✅ 模板已使用标准命名空间，无需修复")
                            # 仍然复制所有文件
                        else:
                            needs_fix = True
                            # 替换命名空间
                            original_ns0_count = content_str.count('ns0:')
                            content_str = content_str.replace('xmlns:ns0=', 'xmlns:w=')
                            content_str = content_str.replace('ns0:', 'w:')

                            # 验证修复
                            new_ns0_count = content_str.count('ns0:')
                            fixed_count = original_ns0_count - new_ns0_count
                            print(f"✅ 已修复 {fixed_count} 处命名空间引用")

                        content = content_str.encode('utf-8')

                    z_out.writestr(item, content)

        return True, needs_fix

    except Exception as e:
        print(f"❌ 修复失败: {e}", file=sys.stderr)
        return False, False


def verify_template(template_path: Path) -> bool:
    """
    验证模板是否使用标准命名空间

    Args:
        template_path: 模板路径

    Returns:
        是否通过验证
    """
    try:
        with zipfile.ZipFile(template_path, 'r') as z:
            # 检查 word/styles.xml 是否存在
            if 'word/styles.xml' not in z.namelist():
                # 尝试其他可能的路径
                styles_content = None
                for name in z.namelist():
                    if 'styles' in name.lower() and name.endswith('.xml'):
                        styles_content = z.read(name).decode('utf-8')
                        break

                if styles_content is None:
                    print(f"⚠️  未找到 styles.xml 文件，跳过验证")
                    return True
            else:
                styles_content = z.read('word/styles.xml').decode('utf-8')

            # 检查命名空间
            ns0_count = styles_content.count('ns0:')
            w_count = styles_content.count('w:')

            print(f"\n验证结果:")
            print(f"  ns0: 使用次数: {ns0_count}")
            print(f"  w: 使用次数: {w_count}")

            if ns0_count > 0:
                print(f"  ❌ 模板使用非标准命名空间")
                return False
            else:
                print(f"  ✅ 模板使用标准命名空间")
                return True

    except Exception as e:
        print(f"❌ 验证失败: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="修复 Word 模板的命名空间问题（解决 Word 警告）"
    )
    parser.add_argument(
        '--input',
        type=Path,
        required=True,
        help='输入模板文件路径'
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='输出模板文件路径'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='修复后验证输出文件'
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"❌ 输入文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"正在修复模板: {args.input}")
    print(f"输出到: {args.output}")

    success, needs_fix = fix_template_namespace(args.input, args.output)
    if success:
        print(f"✅ 处理完成: {args.output}")

        if args.verify:
            if verify_template(args.output):
                sys.exit(0)
            else:
                print(f"⚠️  修复后的模板未通过验证", file=sys.stderr)
                sys.exit(1)
        else:
            sys.exit(0)
    else:
        print(f"❌ 修复失败", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
