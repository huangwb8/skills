import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_targets_renv.py"

class TargetsRenvChecks(unittest.TestCase):
    def run_check(self, root, mode="auto"):
        out = subprocess.run([sys.executable, str(SCRIPT), str(root), "--mode", mode], text=True, capture_output=True)
        return out.returncode, json.loads(out.stdout)

    def test_new_project_requires_three_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, result = self.run_check(Path(tmp), "new")
            self.assertEqual(code, 1)
            self.assertEqual(result["missing"], ["_targets.R", "renv.lock", "renv/activate.R"])

    def test_existing_project_does_not_require_missing_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "analysis.R").write_text("# existing\n")
            code, result = self.run_check(root, "auto")
            self.assertEqual(code, 0)
            self.assertEqual(result["mode"], "existing")
            self.assertEqual(result["missing"], [])

    def test_new_project_passes_when_assets_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "_targets.R").write_text("# targets\n")
            (root / "renv.lock").write_text("{}\n")
            (root / "renv").mkdir()
            (root / "renv" / "activate.R").write_text("# renv\n")
            code, result = self.run_check(root, "new")
            self.assertEqual(code, 0)
            self.assertEqual(result["missing"], [])

if __name__ == "__main__":
    unittest.main()
