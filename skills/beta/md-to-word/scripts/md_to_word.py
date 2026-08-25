#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any


FALLBACK_TEMPLATES = {
    "default": Path("assets/reference-default.docx"),
    "cn-modern": Path("assets/reference-cn-modern.docx"),
    "compact": Path("assets/reference-compact.docx"),
}


@dataclass
class Options:
    pandoc: str
    template: str | None
    reference_doc: Path | None
    output_dir: Path | None
    output: Path | None
    output_suffix: str
    overwrite: bool
    dry_run: bool
    toc: bool
    toc_depth: int
    allow_any_extension: bool
    list_templates: bool
    config_path: Path | None
    extract_media: str | None
    fix_images: bool
    keep_temp_files: bool
    clean: bool


@dataclass(frozen=True)
class EffectiveConfig:
    max_inputs: int = 200
    allowed_input_extensions: frozenset[str] = frozenset({".md", ".markdown"})
    pandoc_from: str = "markdown+smart"
    pandoc_to: str = "docx"
    pandoc_wrap: str = "preserve"
    pandoc_standalone: bool = True
    default_template: str = "default"
    templates: dict[str, Path] = field(default_factory=lambda: dict(FALLBACK_TEMPLATES))


def _die(message: str, code: int = 2) -> "NoReturn":  # type: ignore[name-defined]
    raise SystemExit(message)


def _check_pillow_available() -> bool:
    """检查 Pillow 是否可用于图片处理"""
    try:
        import PIL  # type: ignore
        return True
    except Exception:
        return False


def _apply_exif_orientation(img: "Image.Image") -> "Image.Image":
    """
    应用 EXIF 方向信息到图片。

    EXIF Orientation 标准值：
    1: 无旋转
    2: 水平翻转
    3: 旋转180°
    4: 垂直翻转
    5: 逆时针90° + 水平翻转
    6: 顺时针90°
    7: 顺时针90° + 水平翻转
    8: 逆时针90°
    """
    try:
        from PIL import ImageOps
        # ImageOps.exif_transpose() 会自动读取并应用 EXIF 方向
        return ImageOps.exif_transpose(img)
    except Exception:
        # Pillow 版本过低或没有 EXIF 信息，返回原图
        return img


def _allocate_bensz_run_dir(base: Path, skill_name: str) -> Path:
    root = base / ".bensz-api" / "skills" / skill_name
    stamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    candidate = root / stamp
    if not candidate.exists():
        return candidate
    for idx in range(2, 100):
        candidate = root / f"{stamp}-{idx:02d}"
        if not candidate.exists():
            return candidate
    _die(f"无法分配唯一中间工作目录：{root / stamp}")


