import gzip

import pyperclip
from typer.testing import CliRunner

from f2clipboard import app, codex_task
from f2clipboard.codex_task import _decode_log, _extract_pr_url, _parse_pr_url


def test_extract_pr_url_success():
    html = '<html><a href="https://github.com/owner/repo/pull/123">PR</a></html>'
    assert _extract_pr_url(html) == "https://github.com/owner/repo/pull/123"


def test_extract_pr_url_missing():
    assert _extract_pr_url("<html></html>") is None


def test_parse_pr_url():
    assert _parse_pr_url("https://github.com/owner/repo/pull/42") == (
        "owner",
        "repo",
        42,
    )


def test_decode_log_handles_gzip():
    data = gzip.compress(b"hello")
    assert _decode_log(data) == "hello"


def test_decode_log_plain():
    assert _decode_log(b"plain") == "plain"


def test_codex_task_copies_to_clipboard(monkeypatch):
    runner = CliRunner()

    async def fake_process(url: str, settings: object) -> str:
        return "report"

    monkeypatch.setattr(codex_task, "_process_task", fake_process)
    captured: dict[str, str] = {}

    def fake_copy(text: str) -> None:
        captured["text"] = text

    monkeypatch.setattr(pyperclip, "copy", fake_copy)
    result = runner.invoke(app, ["codex-task", "https://example.com/task"])
    assert result.exit_code == 0
    assert "report" in result.stdout
    assert captured["text"] == "report"


def test_codex_task_warns_without_clipboard(monkeypatch):
    runner = CliRunner()

    async def fake_process(url: str, settings: object) -> str:
        return "report"

    monkeypatch.setattr(codex_task, "_process_task", fake_process)

    def fake_copy(text: str) -> None:
        raise pyperclip.PyperclipException("no clipboard")

    monkeypatch.setattr(pyperclip, "copy", fake_copy)
    result = runner.invoke(app, ["codex-task", "https://example.com/task"])
    assert result.exit_code == 0
    assert "report" in result.stdout
    assert "clipboard" in result.stderr.lower()
