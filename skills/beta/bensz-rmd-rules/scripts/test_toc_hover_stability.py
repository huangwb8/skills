from pathlib import Path
import re
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
THEME_CSS = SKILL_ROOT / "templates" / "liquid_glass_theme.css"


class TocHoverStabilityTests(unittest.TestCase):
    def test_dynamic_toc_does_not_animate_hit_test_geometry(self) -> None:
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
        self.assertNotRegex(
            transition.group("value"),
            r"\b(?:all|width|max-height|height|padding|border-radius)\b",
            "animating TOC hit-test geometry can close the menu under the pointer",
        )

    def test_fast_pointer_move_into_toc_keeps_it_open(self) -> None:
        try:
            from playwright.sync_api import Error, sync_playwright
        except ImportError:
            self.skipTest("Playwright is not installed")

        css = THEME_CSS.read_text(encoding="utf-8")
        page_html = (
            '<!doctype html><html class="lg-toc-layout lg-toc-mode-dynamic">'
            f"<head><style>{css}</style><style>.tocify {{ margin-top: 25px; max-width: 260px; }}</style></head>"
            '<body><div id="TOC" class="tocify"><div class="lg-toc-header">目录</div>'
            '<ul><li><a href="#section">Section</a></li></ul></div></body></html>'
        )
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
            except Error as exc:
                self.skipTest(f"Chromium is unavailable: {exc.__class__.__name__}")
            try:
                page = browser.new_page(viewport={"width": 1600, "height": 900})
                page.set_content(page_html)
                page.mouse.move(600, 800)
                page.mouse.move(48, 73)
                page.wait_for_timeout(40)
                page.mouse.move(180, 75)
                page.wait_for_timeout(320)
                self.assertTrue(
                    page.locator("#TOC").evaluate("element => element.matches(':hover')"),
                    "moving into the TOC during expansion must not close it",
                )
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()
