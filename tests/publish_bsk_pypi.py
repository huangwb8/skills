#!/usr/bin/env python3
"""Build, validate, and optionally publish bensz-skill-kernel to PyPI."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and earlier; the published package still requires 3.11+.
    tomllib = None  # type: ignore[assignment]


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "packages" / "bensz-skill-kernel"


def package_identity() -> tuple[str, str]:
    content = (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if tomllib is not None:
        project = tomllib.loads(content)["project"]
        return str(project["name"]), str(project["version"])

    project_section = content.split("[project]", 1)[-1].split("\n[", 1)[0]
    values = {}
    for key in ("name", "version"):
        match = re.search(rf'^\s*{key}\s*=\s*"([^"]+)"\s*$', project_section, re.MULTILINE)
        if match is None:
            raise RuntimeError(f"pyproject.toml 的 [project] 缺少 {key}")
        values[key] = match.group(1)
    return values["name"], values["version"]


def _run(command: list[str]) -> None:
    print("$", shlex.join(command), flush=True)
    subprocess.run(command, cwd=REPOSITORY_ROOT, check=True)


def _build_command(output_dir: Path) -> list[str]:
    if importlib.util.find_spec("build") is not None:
        return [sys.executable, "-m", "build", "--outdir", str(output_dir), str(PACKAGE_ROOT)]
    uv = shutil.which("uv")
    if uv:
        return [uv, "tool", "run", "--from", "build", "pyproject-build", "--outdir", str(output_dir), str(PACKAGE_ROOT)]
    raise RuntimeError("缺少构建工具：请安装 build，或安装 uv。")


def _twine_command() -> list[str]:
    if importlib.util.find_spec("twine") is not None:
        return [sys.executable, "-m", "twine"]
    twine = shutil.which("twine")
    if twine:
        return [twine]
    uv = shutil.which("uv")
    if uv:
        return [uv, "tool", "run", "twine"]
    raise RuntimeError("缺少上传工具：请安装 twine，或安装 uv。")


def _public_version_exists(name: str, version: str) -> bool:
    encoded_name = urllib.parse.quote(name, safe="")
    encoded_version = urllib.parse.quote(version, safe="")
    url = f"https://pypi.org/pypi/{encoded_name}/{encoded_version}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        raise RuntimeError(f"PyPI 版本检查失败：HTTP {exc.code}") from exc
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"PyPI 版本检查失败：{exc}") from exc
    return payload.get("info", {}).get("version") == version


def _archive_members(path: Path) -> list[str]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return archive.namelist()
    with tarfile.open(path, mode="r:gz") as archive:
        return archive.getnames()


def _check_archive_cleanliness(artifacts: list[Path]) -> None:
    forbidden = []
    for artifact in artifacts:
        for member in _archive_members(artifact):
            parts = Path(member).parts
            if "__pycache__" in parts or member.endswith((".pyc", ".pyo", ".DS_Store")):
                forbidden.append(f"{artifact.name}:{member}")
    if forbidden:
        preview = ", ".join(forbidden[:5])
        raise RuntimeError(f"发布归档包含缓存或系统文件：{preview}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="构建并检查 bensz-skill-kernel；默认只构建和检查，必须显式传入 --upload 才会上传。",
    )
    parser.add_argument("--upload", action="store_true", help="通过 Twine 上传已检查的构建产物")
    parser.add_argument("--repository-url", help="可选的 PEP 503 仓库 URL；省略时上传到正式 PyPI")
    parser.add_argument("--out-root", type=Path, default=REPOSITORY_ROOT / "tmp" / "bsk-pypi", help="临时构建产物根目录")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    name, version = package_identity()
    args.out_root.mkdir(parents=True, exist_ok=True)
    output_dir = Path(tempfile.mkdtemp(prefix=f"{name}-{version}-", dir=args.out_root)).resolve()

    try:
        _run(_build_command(output_dir))
        artifacts = sorted((*output_dir.glob("*.whl"), *output_dir.glob("*.tar.gz")))
        if len(artifacts) != 2:
            raise RuntimeError(f"预期得到一个 wheel 和一个 sdist，实际得到 {len(artifacts)} 个发布文件。")
        _check_archive_cleanliness(artifacts)

        twine = _twine_command()
        _run([*twine, "check", *(str(path) for path in artifacts)])

        if not args.upload:
            print(f"检查完成，未上传：{name} {version}\n构建目录：{output_dir}")
            return 0

        if args.repository_url is None and _public_version_exists(name, version):
            raise RuntimeError(f"PyPI 已存在不可覆盖的版本：{name} {version}")

        upload = [*twine, "upload", "--non-interactive"]
        if args.repository_url:
            upload.extend(["--repository-url", args.repository_url])
        upload.extend(str(path) for path in artifacts)
        _run(upload)
        print(f"发布完成：{name} {version}\n构建目录：{output_dir}")
        return 0
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"发布流程失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
