#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


WORK_DIR_NAME = ".parallel_vibe"

IgnoreFunc = Callable[[str, List[str]], set[str]]


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def compute_project_id(prompt: str) -> str:
    s = prompt.strip().encode("utf-8")
    return hashlib.md5(s).hexdigest()


def _is_hex32(s: str) -> bool:
    if len(s) != 32:
        return False
    for ch in s:
        if ch not in "0123456789abcdef":
            return False
    return True


def _validate_existing_dir(path: Path, *, label: str) -> None:
    if not path.exists():
        raise ValueError(f"{label} does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"{label} is not a directory: {path}")


def _require_within(base_dir: Path, target: Path) -> None:
    base = base_dir.resolve()
    tgt = target.resolve()
    try:
        tgt.relative_to(base)
    except Exception as e:
        raise ValueError(f"path escapes base_dir: base={base} target={tgt}") from e


def _load_yaml_if_possible(path: Path) -> Optional[dict]:
    # Optional dependency: keep KISS; fall back to hardcoded defaults if PyYAML isn't available.
    try:
        import yaml  # type: ignore
    except Exception:
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return None


def _default_config() -> dict:
    return {
        "defaults": {
            "n_threads": 5,
            "thread_id_width": 3,
            "execution": "serial",  # serial|parallel
            "max_parallel": 3,
            "symlink_policy": "error",  # error|skip|keep
            "copy_exclude": [
                WORK_DIR_NAME,
                ".git",
                "node_modules",
                "__pycache__",
                ".DS_Store",
                "Thumbs.db",
                ".venv",
                "venv",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                ".cache",
                ".tox",
                ".coverage",
                "dist",
                "build",
                "target",
            ],
            "synthesize": True,
        },
        "cli": {
            # Prefer simple, stable command composition:
            # - codex: global flags first, then "exec"
            # - claude: global flags first, then "-p"
            "codex": {"cmd": ["codex"], "exec_subcommand": ["exec"], "model_flag": "-m"},
            "claude": {"cmd": ["claude"], "print_subcommand": ["-p"], "model_flag": "--model"},
        },
        "models": {
            # Keep defaults empty to avoid hardcoding model IDs that may not exist in a user's environment.
            # Users can fill these in config.yaml if they want deterministic routing.
            "codex": {"default": "", "fast": "", "deep": ""},
            "claude": {"default": "", "fast": "", "deep": ""},
        },
    }


def load_config() -> dict:
    skill_root = Path(__file__).resolve().parents[1]
    cfg_path = skill_root / "config.yaml"
    cfg = _load_yaml_if_possible(cfg_path)
    if isinstance(cfg, dict):
        merged = _default_config()
        # Shallow merge is enough for our current config shape.
        for k, v in cfg.items():
            if isinstance(v, dict) and isinstance(merged.get(k), dict):
                merged[k].update(v)
            else:
                merged[k] = v
        return merged
    return _default_config()


def wrap_thread_prompt(user_prompt: str, thread_id: str, project_id: str) -> str:
    prefix = (
        "你正在一个并行 thread 的独立工作区中执行任务。\n"
        f"- thread_id: {thread_id}\n"
        f"- project_id: {project_id}\n"
        "- 你的工作目录是当前目录（cwd）。只允许读写当前目录及其子目录。\n"
        "- 禁止访问父目录（..），禁止任何绝对路径写入。\n"
        f"- 禁止访问 {WORK_DIR_NAME}/{project_id} 下的其他 thread 目录。\n"
        "- 所有产物必须落盘到当前目录（workspace）。\n\n"
        "用户指令如下（请严格在本工作区内完成）：\n"
    )
    return prefix + user_prompt


def _parse_copy_exclude(arg: Optional[str], default_list: List[str]) -> List[str]:
    if not arg:
        return list(default_list)
    parts = [p.strip() for p in arg.split(",")]
    return [p for p in parts if p]


def _find_symlinks(src_dir: Path, *, ignore: Optional[IgnoreFunc], max_found: int = 50) -> List[str]:
    found: List[str] = []
    for root, dirs, files in os.walk(src_dir, topdown=True, followlinks=False):
        names = list(dirs) + list(files)
        ignored = set(ignore(root, names)) if ignore else set()

        # Prevent walking into ignored directories to keep scan/copy consistent.
        dirs[:] = [d for d in dirs if d not in ignored]

        for name in names:
            if name in ignored:
                continue
            p = Path(root) / name
            try:
                if p.is_symlink():
                    found.append(str(p.relative_to(src_dir)))
                    if len(found) >= max_found:
                        return found
            except Exception:
                # If we cannot stat an entry, ignore it; copy will likely fail anyway.
                continue
    return found


def copy_workspace(
    src_dir: Path,
    dst_dir: Path,
    exclude_names: Sequence[str],
    *,
    symlink_policy: str,
) -> None:
    base_ignore: Optional[IgnoreFunc] = shutil.ignore_patterns(*exclude_names) if exclude_names else None

    policy = (symlink_policy or "error").strip().lower()
    if policy not in {"error", "skip", "keep"}:
        policy = "error"

    def ignore_with_symlink_skip(path: str, names: List[str]) -> set[str]:
        ignored = set(base_ignore(path, names)) if base_ignore else set()
        if policy != "skip":
            return ignored
        root = Path(path)
        for n in names:
            if n in ignored:
                continue
            try:
                if (root / n).is_symlink():
                    ignored.add(n)
            except Exception:
                continue
        return ignored

    ignore = ignore_with_symlink_skip if (base_ignore or policy == "skip") else None

    if policy == "error":
        syms = _find_symlinks(src_dir, ignore=ignore)
        if syms:
            preview = "\n".join([f"- {s}" for s in syms[:20]])
            more = "" if len(syms) <= 20 else f"\n- ...(and {len(syms) - 20} more)"
            raise ValueError(
                "src_dir contains symlinks; this breaks the workspace boundary assumption.\n"
                "Refuse to proceed by default.\n"
                f"Symlinks (relative to src_dir):\n{preview}{more}\n\n"
                "Use --symlink-policy skip (drop symlinks) or --symlink-policy keep (copy symlinks as symlinks) if you understand the risk."
            )

    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    # Always copy symlinks as symlinks (never dereference), to avoid accidentally pulling in files
    # from outside src_dir via symlink targets.
    shutil.copytree(src_dir, dst_dir, symlinks=True, ignore=ignore)


def _build_shell_cmd_from_template(template: str, wrapped_prompt: str) -> List[str]:
    t = str(template or "")
    if not t.strip():
        raise ValueError("runner-cmd is empty")
    if "{prompt}" not in t:
        raise ValueError("runner-cmd must include a '{prompt}' placeholder")
    cmd_str = t.replace("{prompt}", shlex.quote(wrapped_prompt))
    return shlex.split(cmd_str)


def _cmd_with_optional_model(
    *,
    base_cmd: Sequence[str],
    model_flag: str,
    model: str,
    subcommand: Sequence[str],
    args: Sequence[str],
) -> List[str]:
    cmd: List[str] = list(base_cmd)
    m = str(model or "").strip()
    if m:
        cmd.extend([model_flag, m])
    cmd.extend(list(subcommand))
    cmd.extend(list(args))
    return cmd


def _resolve_model_id(cfg: dict, *, runner_type: str, model: str, profile: str) -> str:
    """
    Prefer an explicit model_id from the plan. If absent, fall back to
    config.yaml:models.{runner_type}.{profile|default}.
    """
    m = str(model or "").strip()
    if m:
        return m
    rt = str(runner_type or "").strip().lower()
    prof = str(profile or "").strip() or "default"
    models = (cfg.get("models", {}) or {}).get(rt, {}) or {}
    return str(models.get(prof) or models.get("default") or "").strip()


def build_runner_cmd(
    *,
    runner_type: str,
    wrapped_prompt: str,
    model: str,
    runner_args: Optional[Sequence[str]],
    runner_cmd_template: Optional[str],
    cfg: dict,
) -> List[str]:
    """
    Build a *single* command for one thread.

    runner_type:
      - codex: codex exec "..."
      - claude: claude -p "..."
      - shell: user-provided template with {prompt}
      - local: deterministic local runner for tests
    """
    t = runner_type.strip().lower()
    extra = list(runner_args or [])

    if t == "codex":
        c = cfg.get("cli", {}).get("codex", {}) or {}
        base_cmd = list(c.get("cmd") or ["codex"])
        sub = list(c.get("exec_subcommand") or ["exec"])
        model_flag = str(c.get("model_flag") or "-m")
        return _cmd_with_optional_model(
            base_cmd=base_cmd,
            model_flag=model_flag,
            model=model,
            subcommand=sub,
            args=extra + [wrapped_prompt],
        )

    if t == "claude":
        c = cfg.get("cli", {}).get("claude", {}) or {}
        base_cmd = list(c.get("cmd") or ["claude"])
        sub = list(c.get("print_subcommand") or ["-p"])
        model_flag = str(c.get("model_flag") or "--model")
        return _cmd_with_optional_model(
            base_cmd=base_cmd,
            model_flag=model_flag,
            model=model,
            subcommand=sub,
            args=extra + [wrapped_prompt],
        )

    if t == "shell":
        if not runner_cmd_template:
            raise ValueError("--runner-cmd is required when runner_type is shell")
        # Shell template can include a model placeholder too, but we keep it minimal.
        return _build_shell_cmd_from_template(runner_cmd_template, wrapped_prompt)

    if t == "local":
        # Deterministic runner for tests: writes a RESULT.md to the workspace.
        code = (
            "import os, pathlib, textwrap\n"
            "tid=os.environ.get('PARALLEL_VIBE_THREAD_ID','')\n"
            "pid=os.environ.get('PARALLEL_VIBE_PROJECT_ID','')\n"
            "p=pathlib.Path('RESULT.md')\n"
            "p.write_text(textwrap.dedent(f'''\\\n"
            "# Local Runner Result\\n\\n"
            "- thread_id: `{tid}`\\n"
            "- project_id: `{pid}`\\n"
            "'''), encoding='utf-8')\n"
            "print('wrote', str(p))\n"
        )
        return [sys.executable, "-c", code]

    raise ValueError(f"unknown runner_type: {runner_type}")


@dataclass(frozen=True)
class ThreadDirs:
    thread_id: str
    thread_root: Path
    workspace: Path
    runner_log: Path
    exit_code_txt: Path
    done_json: Path
    thread_json: Path
    prompt_txt: Path
    result_md: Path


def make_thread_dirs(project_root: Path, thread_id: str) -> ThreadDirs:
    thread_root = project_root / thread_id
    workspace = thread_root / "workspace"
    return ThreadDirs(
        thread_id=thread_id,
        thread_root=thread_root,
        workspace=workspace,
        runner_log=thread_root / "runner.log",
        exit_code_txt=thread_root / "exit_code.txt",
        done_json=thread_root / "done.json",
        thread_json=thread_root / "thread.json",
        prompt_txt=thread_root / "prompt.txt",
        result_md=thread_root / "RESULT.md",
    )


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _write_text(path: Path, s: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s, encoding="utf-8")


def ensure_project_root(workdir: Path, work_dir_name: str, project_id: str) -> Path:
    base = (workdir.resolve() / work_dir_name).resolve()
    project_root = (base / project_id).resolve()
    _require_within(base, project_root)
    project_root.mkdir(parents=True, exist_ok=True)
    return project_root


def ensure_project_json(project_root: Path, meta: dict) -> Path:
    path = project_root / "project.json"
    _write_json(path, meta)
    return path


def _read_text_maybe(path: Path, *, max_chars: int = 80_000) -> str:
    try:
        s = path.read_text(encoding="utf-8")
    except Exception:
        return ""
    if len(s) > max_chars:
        return s[:max_chars] + f"\n\n...(truncated, total_chars={len(s)})\n"
    return s


def _build_split_plan(
    *,
    user_prompt: str,
    n_threads: int,
    thread_id_width: int,
    cfg: dict,
) -> dict:
    """
    Deterministic plan template (no LLM calls). The host AI can still override
    by passing --plan-file.
    """
    def model_for(runner: str, profile: str) -> str:
        models = cfg.get("models", {}).get(runner, {}) or {}
        return str(models.get(profile) or models.get("default") or "").strip()

    def mk_thread(i: int, title: str, runner: str, profile: str, extra: str) -> dict:
        tid = str(i).zfill(thread_id_width)
        # Each thread must always produce a small, structured artifact in workspace root.
        prompt = (
            f"{user_prompt.strip()}\n\n"
            "你需要以本 thread 的角色独立完成上述任务，并遵守以下交付要求：\n"
            "- 必须在当前工作目录写出 `RESULT.md`（Markdown）。\n"
            "- RESULT.md 必须包含：你做了什么、关键决策、你运行了哪些命令（如有）、如何验证、风险与下一步。\n"
            "- 如果你修改了代码：只在当前工作区内修改，并在 RESULT.md 里列出你改动的关键文件路径。\n"
            f"\n你的角色要求：{extra.strip()}\n"
        )
        return {
            "thread_id": tid,
            "title": title,
            "runner": {
                "type": runner,
                "profile": profile,
                "model": model_for(runner, profile),
                "args": [],
            },
            "prompt": prompt,
        }

    threads: List[dict] = []
    if n_threads <= 1:
        threads.append(
            mk_thread(
                1,
                "Full Task",
                "codex",
                "deep",
                "一次性完成：方案设计 + 实现/修改 + 自检 + 轻量验证。优先最小可用，避免过度设计。",
            )
        )
    elif n_threads == 2:
        threads.append(
            mk_thread(1, "Implementation", "codex", "deep", "聚焦实现/修改出一个可用版本。")
        )
        threads.append(
            mk_thread(2, "Review & Risks", "claude", "deep", "聚焦挑错：边界/安全/一致性/可维护性，给出可执行改进清单。")
        )
    elif n_threads == 3:
        threads.append(
            mk_thread(1, "Approach A", "codex", "deep", "实现/修改：路线 A（偏保守、最小改动）。")
        )
        threads.append(
            mk_thread(2, "Approach B", "codex", "deep", "实现/修改：路线 B（偏激进/重构，但仍保持可交付）。")
        )
        threads.append(
            mk_thread(3, "Tests & Edge Cases", "codex", "fast", "聚焦测试与边界：补充最小验证、列出高风险边界。")
        )
    else:
        # Default (>=4): start with planning, then implementations, then tests/review.
        threads.append(
            mk_thread(
                1,
                "Planner",
                "claude",
                "deep",
                "聚焦规划：澄清需求边界，提出结构化执行计划与验收标准。不要假设你能访问其他 thread 的产物。",
            )
        )
        # Implementation threads
        threads.append(
            mk_thread(2, "Implementation A", "codex", "deep", "实现/修改：按计划落地，优先正确性与可验证性。")
        )
        threads.append(
            mk_thread(3, "Implementation B", "codex", "deep", "实现/修改：尝试不同实现或重构路径，争取更高质量。")
        )
        threads.append(
            mk_thread(
                4,
                "Tests & Verification",
                "codex",
                "fast",
                "聚焦测试与验证：跑/补最小测试，列出如何复现与验证。",
            )
        )
        if n_threads >= 5:
            threads.append(
                mk_thread(
                    5,
                    "Code Review",
                    "claude",
                    "deep",
                    "聚焦 code review：指出潜在 bug/回归/安全风险，并给出最小修复建议。",
                )
            )
        # Extra threads beyond 5: keep them useful and diverse.
        for i in range(6, n_threads + 1):
            threads.append(
                mk_thread(
                    i,
                    f"Extra {i}",
                    "codex",
                    "fast",
                    "聚焦补充视角：性能/可读性/文档/错误处理（任选最关键点），输出可执行建议。",
                )
            )

    plan = {
        "plan_version": 1,
        "prompt": user_prompt,
        "threads": threads[:n_threads],
        "synthesis": {
            "enabled": bool(cfg.get("defaults", {}).get("synthesize", True)),
            "runner": {
                "type": "claude",
                "profile": "deep",
                "model": str((cfg.get("models", {}).get("claude", {}) or {}).get("deep") or "").strip(),
                "args": [],
            },
            "prompt": (
                "请综合输入中的多 thread 产物，生成一份可执行的最终结论（面向用户）。\n"
                "要求：\n"
                "- 先给结论，再给取舍理由。\n"
                "- 如果存在互相矛盾的建议，明确你选择哪一个，并说明依据。\n"
                "- 给出最小验证步骤（命令/检查点）。\n"
                "- 输出为 Markdown。\n"
            ),
        },
    }
    return plan


def _validate_plan_obj(plan: dict, *, thread_id_width: int) -> None:
    if not isinstance(plan, dict):
        raise ValueError("plan must be a JSON object")
    threads = plan.get("threads")
    if not isinstance(threads, list) or not threads:
        raise ValueError("plan.threads must be a non-empty list")
    seen: set[str] = set()
    for t in threads:
        if not isinstance(t, dict):
            raise ValueError("each thread must be an object")
        tid = str(t.get("thread_id") or "").strip()
        if not tid.isdigit() or len(tid) != thread_id_width:
            raise ValueError(f"invalid thread_id: {tid!r} (expected {thread_id_width}-digit string)")
        if tid in seen:
            raise ValueError(f"duplicate thread_id in plan: {tid}")
        seen.add(tid)
        runner = t.get("runner")
        if not isinstance(runner, dict):
            raise ValueError(f"thread {tid}: runner must be an object")
        rtype = str(runner.get("type") or "").strip().lower()
        if rtype not in {"codex", "claude", "shell", "local"}:
            raise ValueError(f"thread {tid}: unsupported runner.type: {rtype!r}")
        if rtype == "shell":
            # shell runner needs a template somewhere (thread or global)
            if not str(runner.get("cmd_template") or "").strip():
                raise ValueError(f"thread {tid}: runner.cmd_template required when runner.type=shell")
        if not str(t.get("prompt") or "").strip():
            raise ValueError(f"thread {tid}: prompt is required")


def _run_threads(
    *,
    thread_dirs: List[ThreadDirs],
    cfg: dict,
    plan: dict,
    project_id: str,
    timeout_seconds: int,
    parallel: bool,
    max_parallel: int,
) -> List[dict]:
    plan_threads = {str(t.get("thread_id")): t for t in (plan.get("threads") or []) if isinstance(t, dict)}

    def start_thread(td: ThreadDirs) -> Tuple[subprocess.Popen, Any, dict]:
        t = plan_threads.get(td.thread_id) or {}
        runner = t.get("runner") or {}

        env = os.environ.copy()
        env["PARALLEL_VIBE_THREAD_ID"] = td.thread_id
        env["PARALLEL_VIBE_PROJECT_ID"] = project_id

        start_at = _now_iso()
        wrapped_prompt = wrap_thread_prompt(str(t.get("prompt") or ""), td.thread_id, project_id)

        td.workspace.mkdir(parents=True, exist_ok=True)
        _write_text(td.prompt_txt, wrapped_prompt)
        _write_json(td.thread_json, t)

        cmd = build_runner_cmd(
            runner_type=str(runner.get("type") or ""),
            wrapped_prompt=wrapped_prompt,
            model=_resolve_model_id(
                cfg,
                runner_type=str(runner.get("type") or ""),
                model=str(runner.get("model") or ""),
                profile=str(runner.get("profile") or ""),
            ),
            runner_args=runner.get("args") if isinstance(runner.get("args"), list) else [],
            runner_cmd_template=str(runner.get("cmd_template") or "").strip() or None,
            cfg=cfg,
        )

        log_f = td.runner_log.open("w", encoding="utf-8")
        try:
            p = subprocess.Popen(
                cmd,
                cwd=str(td.workspace),
                stdout=log_f,
                stderr=subprocess.STDOUT,
                env=env,
            )
        except Exception:
            try:
                log_f.close()
            except Exception:
                pass
            raise
        # Keep internal start time for enforcing timeouts in parallel mode.
        try:
            import time as _time

            start_mono = _time.monotonic()
        except Exception:
            start_mono = 0.0
        meta = {
            "thread_id": td.thread_id,
            "runner": runner.get("type"),
            "cmd": cmd,
            "start_at": start_at,
            "_start_mono": start_mono,
        }
        return p, log_f, meta

    def finish_thread(td: ThreadDirs, p: subprocess.Popen, log_f: Any, meta: dict) -> dict:
        err: Optional[str] = None
        exit_code: int = 1
        end_at: str = _now_iso()
        # Internal-only fields (do not persist into done.json).
        meta.pop("_start_mono", None)
        timeout_killed = bool(meta.pop("_timeout_killed", False))
        try:
            polled = p.poll()
            if polled is not None:
                exit_code = int(polled)
                end_at = _now_iso()
            elif timeout_seconds and timeout_seconds > 0:
                exit_code = p.wait(timeout=timeout_seconds)
                end_at = _now_iso()
            else:
                exit_code = p.wait()
                end_at = _now_iso()
        except subprocess.TimeoutExpired:
            err = f"timeout after {timeout_seconds}s"
            try:
                p.kill()
            except Exception:
                pass
            exit_code = 124
            end_at = _now_iso()
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            try:
                p.kill()
            except Exception:
                pass
            exit_code = 1
            end_at = _now_iso()
        finally:
            try:
                log_f.close()
            except Exception:
                pass

        # Pull RESULT.md from workspace root if present.
        ws_result = td.workspace / "RESULT.md"
        if ws_result.exists():
            try:
                td.result_md.write_text(_read_text_maybe(ws_result), encoding="utf-8")
            except Exception:
                pass

        _write_text(td.exit_code_txt, str(exit_code) + "\n")
        done = dict(meta)
        done.update({"end_at": end_at, "exit_code": exit_code})
        if timeout_killed and not err:
            # Normalize timeout semantics even if the OS exit code is e.g. SIGKILL.
            done["exit_code"] = 124
            done["error"] = f"timeout after {timeout_seconds}s"
        elif err:
            done["error"] = err
        _write_json(td.done_json, done)
        return done

    metas: List[dict] = []
    running: List[Tuple[ThreadDirs, subprocess.Popen, Any, dict]] = []

    if not parallel:
        for td in thread_dirs:
            try:
                p, log_f, meta = start_thread(td)
            except FileNotFoundError as e:
                done = {"thread_id": td.thread_id, "exit_code": 127, "error": f"FileNotFoundError: {e}", "start_at": _now_iso(), "end_at": _now_iso()}
                _write_text(td.exit_code_txt, "127\n")
                _write_json(td.done_json, done)
                metas.append(done)
                continue
            except Exception as e:
                done = {"thread_id": td.thread_id, "exit_code": 1, "error": f"{type(e).__name__}: {e}", "start_at": _now_iso(), "end_at": _now_iso()}
                _write_text(td.exit_code_txt, "1\n")
                _write_json(td.done_json, done)
                metas.append(done)
                continue
            metas.append(finish_thread(td, p, log_f, meta))
        return metas

    # Parallel with a simple fixed-size pool (max_parallel).
    cap = max(1, int(max_parallel or 1))
    q = list(thread_dirs)
    while q or running:
        while q and len(running) < cap:
            td = q.pop(0)
            try:
                p, log_f, meta = start_thread(td)
                running.append((td, p, log_f, meta))
            except FileNotFoundError as e:
                done = {"thread_id": td.thread_id, "exit_code": 127, "error": f"FileNotFoundError: {e}", "start_at": _now_iso(), "end_at": _now_iso()}
                _write_text(td.exit_code_txt, "127\n")
                _write_json(td.done_json, done)
                metas.append(done)
            except Exception as e:
                done = {"thread_id": td.thread_id, "exit_code": 1, "error": f"{type(e).__name__}: {e}", "start_at": _now_iso(), "end_at": _now_iso()}
                _write_text(td.exit_code_txt, "1\n")
                _write_json(td.done_json, done)
                metas.append(done)

        # Poll running processes; finish those that exited.
        still: List[Tuple[ThreadDirs, subprocess.Popen, Any, dict]] = []
        progressed = False
        for td, p, log_f, meta in running:
            if p.poll() is None:
                # Enforce per-thread timeout in parallel mode (best-effort).
                if timeout_seconds and timeout_seconds > 0:
                    try:
                        import time as _time

                        start_mono = float(meta.get("_start_mono") or 0.0)
                        if start_mono > 0.0 and (_time.monotonic() - start_mono) > float(timeout_seconds):
                            try:
                                p.kill()
                            except Exception:
                                pass
                            meta["_timeout_killed"] = True
                    except Exception:
                        pass
                still.append((td, p, log_f, meta))
                continue
            metas.append(finish_thread(td, p, log_f, meta))
            progressed = True
        running = still
        if not progressed:
            # Avoid busy-wait.
            try:
                import time

                time.sleep(0.2)
            except Exception:
                pass

    return metas


def render_summary(project_meta: dict, plan: dict, thread_metas: List[dict]) -> str:
    lines: List[str] = []
    lines.append("# parallel-vibe Summary")
    lines.append("")
    lines.append("## Project")
    lines.append(f"- project_id: `{project_meta.get('project_id','')}`")
    lines.append(f"- created_at: `{project_meta.get('created_at','')}`")
    if project_meta.get("last_run_at"):
        lines.append(f"- last_run_at: `{project_meta.get('last_run_at','')}`")
    lines.append(f"- n_threads: `{project_meta.get('n_threads','')}`")
    lines.append(f"- execution: `{project_meta.get('execution','')}`")
    lines.append("")
    lines.append("## Prompt")
    lines.append("")
    lines.append("```text")
    lines.append(str(project_meta.get("last_run_prompt") or project_meta.get("prompt") or ""))
    lines.append("```")
    lines.append("")
    lines.append("## Plan")
    lines.append("")
    for t in plan.get("threads") or []:
        if not isinstance(t, dict):
            continue
        tid = str(t.get("thread_id") or "")
        title = str(t.get("title") or "").strip()
        runner = t.get("runner") or {}
        rtype = str(runner.get("type") or "")
        profile = str(runner.get("profile") or "").strip()
        model = str(runner.get("model") or "").strip()
        extra: List[str] = [f"runner={rtype}"]
        if profile:
            extra.append(f"profile={profile}")
        if model:
            extra.append(f"model={model}")
        if len(extra) > 1:
            lines.append(f"- {tid}: {title} ({', '.join(extra)})")
        else:
            lines.append(f"- {tid}: {title} (runner={rtype})")
    lines.append("")
    lines.append("## Threads")
    lines.append("")
    for tm in sorted(thread_metas, key=lambda x: x.get("thread_id", "")):
        tid = tm.get("thread_id", "")
        ec = tm.get("exit_code", "")
        err = str(tm.get("error") or "").strip()
        if err:
            err = err.replace("\n", " ")
            if len(err) > 140:
                err = err[:140] + "..."
            lines.append(f"- {tid}: exit_code={ec} error={err} (see `{tid}/RESULT.md` and `{tid}/runner.log`)")
        else:
            lines.append(f"- {tid}: exit_code={ec} (see `{tid}/RESULT.md` and `{tid}/runner.log`)")
    lines.append("")
    lines.append("## Where To Look")
    lines.append("")
    lines.append("- 汇总（索引）：`@main/summary.md`")
    lines.append("- 规划：`@main/plan.json`（机器可读） / `@main/plan.md`（人类可读）")
    lines.append("- 各 thread 结果：`{thread_id}/RESULT.md`（如果 runner 生成）")
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    cfg = load_config()
    defaults = cfg.get("defaults", {})

    p = argparse.ArgumentParser(prog="parallel_vibe.py")
    p.add_argument("--prompt", default="", help="用户指令原文（用于生成计划并传给各 thread runner）")
    p.add_argument("--plan-file", default="", help="自定义计划文件（JSON）。如提供，则忽略 --prompt 的自动拆分逻辑。")
    p.add_argument("--plan-only", action="store_true", help="只生成 project 目录与 plan.json，不运行 threads")
    p.add_argument("--n", type=int, default=int(defaults.get("n_threads", 5)), help="线程数（1-9；仅在未提供 --plan-file 时生效）")
    p.add_argument("--src-dir", default=".", help="复制到各 thread/workspace 的源目录（默认当前目录）")
    p.add_argument("--out-dir", default=".", help="创建 .parallel_vibe 的根目录（默认当前目录）")
    # Backward-compatible alias (old versions used --workdir as out-dir).
    p.add_argument("--workdir", default="", help=argparse.SUPPRESS)
    p.add_argument("--project-id", default="", help="复用已有 project_id（32位小写md5）")
    p.add_argument(
        "--resume",
        action="store_true",
        help="项目目录存在时复用（保留 @main 与 project.json；每次运行仍会重建各 thread/workspace）",
    )
    p.add_argument("--timeout-seconds", type=int, default=0, help="0 表示不超时")
    p.add_argument(
        "--copy-exclude",
        default=",".join(list(defaults.get("copy_exclude", []))),
        help="逗号分隔的排除项（用于复制 workspace）",
    )
    p.add_argument(
        "--symlink-policy",
        default=str(defaults.get("symlink_policy") or "error"),
        choices=["error", "skip", "keep"],
        help="src_dir 中遇到 symlink 的处理策略：error(默认拒绝)/skip(剔除)/keep(保留为 symlink；有越界风险)",
    )
    p.add_argument("--parallel", action="store_true", help="并行运行 threads（默认串行）")
    p.add_argument("--max-parallel", type=int, default=int(defaults.get("max_parallel", 3)), help="并行上限（仅 --parallel 时生效）")
    p.add_argument("--synthesize", action="store_true", help="运行汇总 synth（会额外调用一次 runner；默认由 config.yaml 控制）")
    p.add_argument("--no-synthesize", action="store_true", help="禁用 synth（覆盖 config.yaml）")
    p.add_argument("--dry-run", action="store_true", help="只打印/落盘计划与命令，不实际运行")
    args = p.parse_args(argv)

    # Resolve out-dir with backward-compatible behavior.
    out_dir_arg = str(args.out_dir or "").strip()
    if not out_dir_arg and str(args.workdir or "").strip():
        out_dir_arg = str(args.workdir).strip()
    out_dir = Path(out_dir_arg or ".").resolve()
    src_dir = Path(str(args.src_dir)).resolve()

    try:
        _validate_existing_dir(out_dir, label="out_dir")
        _validate_existing_dir(src_dir, label="src_dir")
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    plan_file = str(args.plan_file or "").strip()
    user_prompt = str(args.prompt or "").strip()
    if not plan_file and not user_prompt:
        print("error: either --prompt or --plan-file is required", file=sys.stderr)
        return 2

    work_dir_name = WORK_DIR_NAME
    # Prevent writing outside out_dir if ".parallel_vibe" is a symlink to elsewhere.
    try:
        base = (out_dir.resolve() / WORK_DIR_NAME).resolve()
        _require_within(out_dir.resolve(), base)
    except ValueError as e:
        print(f"error: invalid {WORK_DIR_NAME} directory under out_dir: {e}", file=sys.stderr)
        return 2

    thread_id_width = int(defaults.get("thread_id_width", 3))
    exclude_names = _parse_copy_exclude(str(args.copy_exclude), list(defaults.get("copy_exclude", [])))
    if work_dir_name not in exclude_names:
        exclude_names.append(work_dir_name)

    project_id = str(args.project_id).strip()
    if project_id:
        if not _is_hex32(project_id):
            print("error: --project-id must be 32 lowercase hex chars", file=sys.stderr)
            return 2
    else:
        if user_prompt:
            project_id = compute_project_id(user_prompt)
        elif plan_file:
            try:
                project_id = hashlib.md5(Path(plan_file).read_bytes()).hexdigest()
            except Exception:
                project_id = compute_project_id(plan_file)
        else:
            project_id = compute_project_id("")

    project_root = ensure_project_root(out_dir, work_dir_name, project_id)

    if project_root.exists() and any(project_root.iterdir()) and not args.resume:
        # Avoid surprising overwrites; use --resume to reuse an existing project directory.
        print(f"error: project already exists: {project_root} (use --resume)", file=sys.stderr)
        return 2

    project_json_path = project_root / "project.json"
    created_at = _now_iso()
    base_prompt = user_prompt
    if args.resume and project_json_path.exists():
        try:
            existing = json.loads(project_json_path.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                created_at = str(existing.get("created_at") or created_at)
                base_prompt = str(existing.get("prompt") or base_prompt)
        except Exception:
            pass

    if args.n < 1 or args.n > 9:
        print("error: --n must be in [1, 9]", file=sys.stderr)
        return 2

    # Load or build plan.
    plan: dict
    if plan_file:
        try:
            plan = json.loads(Path(plan_file).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"error: failed to read plan file: {e}", file=sys.stderr)
            return 2
    else:
        plan = _build_split_plan(
            user_prompt=user_prompt,
            n_threads=int(args.n),
            thread_id_width=thread_id_width,
            cfg=cfg,
        )

    try:
        _validate_plan_obj(plan, thread_id_width=thread_id_width)
    except ValueError as e:
        print(f"error: invalid plan: {e}", file=sys.stderr)
        return 2

    # Determine execution mode (default serial).
    exec_mode = "parallel" if bool(args.parallel) else str(defaults.get("execution") or "serial")
    if exec_mode not in {"serial", "parallel"}:
        exec_mode = "serial"

    # Synthesis toggle: config default -> CLI overrides.
    synth_enabled = bool(plan.get("synthesis", {}).get("enabled", False))
    if bool(args.synthesize):
        synth_enabled = True
    if bool(args.no_synthesize):
        synth_enabled = False

    project_meta = {
        "project_id": project_id,
        "created_at": created_at,
        "prompt": base_prompt,
        "last_run_at": _now_iso(),
        "last_run_prompt": user_prompt or base_prompt,
        "n_threads": len(list(plan.get("threads") or [])),
        "execution": exec_mode,
        "src_dir": str(src_dir),
        "out_dir": str(out_dir),
    }
    ensure_project_json(project_root, project_meta)

    # Threads
    thread_dirs: List[ThreadDirs] = []
    for t in plan.get("threads") or []:
        tid = str((t or {}).get("thread_id") or "").strip()
        td = make_thread_dirs(project_root, tid)
        td.thread_root.mkdir(parents=True, exist_ok=True)
        thread_dirs.append(td)

    # Copy workspaces
    for td in thread_dirs:
        try:
            copy_workspace(
                src_dir,
                td.workspace,
                exclude_names,
                symlink_policy=str(args.symlink_policy or "error"),
            )
        except ValueError as e:
            print(f"error: failed to copy workspace for thread {td.thread_id}: {e}", file=sys.stderr)
            return 2

    main_dir = project_root / "@main"
    main_dir.mkdir(parents=True, exist_ok=True)
    plan_json_path = main_dir / "plan.json"
    plan_md_path = main_dir / "plan.md"
    _write_json(plan_json_path, plan)
    # A small human-readable plan rendering.
    plan_lines: List[str] = ["# parallel-vibe Plan", ""]
    plan_lines.append("## Threads")
    plan_lines.append("")
    for t in plan.get("threads") or []:
        if not isinstance(t, dict):
            continue
        tid = str(t.get("thread_id") or "")
        title = str(t.get("title") or "").strip()
        runner = t.get("runner") or {}
        rtype = str(runner.get("type") or "")
        profile = str(runner.get("profile") or "").strip()
        model = str(runner.get("model") or "").strip()
        extra: List[str] = [f"runner={rtype}"]
        if profile:
            extra.append(f"profile={profile}")
        if model:
            extra.append(f"model={model}")
        if len(extra) > 1:
            plan_lines.append(f"- {tid}: {title} ({', '.join(extra)})")
        else:
            plan_lines.append(f"- {tid}: {title} (runner={rtype})")
    plan_lines.append("")
    plan_md_path.write_text("\n".join(plan_lines) + "\n", encoding="utf-8")

    if bool(args.plan_only):
        print(str(project_root))
        return 0

    if bool(args.dry_run):
        # We still create plan + workspaces for traceability.
        print(str(project_root))
        return 0

    # Run threads.
    thread_metas = _run_threads(
        thread_dirs=thread_dirs,
        cfg=cfg,
        plan=plan,
        project_id=project_id,
        timeout_seconds=int(args.timeout_seconds),
        parallel=(exec_mode == "parallel"),
        max_parallel=int(args.max_parallel),
    )

    summary_path = main_dir / "summary.md"
    summary_path.write_text(render_summary(project_meta, plan, thread_metas), encoding="utf-8")

    # Optional synthesis step: run one more CLI call in @main, feeding it thread RESULT.md files.
    if synth_enabled:
        synth = plan.get("synthesis") or {}
        synth_runner = synth.get("runner") or {}
        synth_prompt = str(synth.get("prompt") or "").strip()
        synth_runner_type = str(synth_runner.get("type") or "claude").strip().lower()
        # Build input
        input_lines: List[str] = []
        input_lines.append("# parallel-vibe Synthesis Input")
        input_lines.append("")
        input_lines.append("## Original Prompt")
        input_lines.append("")
        input_lines.append(user_prompt or base_prompt)
        input_lines.append("")
        input_lines.append("## Thread Results")
        input_lines.append("")
        for td in sorted(thread_dirs, key=lambda x: x.thread_id):
            input_lines.append(f"### Thread {td.thread_id}")
            input_lines.append("")
            if td.result_md.exists():
                input_lines.append(_read_text_maybe(td.result_md, max_chars=40_000))
            else:
                input_lines.append("_RESULT.md not found; see runner.log_")
            input_lines.append("")
        synth_input_path = main_dir / "synthesis_input.md"
        synth_input_path.write_text("\n".join(input_lines) + "\n", encoding="utf-8")

        try:
            # If we synthesize via codex, use stdin prompt ("-") and embed synth_prompt into stdin.
            stdin_path = synth_input_path
            wrapped_prompt = synth_prompt
            if synth_runner_type == "codex":
                stdin_lines = ["# Synthesis Instructions", "", synth_prompt, "", "---", ""]
                stdin_lines.extend(input_lines)
                stdin_path = main_dir / "synthesis_stdin.md"
                stdin_path.write_text("\n".join(stdin_lines) + "\n", encoding="utf-8")
                wrapped_prompt = "-"

            cmd = build_runner_cmd(
                runner_type=synth_runner_type,
                wrapped_prompt=wrapped_prompt,
                model=_resolve_model_id(
                    cfg,
                    runner_type=synth_runner_type,
                    model=str(synth_runner.get("model") or ""),
                    profile=str(synth_runner.get("profile") or ""),
                ),
                runner_args=synth_runner.get("args") if isinstance(synth_runner.get("args"), list) else [],
                runner_cmd_template=str(synth_runner.get("cmd_template") or "").strip() or None,
                cfg=cfg,
            )
            _write_json(
                main_dir / "synthesis_meta.json",
                {"runner": synth_runner_type, "cmd": cmd, "start_at": _now_iso()},
            )
            summary_ai_path = main_dir / "summary_ai.md"
            synth_out = summary_ai_path.open("w", encoding="utf-8")
            p2 = subprocess.Popen(
                cmd,
                cwd=str(main_dir),
                stdin=stdin_path.open("r", encoding="utf-8"),
                stdout=synth_out,
                stderr=subprocess.STDOUT,
                env=os.environ.copy(),
            )
            if int(args.timeout_seconds) > 0:
                rc = p2.wait(timeout=int(args.timeout_seconds))
            else:
                rc = p2.wait()
            try:
                synth_out.close()
            except Exception:
                pass
            _write_text(main_dir / "synthesis_exit_code.txt", str(rc) + "\n")
            # Add a pointer in the main summary for discoverability.
            if summary_ai_path.exists():
                try:
                    with summary_path.open("a", encoding="utf-8") as f:
                        f.write("\n## Synthesized Result (AI)\n\n")
                        f.write("见：`@main/summary_ai.md`\n")
                except Exception:
                    pass
        except Exception as e:
            _write_text(main_dir / "synthesis_error.txt", f"{type(e).__name__}: {e}\n")

    print(str(project_root))
    return 0 if all(int(tm.get("exit_code", 1)) == 0 for tm in thread_metas) else 1


if __name__ == "__main__":
    raise SystemExit(main())
