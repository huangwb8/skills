"""Output contracts shared by generation, iteration and local inspection."""
from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

FORMATS = {"jpeg": ".jpg", "png": ".png", "webp": ".webp", "svg": ".svg", "gif": ".gif"}
GENERATION_ONLY_FORMATS = {"svg", "gif"}
IMAGE_26_MODELS = {"gpt-image-2.6-flare", "gpt-image-2.6-sunburst"}


def resolve_output_format(requested: Optional[str], path: Optional[Path], default: str = "jpeg") -> str:
    suffix = path.suffix.lower() if path else ""
    inferred = {".jpg": "jpeg", ".jpeg": "jpeg", **{v: k for k, v in FORMATS.items()}}.get(suffix)
    value = str(requested or inferred or default).strip().lower()
    if value not in FORMATS:
        raise ValueError(f"不支持的 output_format：{value}")
    if value in GENERATION_ONLY_FORMATS and path is not None and inferred != value:
        raise ValueError(f"{value} 输出必须使用 {FORMATS[value]} 扩展名。")
    if inferred in GENERATION_ONLY_FORMATS and value != inferred:
        raise ValueError("输出格式与 SVG/GIF 文件扩展名不一致。")
    return value


def validate_image_options(
    *, model: str, provider: str, output_format: str,
    references: Optional[List[Path]] = None, markup: Optional[Path] = None,
    complexity: Optional[str] = None, frame_count: Optional[int] = None,
    frame_duration_ms: Optional[int] = None, output_compression: Optional[int] = None,
    postprocess_resize: bool = False, provider_size: Optional[str] = None,
) -> None:
    special = output_format in GENERATION_ONLY_FORMATS
    if special or complexity is not None or frame_count is not None or frame_duration_ms is not None:
        if provider != "gpt-image-2" or model not in IMAGE_26_MODELS:
            raise ValueError("SVG/GIF、complexity 和动画参数需要显式选择 GPT Image 2.6 Flare 或 Sunburst。")
    if complexity is not None and complexity not in {"low", "medium", "high"}:
        raise ValueError("complexity 必须为 low、medium 或 high。")
    if special:
        if references or markup:
            raise ValueError("SVG/GIF 仅支持文本生成，不能使用参考图或 markup 编辑。")
        if postprocess_resize:
            raise ValueError("SVG/GIF 不支持位图后处理缩放。")
        if output_compression is not None:
            raise ValueError("SVG/GIF 不支持 output_compression；请省略该参数。")
    if frame_count is not None or frame_duration_ms is not None:
        if output_format != "gif":
            raise ValueError("frame_count 和 frame_duration_ms 只能用于 GIF。")
    for name, value, low, high in [("frame_count", frame_count, 2, 64), ("frame_duration_ms", frame_duration_ms, 20, 2000)]:
        if value is not None and (type(value) is not int or not low <= value <= high):
            raise ValueError(f"{name} 必须为 {low}–{high} 范围的整数。")
    if output_format == "gif" and provider_size and provider_size != "auto":
        if not re.fullmatch(r"[1-9]\d*x[1-9]\d*", provider_size):
            raise ValueError("GIF size 必须为 auto 或 WIDTHxHEIGHT。")
        if any(int(v) % 16 for v in provider_size.split("x")):
            raise ValueError("GIF 每帧宽高必须为 16 的倍数。")
    if markup is not None:
        if provider != "gpt-image-2" or model not in IMAGE_26_MODELS | {"gpt-image-2.5-flare", "gpt-image-2.5-sunburst"}:
            raise ValueError("当前模型不支持 markup 编辑。")
        if len(references or []) != 1:
            raise ValueError("markup 编辑需要且仅接受一张原始参考图。")
    if output_format == "gif" or markup is not None:
        try:
            from PIL import Image  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("GIF 与 markup 需要 Pillow；请先在当前 Python 环境安装 Pillow。") from exc


def parse_static_svg(raw: bytes) -> ET.Element:
    if len(raw) > 48 * 1024 * 1024:
        raise ValueError("SVG 超过 48 MiB 限制。")
    if re.search(br"<!\s*(?:DOCTYPE|ENTITY)", raw, re.I):
        raise ValueError("SVG 不允许 DTD 或实体声明。")
    if re.search(br"<\?(?!xml(?:\s|\?>))", raw, re.I):
        raise ValueError("SVG 不允许样式表或其它处理指令。")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError("SVG 不是有效的 XML。") from exc
    allowed = set("svg g defs title desc metadata path rect circle ellipse line polyline polygon text tspan textPath use symbol clipPath mask linearGradient radialGradient stop pattern marker filter feBlend feColorMatrix feComponentTransfer feComposite feConvolveMatrix feDiffuseLighting feDisplacementMap feDistantLight feDropShadow feFlood feFuncA feFuncB feFuncG feFuncR feGaussianBlur feMerge feMergeNode feMorphology feOffset fePointLight feSpecularLighting feSpotLight feTile feTurbulence style".split())
    if root.tag not in {"svg", "{http://www.w3.org/2000/svg}svg"}:
        raise ValueError("SVG 根元素无效。")
    nodes = list(root.iter())
    if len(nodes) > 100000:
        raise ValueError("SVG 元素数量超过限制。")
    if not any(node.tag.rsplit("}", 1)[-1] in {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "text", "use"} for node in nodes):
        raise ValueError("SVG 没有可编辑的矢量元素。")
    for node in nodes:
        if node.tag.startswith("{") and not node.tag.startswith("{http://www.w3.org/2000/svg}"):
            raise ValueError("SVG 不允许外部命名空间元素。")
        tag = node.tag.rsplit("}", 1)[-1]
        if tag not in allowed:
            raise ValueError(f"SVG 包含不支持的非静态矢量元素：{tag}")
        for key, value in node.attrib.items():
            name = key.rsplit("}", 1)[-1].lower()
            if name.startswith("on") or name == "base" or (name == "href" and not value.startswith("#")):
                raise ValueError("SVG 不允许事件处理、外部引用或内嵌位图。")
        css = " ".join(node.attrib.values()) + " " + ("".join(node.itertext()) if tag == "style" else "")
        if "@" in css or "/*" in css or re.search(r"expression\s*\(|\\", css, re.I):
            raise ValueError("SVG 包含不支持的样式内容。")
        for target in re.findall(r"url\s*\((.*?)\)", css, re.I):
            if not target.strip(" \t\r\n\"'").startswith("#"):
                raise ValueError("SVG 不允许外部资源。")
    return root


