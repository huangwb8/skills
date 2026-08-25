#!/usr/bin/env python3
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile


def _run(cmd, *, env=None, cwd=None):
    proc = subprocess.run(
        cmd,
        env=env,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout


def _which(cmd, env):
    return shutil.which(cmd, path=env.get("PATH"))


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def _detect_pandoc(env):
    pandoc = _which("pandoc", env)
    if not pandoc:
        return None, None
    code, out = _run([pandoc, "--version"], env=env)
    if code != 0:
        return pandoc, None
    first = out.splitlines()[0].strip() if out else None
    return pandoc, first


def _github_latest_pandoc_tag(env):
    url = "https://api.github.com/repos/jgm/pandoc/releases/latest"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "knit-rmd-html-skill"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("tag_name")


def _pandoc_asset_name(version, system, machine):
    system = system.lower()
    machine = machine.lower()
    if system == "darwin":
        if machine in ("arm64", "aarch64"):
            return f"pandoc-{version}-arm64-macOS.zip"
        if machine in ("x86_64", "amd64"):
            return f"pandoc-{version}-x86_64-macOS.zip"
        raise RuntimeError(f"Unsupported macOS arch: {machine}")
    if system == "linux":
        if machine in ("x86_64", "amd64"):
            return f"pandoc-{version}-linux-amd64.tar.gz"
        if machine in ("arm64", "aarch64"):
            return f"pandoc-{version}-linux-arm64.tar.gz"
        raise RuntimeError(f"Unsupported linux arch: {machine}")
    if system == "windows":
        if machine in ("x86_64", "amd64"):
            return f"pandoc-{version}-windows-x86_64.zip"
        if machine in ("arm64", "aarch64"):
            return f"pandoc-{version}-windows-arm64.zip"
        raise RuntimeError(f"Unsupported windows arch: {machine}")
    raise RuntimeError(f"Unsupported OS: {system}")


def _install_pandoc_zip(zip_path, install_root):
    install_root = os.path.abspath(install_root)
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            target = os.path.abspath(os.path.join(install_root, member.filename))
            if os.path.commonpath([install_root, target]) != install_root:
                raise RuntimeError(f"Unsafe path in Pandoc zip: {member.filename}")
        zf.extractall(install_root)

    candidates = []
    for root, _, filenames in os.walk(install_root):
        for filename in filenames:
            if filename.lower() in {"pandoc", "pandoc.exe"}:
                candidates.append(os.path.join(root, filename))
    candidates.sort()
    if not candidates:
        raise RuntimeError("Pandoc zip extracted but no pandoc or pandoc.exe executable was found.")
    if len(candidates) > 1:
        relative = [os.path.relpath(path, install_root) for path in candidates]
        raise RuntimeError(f"Pandoc zip contains ambiguous executables: {', '.join(relative)}")
    return candidates[0]


def _ensure_pandoc(env, *, version, no_install):
    pandoc, verline = _detect_pandoc(env)
    if pandoc:
        return pandoc, verline
    if no_install:
        raise RuntimeError("pandoc not found in PATH, and --no-install is set.")

    system = platform.system()
    machine = platform.machine()
    asset = _pandoc_asset_name(version, system, machine)
    url = f"https://github.com/jgm/pandoc/releases/download/{version}/{asset}"

    home = os.path.expanduser("~")
    pandoc_root = os.path.join(home, ".local", "pandoc")
    bin_root = os.path.join(home, ".local", "bin")
    _ensure_dir(pandoc_root)
    _ensure_dir(bin_root)

    zip_path = os.path.join(pandoc_root, asset)
    if not os.path.exists(zip_path):
        with urllib.request.urlopen(url, timeout=120) as resp, open(zip_path, "wb") as f:
            f.write(resp.read())

    if not asset.endswith(".zip"):
        raise RuntimeError(
            f"Auto-install currently supports zip assets only (got {asset}). "
            f"Please install pandoc manually or use a zip-capable platform."
        )

    # Extract into a versioned folder to keep installs reproducible
    install_root = os.path.join(pandoc_root, f"pandoc-{version}")
    if os.path.exists(install_root):
        shutil.rmtree(install_root)
    _ensure_dir(install_root)

    pandoc_bin = _install_pandoc_zip(zip_path, install_root)
    if not os.path.exists(pandoc_bin):
        raise RuntimeError("pandoc binary not found after installation.")
    try:
        os.chmod(pandoc_bin, 0o755)
    except OSError:
        pass

    link_name = "pandoc.exe" if pandoc_bin.lower().endswith(".exe") else "pandoc"
    link_path = os.path.join(bin_root, link_name)
    try:
        if os.path.islink(link_path) or os.path.exists(link_path):
            os.remove(link_path)
        os.symlink(pandoc_bin, link_path)
    except OSError:
        shutil.copy2(pandoc_bin, link_path)
        try:
            os.chmod(link_path, 0o755)
        except OSError:
            pass

    # Prepend ~/.local/bin to PATH for the current process & downstream
    env2 = dict(env)
    env2["PATH"] = os.pathsep.join([bin_root, env.get("PATH", "")])
    pandoc, verline = _detect_pandoc(env2)
    if not pandoc:
        raise RuntimeError("pandoc installation finished but still not detectable.")
    return pandoc, verline


def _ensure_rscript(env):
    rscript = _which("Rscript", env)
    if not rscript:
        raise RuntimeError("Rscript not found in PATH. Please install R first.")
    return rscript


def main():
    ap = argparse.ArgumentParser(description="Render a .Rmd to HTML (auto-bootstrap pandoc) via a Python wrapper.")
    ap.add_argument("input", help="Path to .Rmd")
    ap.add_argument("-o", "--output", default=None, help="Output HTML path (default: alongside input)")
    ap.add_argument("--pandoc-version", default="3.8.3", help="Pandoc version to auto-install when missing")
    ap.add_argument("--no-install", action="store_true", help="Do not auto-install pandoc / R packages; fail fast")
    ap.add_argument("--quiet", action="store_true", help="Quiet render output")
    args = ap.parse_args()

    inp = os.path.abspath(args.input)
    if not os.path.exists(inp):
        raise SystemExit(f"Input not found: {inp}")
    if not inp.lower().endswith(".rmd"):
        raise SystemExit("Input must be a .Rmd file.")

    out = args.output
    if out is None:
        base, _ = os.path.splitext(inp)
        out = base + ".html"
    out = os.path.abspath(out)

    env = dict(os.environ)

    try:
        pandoc, verline = _ensure_pandoc(env, version=args.pandoc_version, no_install=args.no_install)
    except Exception as e:
        raise SystemExit(f"[pandoc] {e}")

    # Make sure downstream R can see pandoc if installed into ~/.local/bin
    home = os.path.expanduser("~")
    env["PATH"] = os.pathsep.join([os.path.join(home, ".local", "bin"), env.get("PATH", "")])

    try:
        rscript = _ensure_rscript(env)
    except Exception as e:
        raise SystemExit(f"[R] {e}")

    knit_root = os.path.dirname(inp)

    # Render via rmarkdown. Keep the R snippet minimal; orchestration is in Python.
    ensure_rmarkdown = (
        "if (!requireNamespace('rmarkdown', quietly=TRUE)) {"
        + (
            "stop('Package rmarkdown is required but missing (use --no-install to fail fast).', call.=FALSE);"
            if args.no_install
            else "install.packages('rmarkdown', repos='https://cloud.r-project.org');"
        )
        + "}"
    )
    render_call = (
        "rmarkdown::render("
        f"input={json.dumps(inp)}, "
        f"output_file={json.dumps(out)}, "
        f"knit_root_dir={json.dumps(knit_root)}, "
        f"quiet={str(bool(args.quiet)).upper()}"
        ")"
    )
    r_expr = ensure_rmarkdown + ";" + render_call

    code, outlog = _run([rscript, "-e", r_expr], env=env, cwd=knit_root)
    if code != 0:
        sys.stdout.write(outlog)
        raise SystemExit(f"[render] Failed (exit={code}).")

    if not args.quiet and outlog.strip():
        sys.stdout.write(outlog)
    print(f"[render] OK: {out}")


if __name__ == "__main__":
    main()
