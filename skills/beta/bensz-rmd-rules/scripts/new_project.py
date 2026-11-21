#!/usr/bin/env python3
"""Copy a runnable demonstration into a new project directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


HTML_THEMES = {
    "liquid-glass": (
        "    theme: default\n"
        "    toc: true\n"
        "    toc_float: true\n"
        "    toc_depth: 3\n"
        "    highlight: tango\n"
        "    css: templates/liquid-glass/liquid_glass_theme.css\n"
        "    includes:\n"
        "      after_body: templates/liquid-glass/liquid_glass_lightbox.html"
    ),
    "flatly": "    theme: flatly",
    "plain": "",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("simple", "complex"))
    parser.add_argument("destination", type=Path, help="new directory; its parent must exist")
    parser.add_argument("--detail", "--dt", action="store_true",
                        help="add a wide-table appendix; the summary already uses DT")
    parser.add_argument("--theme", choices=HTML_THEMES, default="liquid-glass",
                        help="HTML theme (default: liquid-glass)")
    args = parser.parse_args()
    templates = Path(__file__).resolve().parents[1] / "templates"
    destination = args.destination
    source = (templates / "report.Rmd").read_text(encoding="utf-8")
    theme = HTML_THEMES[args.theme]
    source = source.replace("{{HTML_THEME}}\n", f"{theme}\n" if theme else "", 1)
    setup = (templates / f"{args.mode}.Rmd").read_text(encoding="utf-8")
    source = source.replace("{{SETUP}}", setup.rstrip(), 1)

    try:
        destination.mkdir()  # Claim the new directory without touching an existing project.
    except OSError as error:
        parser.error(f"cannot create a new project directory: {error.strerror}")

    shutil.copytree(templates / "common", destination, dirs_exist_ok=True)
    packages = ["rmarkdown", "knitr", "DT"]
    if args.mode == "complex":
        shutil.copytree(templates / "complex", destination, dirs_exist_ok=True)
        packages.append("targets")
    if args.theme == "liquid-glass":
        shutil.copytree(templates / "liquid-glass", destination / "templates" / "liquid-glass")
    if args.detail:
        packages.append("htmltools")
        optional = templates / "optional"
        source += (optional / "long-table.Rmd").read_text(encoding="utf-8")
        shutil.copyfile(optional / "detail.csv", destination / "raw" / "detail.csv")
    (destination / "report.Rmd").write_text(source, encoding="utf-8")
    (destination / "00.Environments" / "packages.txt").write_text(
        "\n".join(packages) + "\n", encoding="utf-8"
    )
    print("From the new project root, run:")
    print("  Rscript --vanilla run.R prepare")
    print("  Rscript --vanilla run.R build")


if __name__ == "__main__":
    main()
