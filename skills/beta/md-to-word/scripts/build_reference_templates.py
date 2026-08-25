#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _die(message: str) -> "NoReturn":  # type: ignore[name-defined]
    raise SystemExit(message)


def _set_run_fonts(style: ET.Element, east_asia: str | None) -> None:
    rpr = style.find("w:rPr", NS)
    if rpr is None:
        rpr = ET.SubElement(style, f"{{{NS['w']}}}rPr")

    rfonts = rpr.find("w:rFonts", NS)
    if rfonts is None:
        rfonts = ET.SubElement(rpr, f"{{{NS['w']}}}rFonts")

    if east_asia:
        rfonts.set(f"{{{NS['w']}}}eastAsia", east_asia)


def _set_paragraph_spacing(style: ET.Element, before: int | None, after: int | None, line: int | None) -> None:
    ppr = style.find("w:pPr", NS)
    if ppr is None:
        ppr = ET.SubElement(style, f"{{{NS['w']}}}pPr")

    spacing = ppr.find("w:spacing", NS)
    if spacing is None:
        spacing = ET.SubElement(ppr, f"{{{NS['w']}}}spacing")

    if before is not None:
        spacing.set(f"{{{NS['w']}}}before", str(before))
    if after is not None:
        spacing.set(f"{{{NS['w']}}}after", str(after))
    if line is not None:
        spacing.set(f"{{{NS['w']}}}line", str(line))
        spacing.set(f"{{{NS['w']}}}lineRule", "auto")


def patch_styles_xml(styles_xml: bytes, *, east_asia_font: str | None, compact: bool) -> bytes:
    tree = ET.ElementTree(ET.fromstring(styles_xml))
    root = tree.getroot()

    for style in root.findall("w:style", NS):
        style_id = style.get(f"{{{NS['w']}}}styleId", "")
        if style_id in {"Normal", "Heading1", "Heading2", "Heading3", "Heading4"}:
            _set_run_fonts(style, east_asia_font)
            if compact:
                _set_paragraph_spacing(style, before=0, after=120, line=240)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build_variant(src_docx: Path, dst_docx: Path, *, east_asia_font: str | None, compact: bool) -> None:
    tmp_dir = dst_docx.parent / (dst_docx.stem + "_tmp")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)

    with zipfile.ZipFile(src_docx, "r") as zin:
        zin.extractall(tmp_dir)

    styles_path = tmp_dir / "word/styles.xml"
    if not styles_path.exists():
        _die(f"未找到 styles.xml：{styles_path}")

    patched = patch_styles_xml(styles_path.read_bytes(), east_asia_font=east_asia_font, compact=compact)
    styles_path.write_bytes(patched)

    if dst_docx.exists():
        dst_docx.unlink()
    with zipfile.ZipFile(dst_docx, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for file_path in sorted(tmp_dir.rglob("*")):
            if file_path.is_dir():
                continue
            arcname = file_path.relative_to(tmp_dir)
            zout.write(file_path, arcname.as_posix())

    shutil.rmtree(tmp_dir)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build md-to-word reference.docx variants from a base file.")
    parser.add_argument("--base", required=True, help="Base reference docx path (default template).")
    parser.add_argument("--out-dir", required=True, help="Output directory (usually md-to-word/assets).")
    args = parser.parse_args(argv)

    base = Path(args.base).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not base.exists():
        _die(f"Base docx 不存在：{base}")

    (out_dir / "reference-default.docx").write_bytes(base.read_bytes())

    build_variant(
        out_dir / "reference-default.docx",
        out_dir / "reference-cn-modern.docx",
        east_asia_font="Microsoft YaHei",
        compact=False,
    )

    build_variant(
        out_dir / "reference-default.docx",
        out_dir / "reference-compact.docx",
        east_asia_font=None,
        compact=True,
    )

    print("OK:", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