def _prepare_md_with_rgb_images(input_md: Path, keep_temp: bool = False) -> tuple[Path | None, list[str]]:
    """
    在 .bensz-api/skills/md-to-word/<timestamp>/ 中准备 MD 副本，并将所有图片转换为 RGB 模式。

    工作流：
    1. 创建 .bensz-api/skills/md-to-word/<timestamp>/ 隐藏目录
    2. 创建 output/images-rgb/ 存放转换后的图片
    3. 创建 MD 副本，更新所有图片链接指向 RGB 版本
    4. 应用 EXIF 方向信息
    5. 转换非 RGB 模式的图片（RGBA/P/L 等）

    返回: (MD 副本路径, 转换的图片列表)
    如果没有图片或无需转换，返回 (None, [])
    """
    try:
        from PIL import Image
    except Exception:
        # Pillow 不可用，跳过图片处理
        return None, []

    md_content = input_md.read_text(encoding="utf-8")
    md_dir = input_md.parent.resolve()

    # 查找所有图片引用：![alt](path)
    # 支持多种格式：png, jpg, jpeg, gif, bmp, webp
    img_pattern = re.compile(
        r'!\[([^\]]*)\]\(([^)]+\.(png|PNG|jpe?g|JPE?G|gif|GIF|bmp|BMP|webp|WEBP))\)'
    )

    # 收集需要处理的图片
    images_to_process = []  # (相对路径, 完整路径, 扩展名)
    for match in img_pattern.finditer(md_content):
        img_rel_path = match.group(2)
        img_ext = match.group(3).lower()
        img_full_path = (md_dir / img_rel_path).resolve()

        if not img_full_path.exists() or not img_full_path.is_file():
            continue

        images_to_process.append((img_rel_path, img_full_path, img_ext))

    if not images_to_process:
        # 没有图片，直接返回
        return None, []

    # 确认有图片后，创建统一中间工作目录。
    work_dir = _allocate_bensz_run_dir(md_dir, "md-to-word")
    (work_dir / "input").mkdir(parents=True, exist_ok=True)
    (work_dir / "log").mkdir(parents=True, exist_ok=True)

    # 创建 RGB 图片目录
    rgb_images_dir = work_dir / "output" / "images-rgb"
    rgb_images_dir.mkdir(parents=True, exist_ok=True)

    # 处理图片：转换为 RGB 模式
    fixed_images = []
    replacement_map = {}  # 原始相对路径 -> RGB 图片相对路径

    for rel_path, full_path, ext in images_to_process:
        try:
            with Image.open(full_path) as img:
                # 首先应用 EXIF 方向信息
                img = _apply_exif_orientation(img)

                # 检查是否需要转换
                needs_conversion = img.mode not in ("RGB", "L")  # L 是灰度，通常无需转换

                if needs_conversion:
                    # 转换为 RGB
                    if img.mode == "RGBA":
                        # RGBA -> RGB（白色背景）
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])  # alpha 通道作为 mask
                        img = background
                    else:
                        # 其他模式（P/PA/LA等）直接转换
                        img = img.convert("RGB")

                # 计算输出路径（保持原文件名）
                rgb_filename = full_path.name
                rgb_path = rgb_images_dir / rgb_filename
                # 根据扩展名确定保存格式
                save_format = "JPEG" if ext.lower() in ("jpg", "jpeg") else ext.upper()
                img.save(rgb_path, format=save_format)

                # 更新替换映射（相对路径）
                # 在 MD 副本中，图片链接指向同一 run 目录下的 output/images-rgb/
                replacement_map[rel_path] = f"output/images-rgb/{rgb_filename}"

                if needs_conversion:
                    fixed_images.append(str(full_path))

        except Exception as e:
            # 转换失败，记录但不中断
            print(f"⚠️  警告：无法处理图片 {full_path.name}: {e}")
            continue

    if not replacement_map:
        # 没有成功处理的图片，清理空的工作目录
        rgb_images_dir.rmdir()
        (work_dir / "output").rmdir()
        (work_dir / "input").rmdir()
        (work_dir / "log").rmdir()
        work_dir.rmdir()
        return None, []

    # 创建 MD 副本，更新图片链接
    new_content = md_content
    for original, replacement in replacement_map.items():
        # 转义特殊字符，精确匹配
        original_escaped = re.escape(original)
        # 使用反向引用保留 alt 文本
        new_content = re.sub(
            rf'!\[([^\]]*)\]\({original_escaped}\)',
            rf'![\1]({replacement})',
            new_content
        )

    # 保存 MD 副本
    md_copy = work_dir / input_md.name
    md_copy.write_text(new_content, encoding="utf-8")

    return md_copy, fixed_images


def _resolve_reference_doc(opts: Options, skill_root: Path, cfg: EffectiveConfig) -> Path | None:
    if opts.reference_doc is not None:
        ref = opts.reference_doc.expanduser().resolve()
        if not ref.exists() or not ref.is_file():
            _die(f"reference.docx 不存在或不是文件：{ref}")
        return ref

    template_name = opts.template or cfg.default_template
    if template_name not in cfg.templates:
        _die(
            "未知模板："
            f"{template_name}；可选：{', '.join(sorted(cfg.templates.keys()))}"
        )

    ref = (skill_root / cfg.templates[template_name]).resolve()
    if not ref.exists():
        _die(f"内置模板文件缺失：{ref}")
    return ref


def _compute_output_path(input_md: Path, output_dir: Path | None, output_suffix: str) -> Path:
    out_dir = output_dir if output_dir is not None else input_md.parent
    return (out_dir / (input_md.stem + output_suffix + ".docx")).resolve()


def _ensure_no_overwrite(output_path: Path, overwrite: bool) -> None:
    if output_path.exists() and not overwrite:
        _die(
            "输出文件已存在，默认不覆盖。"
            f"如需覆盖请显式传 --overwrite：{output_path}"
        )


