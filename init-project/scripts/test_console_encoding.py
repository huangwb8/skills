from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "generate.py"


def _load_generate_module():
    spec = importlib.util.spec_from_file_location("init_project_generate_for_test", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load generate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _AsciiStream:
    encoding = "ascii"

    def __init__(self) -> None:
        self.data = ""

    def write(self, text: str) -> int:
        encoded = text.encode(self.encoding)
        decoded = encoded.decode(self.encoding)
        self.data += decoded
        return len(text)

    def flush(self) -> None:
        return None


class _BrokenStream(_AsciiStream):
    def write(self, text: str) -> int:
        raise OSError("simulated stream failure")


class ConsoleEncodingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_generate_module()

    def _run_cli(self, args: list[str], *, encoding: str) -> tuple[subprocess.CompletedProcess[bytes], Path]:
        tempdir = tempfile.TemporaryDirectory(prefix="init-project-console-")
        self.addCleanup(tempdir.cleanup)
        project_root = Path(tempdir.name) / "project"
        project_root.mkdir()
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = f"{encoding}:strict"
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            cwd=str(project_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return proc, project_root

    def test_proxy_retries_only_unicode_encode_error(self) -> None:
        stream = _AsciiStream()
        proxy = self.module._UnicodeSafeTextStream(stream)
        proxy.write("status ✅")
        self.assertIn("\\u2705", stream.data)

        with self.assertRaises(OSError):
            self.module._UnicodeSafeTextStream(_BrokenStream()).write("plain text")

    def test_non_reconfigurable_streams_are_wrapped(self) -> None:
        stdout = _AsciiStream()
        stderr = _AsciiStream()
        original_stdout, original_stderr = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = stdout, stderr
            self.module._configure_console_streams()
            self.assertIsInstance(sys.stdout, self.module._UnicodeSafeTextStream)
            self.assertIsInstance(sys.stderr, self.module._UnicodeSafeTextStream)
            sys.stdout.write("✅")
            sys.stderr.write("❌")
        finally:
            sys.stdout, sys.stderr = original_stdout, original_stderr
        self.assertIn("\\u2705", stdout.data)
        self.assertIn("\\u274c", stderr.data)

    def test_auto_mode_completes_under_strict_gbk(self) -> None:
        proc, project_root = self._run_cli(["--auto", "--disable-bac"], encoding="gbk")
        output = (proc.stdout + proc.stderr).decode("gbk", errors="replace")
        self.assertEqual(proc.returncode, 0, output)
        self.assertNotIn("UnicodeEncodeError", output)
        for name in ("AGENTS.md", "CLAUDE.md", "README.md", "CHANGELOG.md", ".gitignore"):
            self.assertTrue((project_root / name).exists(), name)
        self.assertTrue((project_root / "docs" / "plans").is_dir())

    def test_manual_mode_completes_under_strict_gbk(self) -> None:
        proc, project_root = self._run_cli(
            [
                "--project-name",
                "console-test",
                "--project-description",
                "encoding regression",
                "--disable-bac",
            ],
            encoding="gbk",
        )
        output = (proc.stdout + proc.stderr).decode("gbk", errors="replace")
        self.assertEqual(proc.returncode, 0, output)
        self.assertNotIn("UnicodeEncodeError", output)
        self.assertTrue((project_root / "AGENTS.md").exists())
        self.assertTrue((project_root / "CLAUDE.md").exists())

    def test_utf8_behavior_remains_successful(self) -> None:
        proc, project_root = self._run_cli(["--auto", "--disable-bac"], encoding="utf-8")
        output = (proc.stdout + proc.stderr).decode("utf-8", errors="replace")
        self.assertEqual(proc.returncode, 0, output)
        self.assertIn("已生成", output)
        self.assertTrue((project_root / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()