def preflight_gif(raw: bytes) -> None:
    if len(raw) < 13 or len(raw) > 48 * 1024 * 1024 or raw[:6] not in (b"GIF87a", b"GIF89a"):
        raise ValueError("GIF 长度或文件头无效。")
    width, height = int.from_bytes(raw[6:8], "little"), int.from_bytes(raw[8:10], "little")
    if not 0 < width <= 8192 or not 0 < height <= 8192:
        raise ValueError("GIF 尺寸超过限制。")
    pos = 13 + (3 * (1 << ((raw[10] & 7) + 1)) if raw[10] & 128 else 0)
    frames = pixels = 0

    def skip_blocks(offset: int) -> int:
        while offset < len(raw):
            size = raw[offset]
            offset += 1
            if not size:
                return offset
            offset += size
        raise ValueError("GIF 数据块不完整。")

    while pos < len(raw):
        block = raw[pos]
        pos += 1
        if block == 0x21:
            if pos >= len(raw):
                raise ValueError("GIF 扩展不完整。")
            pos = skip_blocks(pos + 1)
        elif block == 0x2C:
            if pos + 9 > len(raw):
                raise ValueError("GIF 帧不完整。")
            x, y, w, h = [int.from_bytes(raw[pos + i:pos + i + 2], "little") for i in (0, 2, 4, 6)]
            flags = raw[pos + 8]
            pos += 9
            frames += 1
            pixels += w * h
            if frames > 64 or not w or not h or x + w > width or y + h > height or pixels > 64 * 1024 * 1024:
                raise ValueError("GIF 帧数、尺寸或总像素超过限制。")
            if flags & 128:
                pos += 3 * (1 << ((flags & 7) + 1))
            if pos >= len(raw):
                raise ValueError("GIF 色板不完整。")
            pos = skip_blocks(pos + 1)
        elif block == 0x3B:
            if frames < 2 or pos != len(raw):
                raise ValueError("GIF 必须包含多帧和有效结尾。")
            return
        else:
            raise ValueError("GIF 含无效数据块。")
    raise ValueError("GIF 缺少结尾。")


def inspect_artifact(path: Path, *, previews: bool = False) -> Dict[str, Any]:
    """Inspect real content; metadata never certifies visual/semantic quality."""
    raw = path.read_bytes()
    if path.suffix.lower() == ".svg":
        root = parse_static_svg(raw)
        result: Dict[str, Any] = {"artifact_type": "svg", "vector_element_count": sum(1 for n in root.iter() if n.tag.rsplit("}", 1)[-1] in {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "text", "use"}), "structural_check_passed": True}
        viewbox = root.get("viewBox", "").replace(",", " ").split()
        if len(viewbox) == 4:
            try:
                result["view_box"] = [float(v) for v in viewbox]
            except ValueError:
                pass
        if previews:
            try:
                import cairosvg
                preview = path.with_suffix(".preview.png")
                cairosvg.svg2png(bytestring=raw, write_to=str(preview), output_width=1200, output_height=900)
                result["preview_path"] = str(preview)
            except Exception:
                result["preview_warning"] = "SVG 原件已校验；PNG 预览需要可用的 CairoSVG 与 Cairo，请用浏览器检查原件。"
        return result
    from PIL import Image, ImageDraw

    if raw.startswith((b"GIF87a", b"GIF89a")):
        preflight_gif(raw)
    with Image.open(io.BytesIO(raw)) as image:
        result = {"artifact_type": (image.format or "raster").lower(), "width": image.width, "height": image.height, "structural_check_passed": True}
        if image.format != "GIF":
            return result
        count = image.n_frames
        if not 2 <= count <= 64 or image.width > 8192 or image.height > 8192 or image.width * image.height * count > 64 * 1024 * 1024:
            raise ValueError("GIF 帧数、尺寸或总像素超过限制，或不是动画 GIF。")
        if "loop" not in image.info:
            raise ValueError("GIF 缺少循环信息。")
        durations = []
        for index in range(count):
            image.seek(index)
            durations.append(int(image.info.get("duration", 0)))
        result.update({"frame_count": count, "frame_durations_ms": durations, "duration_ms": sum(durations), "loop": image.info.get("loop"), "animated": count > 1})
        if previews:
            indices = sorted({round(i * (count - 1) / 5) for i in range(6)})
            sheet = Image.new("RGB", (3 * 320, ((len(indices) + 2) // 3) * 260), "white")
            draw = ImageDraw.Draw(sheet)
            for slot, index in enumerate(indices):
                image.seek(index)
                thumb = image.convert("RGBA")
                thumb.thumbnail((320, 230))
                x, y = (slot % 3) * 320, (slot // 3) * 260
                sheet.paste(thumb, (x, y), thumb)
                draw.text((x + 8, y + 235), f"Frame {index + 1}/{count}", fill="black")
            preview = path.with_suffix(".preview.png")
            sheet.save(preview)
            result["preview_path"] = str(preview)
        return result