def _check_pandoc_available(pandoc: str) -> None:
    try:
        subprocess.run(
            [pandoc, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except FileNotFoundError:
        _die(
            "未找到 pandoc。请先安装 Pandoc，并确保 `pandoc` 在 PATH 中。"
        )
    except subprocess.CalledProcessError:
        _die("pandoc 可执行但运行失败：请检查 pandoc 安装状态。")


def _resource_path_for(input_md: Path) -> str:
    """
    构建资源路径列表，确保 Pandoc 能找到相对路径的图片

    优先级：
    1. Markdown 文件所在目录
    2. Markdown 文件的父目录（支持 raw/ 子目录）
    3. 当前工作目录
    """
    md_dir = input_md.parent.resolve()
    md_parent = md_dir.parent.resolve()
    cwd = Path.cwd().resolve()

    # 构建资源路径列表
    paths = [str(md_dir)]

    # 如果父目录存在且不同于 md_dir，也加入
    if md_parent != md_dir:
        paths.append(str(md_parent))

    # 添加当前工作目录
    if cwd != md_dir and cwd != md_parent:
        paths.append(str(cwd))

    # Pandoc 使用系统的路径分隔符（POSIX ':'，Windows ';'）
    return os.pathsep.join(paths)


def convert_one(
    input_md: Path,
    output_docx: Path,
    ref_doc: Path | None,
    opts: Options,
    cfg: EffectiveConfig,
) -> list[str]:
    """
    构建单个文件的转换命令
    """
    cmd: list[str] = [
        opts.pandoc,
        "--from",
        cfg.pandoc_from,
        "--to",
        cfg.pandoc_to,
        "--wrap",
        cfg.pandoc_wrap,
        "--markdown-headings=atx",  # 使用 ATX 标题样式，提高兼容性
    ]
    if cfg.pandoc_standalone:
        cmd.append("--standalone")

    # 关键：设置资源路径，确保能找到相对路径的图片
    cmd.extend([
        "--resource-path",
        _resource_path_for(input_md),
    ])

    # 输出文件
    cmd.extend([
        "--output",
        str(output_docx),
    ])

    # 输入文件
    cmd.append(str(input_md))

    # 参考文档
    if ref_doc is not None:
        cmd.extend(["--reference-doc", str(ref_doc)])

    # 目录
    if opts.toc:
        cmd.append("--toc")
        cmd.extend(["--toc-depth", str(opts.toc_depth)])

    return cmd


def _parse_args(argv: list[str]) -> tuple[Options, list[Path]]:
    parser = argparse.ArgumentParser(
        description="Convert Markdown file(s) to Word (.docx) via Pandoc, with safe defaults.",
    )
    parser.add_argument("md_files", nargs="*", help="Markdown 文件路径（一个或多个）")
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="列出内置模板并退出",
    )
    parser.add_argument(
        "--pandoc",
        default="pandoc",
        help="Pandoc 可执行文件名或路径（默认：pandoc）",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="可选：读取自定义 config.yaml（用于 max_inputs / allowed extensions / pandoc 默认参数）",
    )
    parser.add_argument(
        "--template",
        default=None,
        help="内置模板名（默认读取 config.yaml 的 pandoc.default_template；缺失则为 default）",
    )
    parser.add_argument(
        "--reference-doc",
        dest="reference_doc",
        default=None,
        help="自定义 reference.docx 路径（优先级高于 --template）",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="输出目录（默认：与输入文件同目录）",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="显式指定输出 .docx 路径（仅允许单输入；与 --output-dir/--output-suffix 互斥）",
    )
    parser.add_argument(
        "--output-suffix",
        default="",
        help="输出文件名后缀（默认空）。如后缀以 '-' 开头，请用等号形式：--output-suffix=-cn-modern",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="允许覆盖已存在的输出 docx（默认禁用）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将要执行的 pandoc 命令，不真正转换",
    )
    parser.add_argument(
        "--allow-any-extension",
        action="store_true",
        help="允许输入文件不是 .md/.markdown（默认只接受 Markdown 扩展名）",
    )
    parser.add_argument("--toc", action="store_true", help="在 Word 中生成目录（TOC）")
    parser.add_argument("--toc-depth", type=int, default=3, help="TOC 深度（默认：3）")
    parser.add_argument(
        "--fix-images",
        action="store_true",
        help="自动转换 RGBA PNG 图片为 RGB 模式，解决 Word 兼容性问题（需要 Pillow）",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="转换完成后清理 .bensz-api/skills/md-to-word/<timestamp>/ 工作目录（默认保留以便增量转换）",
    )
    parser.add_argument(
        "--keep-temp-files",
        action="store_true",
        help="[调试用] 保留临时文件（已废弃，使用 --clean 控制清理）",
    )

    args = parser.parse_args(argv)

    if args.list_templates:
        opts = Options(
            pandoc=args.pandoc,
            template=args.template,
            reference_doc=None,
            output_dir=None,
            output=None,
            output_suffix="",
            overwrite=False,
            dry_run=True,
            toc=False,
            toc_depth=args.toc_depth,
            allow_any_extension=True,
            list_templates=True,
            config_path=None,
            extract_media=None,
            fix_images=False,
            keep_temp_files=False,
            clean=False,
        )
        return opts, []

    if any(sep and sep in args.output_suffix for sep in [os.sep, os.altsep]):
        _die("--output-suffix 只能是文件名后缀，不能包含路径分隔符。")

    md_files = [Path(p) for p in args.md_files]
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    output = Path(args.output).expanduser().resolve() if args.output else None
    reference_doc = Path(args.reference_doc).expanduser() if args.reference_doc else None

    if args.toc_depth < 1 or args.toc_depth > 6:
        _die("--toc-depth 必须在 1~6 之间。")

    if output is not None:
        if output_dir is not None or args.output_suffix:
            _die("--output 与 --output-dir/--output-suffix 互斥。")
        if output.suffix.lower() != ".docx":
            _die("--output 必须以 .docx 结尾。")

    opts = Options(
        pandoc=args.pandoc,
        template=args.template,
        reference_doc=reference_doc,
        output_dir=output_dir,
        output=output,
        output_suffix=args.output_suffix,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        toc=args.toc,
        toc_depth=args.toc_depth,
        allow_any_extension=args.allow_any_extension,
        list_templates=False,
        config_path=Path(args.config).expanduser().resolve() if args.config else None,
        extract_media=None,
        fix_images=args.fix_images,
        keep_temp_files=args.keep_temp_files,
        clean=args.clean,
    )
    return opts, md_files


def _load_effective_config(default_config: Path, override: Path | None) -> EffectiveConfig:
    config_path = override if override is not None else default_config
    if not config_path.exists():
        return EffectiveConfig()

    try:
        import yaml  # type: ignore
    except Exception:
        if override is not None:
            _die("缺少 PyYAML（yaml）依赖，无法读取 --config。请安装 PyYAML 或不传 --config。")
        return EffectiveConfig()

    raw: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return EffectiveConfig()

    limits = raw.get("limits") if isinstance(raw.get("limits"), dict) else {}
    io = raw.get("io") if isinstance(raw.get("io"), dict) else {}
    pandoc = raw.get("pandoc") if isinstance(raw.get("pandoc"), dict) else {}
    templates_raw = raw.get("templates") if isinstance(raw.get("templates"), dict) else {}

    max_inputs = limits.get("max_inputs", 200)
    if not isinstance(max_inputs, int) or max_inputs < 1:
        max_inputs = 200

    exts = io.get("allowed_input_extensions", [".md", ".markdown"])
    if isinstance(exts, list):
        allowed = {str(x).lower() for x in exts if str(x).startswith(".")}
    else:
        allowed = {".md", ".markdown"}
    if not allowed:
        allowed = {".md", ".markdown"}

    pandoc_from = pandoc.get("from", "markdown+smart")
    pandoc_to = pandoc.get("to", "docx")
    pandoc_wrap = pandoc.get("wrap", "preserve")
    pandoc_standalone = pandoc.get("standalone", True)
    default_template = pandoc.get("default_template", "default")

    if not isinstance(pandoc_from, str) or not pandoc_from:
        pandoc_from = "markdown+smart"
    if not isinstance(pandoc_to, str) or not pandoc_to:
        pandoc_to = "docx"
    if not isinstance(pandoc_wrap, str) or not pandoc_wrap:
        pandoc_wrap = "preserve"
    if not isinstance(pandoc_standalone, bool):
        pandoc_standalone = True
    if not isinstance(default_template, str) or not default_template:
        default_template = "default"

    templates: dict[str, Path] = dict(FALLBACK_TEMPLATES)
    for k, v in templates_raw.items():
        if not isinstance(k, str) or not k:
            continue
        if not isinstance(v, str) or not v:
            continue
        templates[k] = Path(v)

    return EffectiveConfig(
        max_inputs=max_inputs,
        allowed_input_extensions=frozenset(allowed),
        pandoc_from=pandoc_from,
        pandoc_to=pandoc_to,
        pandoc_wrap=pandoc_wrap,
        pandoc_standalone=pandoc_standalone,
        default_template=default_template,
        templates=templates,
    )


def main(argv: list[str]) -> int:
    opts, md_files = _parse_args(argv)

    skill_root = Path(__file__).resolve().parents[1]
    cfg = _load_effective_config(skill_root / "config.yaml", opts.config_path)

    if opts.list_templates:
        for name in sorted(cfg.templates.keys()):
            print(f"{name}\t{(skill_root / cfg.templates[name]).as_posix()}")
        return 0

    if not md_files:
        _die("缺少输入文件。请提供一个或多个 Markdown 文件路径。")

    if len(md_files) > cfg.max_inputs:
        _die(f"输入文件过多（>{cfg.max_inputs}）。请分批处理，或在 config.yaml 调整 limits。")

    # 图片修复功能需要 Pillow
    if opts.fix_images and not _check_pillow_available():
        print("⚠️  警告：--fix-images 需要 Pillow (PIL)，但未安装。将跳过图片修复。")
        print("   安装方法：pip install Pillow")
        opts.fix_images = False

    for p in md_files:
        if not p.exists() or not p.is_file():
            _die(f"Markdown 文件不存在或不是文件：{p}")
        if not opts.allow_any_extension and p.suffix.lower() not in cfg.allowed_input_extensions:
            _die(
                "默认只接受 "
                f"{', '.join(sorted(cfg.allowed_input_extensions))}：{p}；"
                "如确需转换，请显式传 --allow-any-extension"
            )

    ref_doc = _resolve_reference_doc(opts, skill_root, cfg)
    if not opts.dry_run:
        _check_pandoc_available(opts.pandoc)
        if opts.output is not None:
            opts.output.parent.mkdir(parents=True, exist_ok=True)
        elif opts.output_dir is not None:
            opts.output_dir.mkdir(parents=True, exist_ok=True)

    # 跟踪工作目录（用于 --clean 清理）
    work_dirs_to_cleanup: set[Path] = set()

    try:
        if opts.output is not None:
            if len(md_files) != 1:
                _die("--output 仅允许在单输入文件时使用。")
            input_md = md_files[0].expanduser().resolve()
            out_docx = opts.output
            _ensure_no_overwrite(out_docx, opts.overwrite)

            # 图片处理（使用 .bensz-api/skills/md-to-word/<timestamp>/ 工作目录）
            actual_input_md = input_md
            if opts.fix_images:
                md_copy, fixed_images = _prepare_md_with_rgb_images(input_md, not opts.clean)
                if md_copy is not None:
                    image_count = len(fixed_images) if fixed_images else 0
                    rgb_dir = md_copy.parent / "output" / "images-rgb"
                    total_count = len(list(rgb_dir.glob("*"))) if rgb_dir.exists() else 0
                    if image_count > 0:
                        print(f"🔧 已转换 {image_count}/{total_count} 张图片为 RGB 模式")
                    actual_input_md = md_copy
                    if opts.clean:
                        work_dirs_to_cleanup.add(md_copy.parent)

            cmd = convert_one(actual_input_md, out_docx, ref_doc, opts, cfg)
            if opts.dry_run:
                print(shlex.join(cmd))
                return 0
            subprocess.run(cmd, check=True)
            return 0

        for input_md in md_files:
            input_md_abs = input_md.expanduser().resolve()
            out_docx = _compute_output_path(input_md_abs, opts.output_dir, opts.output_suffix)
            _ensure_no_overwrite(out_docx, opts.overwrite)

            # 图片处理（使用 .bensz-api/skills/md-to-word/<timestamp>/ 工作目录）
            actual_input_md = input_md_abs
            if opts.fix_images:
                md_copy, fixed_images = _prepare_md_with_rgb_images(input_md_abs, not opts.clean)
                if md_copy is not None:
                    image_count = len(fixed_images) if fixed_images else 0
                    rgb_dir = md_copy.parent / "output" / "images-rgb"
                    total_count = len(list(rgb_dir.glob("*"))) if rgb_dir.exists() else 0
                    if image_count > 0:
                        print(f"🔧 已转换 {image_count}/{total_count} 张图片为 RGB 模式")
                    actual_input_md = md_copy
                    if opts.clean:
                        work_dirs_to_cleanup.add(md_copy.parent)

            cmd = convert_one(actual_input_md, out_docx, ref_doc, opts, cfg)
            if opts.dry_run:
                print(shlex.join(cmd))
                continue

            subprocess.run(cmd, check=True)

        return 0

    finally:
        # 清理工作目录
        if opts.clean:
            for work_dir in work_dirs_to_cleanup:
                try:
                    if work_dir.is_dir():
                        # 递归删除
                        import shutil
                        shutil.rmtree(work_dir)
                except Exception:
                    # 清理失败不中断主流程
                    pass


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
