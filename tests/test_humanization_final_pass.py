"""Contract and fail-closed routing tests for the Responses API entry point."""

from io import BytesIO
import json
from pathlib import Path
import runpy
import subprocess
import sys
from urllib.request import HTTPError

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/alpha/humanization/scripts/finalize_prose.py"
ENTRY = runpy.run_path(str(SCRIPT))


@pytest.mark.parametrize("url", [
    "http://benszresearch.com/v1",
    "https://notbenszresearch.com/v1",
    "https://benszresearch.com.example.org/v1",
    "https://benszresearch.com@example.org/v1",
    "https://example.org@benszresearch.com/v1",
    "https://benszresearch.com/v1?endpoint=example.org",
])
def test_nonmatching_provider_skips_before_reading_draft(tmp_path, monkeypatch, url):
    (tmp_path / "config.toml").write_text(
        f'model_provider = "active"\n[model_providers.active]\nbase_url = "{url}"\n'
        '[model_providers.other]\nbase_url = "https://api.benszresearch.com/v1"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    result = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path / "missing.md")], capture_output=True)
    assert (result.returncode, result.stdout, result.stderr) == (3, b"", b"")


@pytest.mark.parametrize(("profile_args", "prompt_name"), [
    ([], "PROMPT_A"),
    (["--prompt-profile", "academic"], "PROMPT_A_ACADEMIC"),
])
def test_codex_wire_request_and_utf8_delivery(tmp_path, monkeypatch, capsysbinary, profile_args, prompt_name):
    (tmp_path / "config.toml").write_text(
        'model_provider = "other"\nprofile = "edit"\n[profiles.edit]\nmodel_provider = "active"\n'
        '[model_providers.active]\nbase_url = "https://example.benszresearch.com/api/v1/"\n'
        'env_key = "TEST_CODEX_PROVIDER_KEY"\n', encoding="utf-8",
    )
    draft = tmp_path / "拟稿 t0.md"
    draft.write_bytes("初稿。[附录](./notes.md)\r\n".encode())
    requirements = tmp_path / "写作要求.txt"
    requirements.write_text("保留链接。", encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    monkeypatch.setenv("TEST_CODEX_PROVIDER_KEY", "fake-key")
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), str(draft), "--requirements-file", str(requirements), *profile_args])
    final = "新版正文。[附录](./notes.md)\r\n"

    class FakeOpener:
        def open(self, request, *, timeout):
            assert request.full_url == "https://example.benszresearch.com/api/v1/responses"
            assert request.get_header("Authorization") == "Bearer fake-key"
            assert request.get_header("Originator") == "codex_cli_rs"
            assert request.get_header("User-agent") == "codex_cli_rs"
            body = json.loads(request.data)
            assert body["stream"] is True and body["store"] is False
            assert body["model"] == "gpt-6.2-sol" and body["reasoning"] == {"effort": "medium"}
            system, constraints, prose = body["input"]
            assert system == {"role": "system", "content": [{"type": "input_text", "text": ENTRY[prompt_name]}]}
            assert constraints["role"] == "developer" and "保留链接。" in constraints["content"][0]["text"]
            assert prose["role"] == "user" and prose["content"][0]["text"].encode() == draft.read_bytes()
            events = [
                {"type": "response.output_text.delta", "delta": "部分草稿"},
                {"type": "response.completed", "response": {"status": "completed", "output": [
                    {"type": "reasoning"},
                    {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": final}]},
                ]}},
            ]
            return BytesIO(b"".join(b"data: " + json.dumps(event).encode() + b"\r\n\r\n" for event in events))

    def build_opener(redirect_handler):
        assert redirect_handler.redirect_request(None, None, 302, "", {}, "https://example.org") is None
        return FakeOpener()

    monkeypatch.setitem(ENTRY["main"].__globals__, "build_opener", build_opener)
    assert ENTRY["main"]() == 0
    assert capsysbinary.readouterr() == (final.encode(), b"")


@pytest.mark.parametrize("events", [
    [{"type": "response.output_text.delta", "delta": "partial text"}],
    [{"type": "response.incomplete", "response": {}}],
    [{"type": "response.completed", "response": {"status": "completed", "output": []}}],
    [{"type": "response.completed", "response": {"status": "completed", "output": [
        {"type": "message", "role": "assistant", "content": [{"type": "refusal", "refusal": "no"}]},
    ]}}],
])
def test_missing_or_unusable_final_text_is_rejected(events):
    with pytest.raises(ENTRY["FinalPassError"]):
        ENTRY["completed_text"](events)


def test_http_errors_do_not_print_response_or_draft(tmp_path, monkeypatch, capsys):
    draft = tmp_path / "draft.txt"
    draft.write_text("private example", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), str(draft)])
    globals_ = ENTRY["main"].__globals__
    monkeypatch.setitem(globals_, "selected_provider", lambda _: {"base_url": "https://benszresearch.com/v1"})

    def fail(*args):
        raise HTTPError("https://benszresearch.com/v1/responses", 403, "private example", {}, BytesIO(b"private"))

    monkeypatch.setitem(globals_, "rewrite", fail)
    assert ENTRY["main"]() == 1
    assert capsys.readouterr() == ("", "final_pass_http_403\n")
