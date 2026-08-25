from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_STATUS_GLYPHS = set("✓✗⚠✅❌📊🔍🚀⊙▶")


class WindowsCliAndDtHelperTests(unittest.TestCase):
    def test_executable_sources_use_gbk_safe_status_prefixes(self) -> None:
        paths = list((SKILL_ROOT / "scripts").glob("*.py"))
        paths += list((SKILL_ROOT / "scripts").glob("*.R"))
        paths += list((SKILL_ROOT / "templates").glob("*.R"))
        violations = []
        for path in paths:
            text = path.read_text(encoding="utf-8")
            found = sorted(FORBIDDEN_STATUS_GLYPHS.intersection(text))
            if found:
                violations.append(f"{path.name}: {''.join(found)}")
        self.assertEqual(violations, [])

    def test_recommended_dt_helper_is_counted_as_table_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rmd = Path(tmpdir) / "helper.Rmd"
            rmd.write_text(
                "```{r table}\nrender_dt_output(data.frame(x = 1))\n```\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "check_figure_table_interpretation.py"),
                    str(rmd),
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            report = json.loads(result.stdout)
            self.assertEqual(report["total_outputs"], 1)
            self.assertEqual(report["unmatched_outputs"], 1)


if __name__ == "__main__":
    unittest.main()
