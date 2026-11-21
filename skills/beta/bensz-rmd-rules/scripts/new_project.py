#!/usr/bin/env python3
"""Create a runnable targets and renv project with a research report."""

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
    parser.add_argument("destination", type=Path, help="new directory; its parent must exist")
    parser.add_argument("--detail", "--dt", action="store_true",
                        help="add a searchable appendix of the report's paired records")
    parser.add_argument("--theme", choices=HTML_THEMES, default="liquid-glass",
                        help="HTML theme (default: liquid-glass)")
    args = parser.parse_args()
    skill_root = Path(__file__).resolve().parents[1]
    templates = skill_root / "templates"
    project = templates / "project"
    report_template = project / "01.01.01-paired-change.Rmd"
    destination = args.destination
    source = report_template.read_text(encoding="utf-8")
    theme = HTML_THEMES[args.theme]
    source = source.replace("{{HTML_THEME}}\n", f"{theme}\n" if theme else "", 1)

    try:
        destination.mkdir()  # Claim the new directory without touching an existing project.
    except OSError as error:
        parser.error(f"cannot create a new project directory: {error.strerror}")

    # Write the report once after applying the theme and any appendix.
    shutil.copytree(project, destination, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(report_template.name))
    packages = ["rmarkdown", "knitr", "DT", "targets"]
    if args.theme == "liquid-glass":
        shutil.copytree(skill_root / "assets" / "liquid-glass",
                        destination / "templates" / "liquid-glass")
    if args.detail:
        source += (templates / "detail" / "appendix.Rmd").read_text(encoding="utf-8")
    (destination / report_template.name).write_text(source, encoding="utf-8")
    (destination / "00.Environments" / "packages.txt").write_text(
        "\n".join(packages) + "\n", encoding="utf-8"
    )
    print("From the new project root, run:")
    print("  Rscript --vanilla run.R prepare")
    print("  Rscript --vanilla run.R build")


if __name__ == "__main__":
    main()
