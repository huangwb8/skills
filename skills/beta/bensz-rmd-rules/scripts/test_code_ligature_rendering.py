from pathlib import Path
import re
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
THEME_CSS = SKILL_ROOT / "templates" / "liquid_glass_theme.css"


class CodeLigatureRenderingTests(unittest.TestCase):
    def test_code_surfaces_disable_programming_ligatures(self) -> None:
        css = THEME_CSS.read_text(encoding="utf-8")
        match = re.search(
            r"pre,\s*\ncode\s*\{(?P<body>.*?)\n\}",
            css,
            re.DOTALL,
        )
        self.assertIsNotNone(
            match,
            "pre/code rule must preserve source operators such as R's <-",
        )
        body = match.group("body")
        self.assertRegex(body, r"font-variant-ligatures:\s*none\s*;")
        self.assertRegex(body, r'font-feature-settings:[^;]*"liga"\s+0')
        self.assertRegex(body, r'font-feature-settings:[^;]*"calt"\s+0')


if __name__ == "__main__":
    unittest.main()
