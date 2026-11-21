#!/usr/bin/env python3
"""Copy a runnable demonstration into a new project directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("simple", "complex"))
    parser.add_argument("destination", type=Path, help="new directory; its parent must exist")
    parser.add_argument("--dt", action="store_true", help="add an interactive wide-table appendix")
    parser.add_argument("--theme", choices=("flatly",), help="use the optional built-in Bootswatch theme")
    args = parser.parse_args()
    templates = Path(__file__).resolve().parents[1] / "templates"
    destination = args.destination

    try:
        destination.mkdir()  # Claim the new directory without touching an existing project.
    except OSError as error:
        parser.error(f"cannot create a new project directory: {error.strerror}")

    for layer in (templates / "common", templates / args.mode):
        shutil.copytree(layer, destination, dirs_exist_ok=True)
    report = destination / "report.Rmd"
    source = report.read_text(encoding="utf-8")
    packages = ["rmarkdown", "knitr"]
    if args.mode == "complex":
        packages.append("targets")
    if args.theme == "flatly":
        source = source.replace("    code_folding: hide\n", "    code_folding: hide\n    theme: flatly\n", 1)
    if args.dt:
        packages.extend(("DT", "htmltools"))
        optional = templates / "optional"
        source += (optional / "long-table.Rmd").read_text(encoding="utf-8")
        shutil.copyfile(optional / "detail.csv", destination / "raw" / "detail.csv")
    report.write_text(source, encoding="utf-8")
    (destination / "00.Environments" / "packages.txt").write_text(
        "\n".join(packages) + "\n", encoding="utf-8"
    )
    print("From the new project root, run:")
    print("  Rscript --vanilla run.R prepare")
    print("  Rscript --vanilla run.R build")


if __name__ == "__main__":
    main()
