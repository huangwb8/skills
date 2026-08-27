from pathlib import Path
import re
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
THEME_CSS = SKILL_ROOT / "templates" / "liquid_glass_theme.css"


class TocHoverStabilityTests(unittest.TestCase):
    def test_dynamic_toc_does_not_animate_hit_test_boundary(self) -> None:
        css = THEME_CSS.read_text(encoding="utf-8")
        match = re.search(
            r"html\.lg-toc-mode-dynamic\.lg-toc-layout #TOC \{(?P<body>.*?)\n  \}",
            css,
            re.DOTALL,
        )
        self.assertIsNotNone(match, "dynamic TOC collapsed rule is missing")
        body = match.group("body")
        transition = re.search(r"transition:\s*(?P<value>.*?);", body, re.DOTALL)
        self.assertIsNotNone(transition, "dynamic TOC transition is missing")
        self.assertNotIn(
            "border-radius",
            transition.group("value"),
            "animating the rounded hit-test boundary causes hover oscillation",
        )


if __name__ == "__main__":
    unittest.main()
