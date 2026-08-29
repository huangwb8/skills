from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'validate_links.py'
SPEC = importlib.util.spec_from_file_location('validate_links', SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class AnchorAndGetFallbackTests(unittest.TestCase):
    def test_relative_document_link_is_checked_as_local_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("# Install\n", encoding="utf-8")
            refs = MODULE.extract_references("[guide](docs/guide.md#install)")
            results = MODULE.validate_references(refs, {}, "", root)
            self.assertTrue(results[0]["validation"]["valid"])
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

    def test_runtime_events_use_kernel_command(self) -> None:
        from bensz_skill_kernel import EventLog

        with tempfile.TemporaryDirectory() as directory:
            events = Path(directory) / 'events.ndjson'
            result = MODULE.record_runtime_events(
                str(events),
                [{'verifier_id': 'bensz.evidence.citation-truth-fit', 'verifier_version': '1.0.0', 'verdict': 'unchecked', 'execution_status': 'unchecked', 'evidence_refs': ['subject_context']}],
                {'decision': 'manual_review', 'reason': 'verification gap or semantic uncertainty'},
                'run-test',
            )
            self.assertTrue(result['recorded'])
            projection = EventLog(events).projection()
            self.assertEqual(projection['verifications'][0]['request_id'], 'run-test')
            self.assertEqual(projection['gate_decisions'][0]['decision'], 'manual_review')

    def test_skill_state_declaration_uses_indexed_state_pack(self) -> None:
        from bensz_skill_kernel import SkillStateDeclaration

        skill_root = SCRIPT.parents[1]
        declaration = SkillStateDeclaration.from_skill_root(skill_root)
        self.assertEqual(declaration.source.name, 'config.yaml')
        self.assertEqual(
            {item.id for item in declaration.registry().definitions(kind='skill')},
            {
                'bensz.validate-md-ref.input-ready',
                'bensz.validate-md-ref.checking',
                'bensz.validate-md-ref.reported',
            },
        )
        self.assertEqual(
            declaration.registry().resolve('validate-md-ref.input-ready').id,
            'bensz.validate-md-ref.input-ready',
        )

    def test_cli_uses_kernel_facts_instead_of_legacy_network_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / 'README.md'
            document.write_text('# Guide\n\n[local](#guide)\n', encoding='utf-8')
            output = StringIO()
            with patch.object(MODULE, 'validate_references', side_effect=AssertionError('legacy adapter called')):
                with redirect_stdout(output):
                    self.assertEqual(MODULE.main([str(document)]), 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload['summary']['total'], 1)
            self.assertTrue(payload['references'][0]['validation']['valid'])
            self.assertEqual(payload['verification']['results'][0]['facts']['summary'], payload['summary'])


if __name__ == '__main__':
    unittest.main()
