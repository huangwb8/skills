from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'validate_links.py'
SPEC = importlib.util.spec_from_file_location('validate_links', SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class AnchorAndGetFallbackTests(unittest.TestCase):
    def test_local_anchor_is_validated_against_heading_and_html_id(self) -> None:
        content = '# 使用方法\n\n<a id="custom-anchor"></a>\n[标题](#使用方法) [显式](#custom-anchor) [缺失](#missing)'
        refs = MODULE.extract_references(content)
        results = MODULE.validate_references(refs, {}, content)
        self.assertEqual([item['validation']['valid'] for item in results], [True, True, False])
        self.assertTrue(all(item['validation'].get('local_anchor') for item in results))

    def test_head_405_falls_back_to_limited_get(self) -> None:
        with patch.object(MODULE.subprocess, 'check_output', side_effect=['405\nhttps://example.test', '200\nhttps://example.test']) as call:
            result = MODULE.validate_url('https://example.test')
        self.assertTrue(result['valid'])
        self.assertEqual(result['status_code'], 200)
        self.assertEqual(call.call_count, 2)
        self.assertIn('-I', call.call_args_list[0].args[0])
        self.assertIn('--range', call.call_args_list[1].args[0])


if __name__ == '__main__':
    unittest.main()
