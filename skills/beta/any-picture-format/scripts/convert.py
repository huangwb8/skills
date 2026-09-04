#!/usr/bin/env python3
"""
Any Picture Format - 图片格式转换脚本

支持任意来源（本地文件/URL/剪贴板）的图片转换为目标格式。
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from urllib.request import urlopen, Request

try:
    from PIL import Image, ImageFile, UnidentifiedImageError
    import yaml
except ImportError as e:
    print(json.dumps({
        "success": False,
        "error": f"Missing required dependency: {e}",
        "message": "Please install: pip install Pillow pyyaml"
    }))
    sys.exit(1)


# 加载配置
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"


def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


CONFIG = load_config()


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_config(key: str, default: Any = None) -> Any:
    """获取配置值，支持嵌套路径如 'defaults.output_format'"""
    keys = key.split(".")
    value = CONFIG
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default
    return value if value is not None else default


class ImageConverter:
    """图片转换器"""

    def __init__(self, source: str, output_format: str,
                 output_path: Optional[str] = None,
                 strategy: str = "new",
                 quality: Optional[int] = None):
        self.source = source
        self.output_format = output_format.upper().replace("JPG", "JPEG")
        self.output_path = output_path
        self.strategy = strategy
        self.quality = quality or get_config("defaults.quality", 85)
        # 硬编码白色作为透明背景色（PNG→JPEG 转换场景）
        self.transparency_color = (255, 255, 255)
        self._input_path = None
        self._temp_file = None

    def _load_from_url(self, url: str) -> str:
        """从URL下载图片"""
        timeout = get_config("defaults.download_timeout", 30)
        max_size = get_config("validation.max_file_size", 104857600)  # 100MB

        # 使用系统默认临时目录
        temp_dir_config = get_config("defaults.temp_dir", "")
        if temp_dir_config:
            temp_dir = Path(temp_dir_config)
        else:
            temp_dir = Path(tempfile.gettempdir()) / "any-picture-format"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 验证 URL 安全性（SSRF 防护）
        parsed = urlparse(url)

        # 拒绝非 HTTP/HTTPS 协议
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"不支持的协议: {parsed.scheme}")

        # 拒绝内网地址
        hostname = parsed.hostname
        if hostname:
            hostname_lower = hostname.lower()
            # 拒绝 localhost 和本地回环地址
            if hostname_lower in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
                raise ValueError(f"不允许访问内网地址: {hostname}")
            # 拒绝私有 IP 地址范围
            if (hostname_lower.startswith("127.") or
                hostname_lower.startswith("10.") or
                hostname_lower.startswith("192.168.") or
                (hostname_lower.startswith("172.16.") or
                 (hostname_lower.startswith("172.") and len(hostname_lower.split(".")) >= 2 and 16 <= int(hostname_lower.split(".")[1]) <= 31))):
                raise ValueError(f"不允许访问内网地址: {hostname}")

        # 解析URL获取文件名
        filename = os.path.basename(parsed.path) or "downloaded_image"

        # 如果没有扩展名，添加 .tmp 后缀
        if not Path(filename).suffix:
            filename = f"{filename}.tmp"

        temp_file = temp_dir / filename

        # 下载文件（带大小限制）
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=timeout) as response:
            content_length = response.getheader("Content-Length")
            if content_length and int(content_length) > max_size:
                raise ValueError(f"文件过大: {content_length} 字节")

            downloaded = 0
            with open(temp_file, "wb") as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    if downloaded > max_size:
                        raise ValueError(f"文件过大: {downloaded} 字节，超过限制 {max_size} 字节")
                    f.write(chunk)

        self._temp_file = str(temp_file)
        return str(temp_file)

    def _load_from_clipboard(self) -> str:
        """从剪贴板加载图片"""
        try:
            import pyperclip
            from PIL import ImageGrab
        except ImportError:
            raise ImportError("Clipboard support requires: pip install pyperclip Pillow")

        image = ImageGrab.grabclipboard()
        if image is None:
            raise ValueError("剪贴板中没有图片")

        # 使用系统默认临时目录
        temp_dir_config = get_config("defaults.temp_dir", "")
        if temp_dir_config:
            temp_dir = Path(temp_dir_config)
        else:
            temp_dir = Path(tempfile.gettempdir()) / "any-picture-format"
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_file = temp_dir / "clipboard.png"

        image.save(temp_file, "PNG")
        self._temp_file = str(temp_file)
        return str(temp_file)

    def _get_input_path(self) -> str:
        """获取输入文件路径"""
        if self.source.lower() == "clipboard":
            return self._load_from_clipboard()
        elif self.source.startswith(("http://", "https://")):
            return self._load_from_url(self.source)
        else:
            # 规范化路径（解析 .. 和符号链接）
            path = Path(self.source).resolve()

            if not path.exists():
                raise FileNotFoundError(f"文件不存在: {self.source}")

            if not path.is_file():
                raise ValueError(f"不是文件: {self.source}")

            return str(path)

    def _determine_output_path(self, input_path: str) -> str:
        """确定输出文件路径"""
        if self.output_path:
            return self.output_path

        input_path_obj = Path(input_path)

        if self.strategy == "overwrite":
            return str(input_path_obj.with_suffix(f".{self.output_format.lower()}"))
        else:  # new
            # 生成新文件名：替换扩展名
            return str(input_path_obj.with_suffix(f".{self.output_format.lower()}"))

    def _convert_transparency(self, image: Image.Image) -> Image.Image:
        """处理透明度（用于不支持透明的格式）"""
        format_config = get_config(f"format_config.{self.output_format}", {})
        if not format_config.get("supports_transparency", True):
            if image.mode in ("RGBA", "LA", "P"):
                # 创建白色背景
                background = Image.new("RGB", image.size, self.transparency_color)
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                return background
        return image

    def convert(self) -> Dict[str, Any]:
        """执行转换"""
        try:
            # 加载输入
            self._input_path = self._get_input_path()

            # 打开图片
            ImageFile.LOAD_TRUNCATED_IMAGES = True
            with Image.open(self._input_path) as img:
                original_size = os.path.getsize(self._input_path)
                original_format = img.format or "UNKNOWN"

                # 处理透明度
                img = self._convert_transparency(img)

                # 确定输出路径
                output_path = self._determine_output_path(self._input_path)
                output_dir = Path(output_path).parent
                output_dir.mkdir(parents=True, exist_ok=True)

                # 准备保存参数
                save_kwargs = {}
                if self.output_format in ("JPEG", "WEBP"):
                    save_kwargs["quality"] = self.quality
                elif self.output_format == "PNG":
                    save_kwargs["compress_level"] = get_config("defaults.png_compression", 6)

                # 转换模式
                if self.output_format == "JPEG":
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                elif self.output_format == "PNG":
                    if img.mode not in ("RGB", "RGBA", "LA", "L", "P"):
                        img = img.convert("RGBA")

                # 保存
                img.save(output_path, self.output_format, **save_kwargs)

                # 获取结果
                output_size = os.path.getsize(output_path)

                return {
                    "success": True,
                    "input_path": self._input_path,
                    "output_path": output_path,
                    "format": {
                        "from": original_format,
                        "to": self.output_format
                    },
                    "size": {
                        "before": original_size,
                        "after": output_size,
                        "before_human": format_size(original_size),
                        "after_human": format_size(output_size),
                        "compression_ratio": round((1 - output_size / original_size) * 100, 1) if original_size > 0 else 0
                    },
                    "dimensions": {
                        "width": img.width,
                        "height": img.height
                    }
                }

        except UnidentifiedImageError:
            return {
                "success": False,
                "error": "无法识别为图片文件",
                "error_type": "UnidentifiedImageError",
                "suggestion": "请确认文件是有效的图片格式（PNG/JPEG/WEBP/GIF/BMP/TIFF/ICO/HEIC）"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        finally:
            # 清理临时文件
            if self._temp_file and Path(self._temp_file).exists():
                try:
                    os.remove(self._temp_file)
                except (OSError, PermissionError):
                    # 清理失败不影响主流程
                    pass


class BatchConverter:
    """批量转换器"""

    def __init__(self, directory: str, output_format: str,
                 recursive: bool = False,
                 strategy: str = "new",
                 quality: Optional[int] = None):
        self.directory = Path(directory)
        self.output_format = output_format.upper().replace("JPG", "JPEG")
        self.recursive = recursive
        self.strategy = strategy
        self.quality = quality

    def _get_image_files(self) -> List[Path]:
        """获取目录中的所有图片文件"""
        image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif",
                           ".bmp", ".tiff", ".tif", ".ico", ".heic"}

        if self.recursive:
            files = list(self.directory.rglob("*"))
        else:
            files = list(self.directory.glob("*"))

        return [f for f in files if f.suffix.lower() in image_extensions and f.is_file()]

    def convert(self) -> Dict[str, Any]:
        """执行批量转换"""
        files = self._get_image_files()

        if not files:
            return {
                "success": True,
                "total": 0,
                "success_count": 0,
                "failed_count": 0,
                "results": [],
                "message": "目录中没有找到图片文件"
            }

        results = []
        errors = []

        for file_path in files:
            converter = ImageConverter(
                source=str(file_path),
                output_format=self.output_format,
                strategy=self.strategy,
                quality=self.quality
            )
            result = converter.convert()

            if result.get("success"):
                results.append({
                    "file": str(file_path),
                    "output": result["output_path"],
                    "size_change": result["size"]
                })
            else:
                errors.append({
                    "file": str(file_path),
                    "error": result.get("error"),
                    "error_type": result.get("error_type")
                })

        return {
            "success": True,
            "total": len(files),
            "success_count": len(results),
            "failed_count": len(errors),
            "results": results,
            "errors": errors
        }


def validate_input(source: str) -> Dict[str, Any]:
    """验证输入"""
    try:
        if source.lower() == "clipboard":
            return {
                "valid": True,
                "source_type": "clipboard",
                "message": "剪贴板输入（将在转换时验证）"
            }

        if source.startswith(("http://", "https://")):
            return {
                "valid": True,
                "source_type": "url",
                "format": "unknown",
                "message": "URL输入（将下载后验证）"
            }

        path = Path(source)
        if not path.exists():
            return {
                "valid": False,
                "error": "文件不存在"
            }

        if not path.is_file():
            return {
                "valid": False,
                "error": "不是文件"
            }

        # 尝试打开图片
        try:
            with Image.open(path) as img:
                return {
                    "valid": True,
                    "source_type": "file",
                    "format": img.format or "UNKNOWN",
                    "size": os.path.getsize(path),
                    "size_human": format_size(os.path.getsize(path)),
                    "dimensions": {
                        "width": img.width,
                        "height": img.height
                    }
                }
        except Exception as e:
            return {
                "valid": False,
                "error": f"无法识别为图片: {e}"
            }

    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(description="图片格式转换工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # validate 命令
    validate_parser = subparsers.add_parser("validate", help="验证输入")
    validate_parser.add_argument("--source", required=True, help="输入来源（文件路径/URL/clipboard）")

    # convert 命令
    convert_parser = subparsers.add_parser("convert", help="转换单个图片")
    convert_parser.add_argument("--source", required=True, help="输入来源")
    convert_parser.add_argument("--format", required=True, help="目标格式")
    convert_parser.add_argument("--output", help="输出路径")
    convert_parser.add_argument("--strategy", default="new", choices=["new", "overwrite"], help="输出策略")
    convert_parser.add_argument("--quality", type=int, help="质量参数（1-100）")

    # batch 命令
    batch_parser = subparsers.add_parser("batch", help="批量转换")
    batch_parser.add_argument("--directory", required=True, help="目录路径")
    batch_parser.add_argument("--format", required=True, help="目标格式")
    batch_parser.add_argument("--recursive", action="store_true", help="递归处理子目录")
    batch_parser.add_argument("--strategy", default="new", choices=["new", "overwrite"], help="输出策略")
    batch_parser.add_argument("--quality", type=int, help="质量参数（1-100）")

    args = parser.parse_args()

    if args.command == "validate":
        result = validate_input(args.source)
    elif args.command == "convert":
        converter = ImageConverter(
            source=args.source,
            output_format=args.format,
            output_path=args.output,
            strategy=args.strategy,
            quality=args.quality
        )
        result = converter.convert()
    elif args.command == "batch":
        batch_converter = BatchConverter(
            directory=args.directory,
            output_format=args.format,
            recursive=args.recursive,
            strategy=args.strategy,
            quality=args.quality
        )
        result = batch_converter.convert()
    else:
        parser.print_help()
        sys.exit(1)

    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 返回适当的退出码
    sys.exit(0 if result.get("success", False) else 1)


if __name__ == "__main__":
    main()
