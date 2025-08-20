import clipboard
import pytest
import typer

from f2clipboard.chat2prompt import (
    _extract_text,
    _fetch_transcript,
    chat2prompt_command,
)


def test_extract_text_removes_html():
    html = "<div>Hello <b>World</b></div>"
    assert _extract_text(html) == "Hello World"


def test_extract_text_unescapes_entities():
    html = "Tom &amp; Jerry"
    assert _extract_text(html) == "Tom & Jerry"


def test_extract_text_preserves_line_breaks():
    html = "<p>Hello</p><p>World</p>"
    assert _extract_text(html) == "Hello\nWorld"


def test_extract_text_converts_list_items_to_bullets():
    html = "<ul><li>One</li><li>Two</li></ul>"
    assert _extract_text(html) == "- One\n- Two"


def test_extract_text_converts_ordered_list_to_numbered_items():
    html = "<ol><li>First</li><li>Second</li></ol>"
    assert _extract_text(html) == "1. First\n2. Second"


def test_extract_text_respects_ordered_list_start():
    html = '<ol start="3"><li>First</li><li>Second</li></ol>'
    assert _extract_text(html) == "3. First\n4. Second"


def test_chat2prompt_command_copies_prompt(monkeypatch, capsys):
    def fake_fetch(url: str, timeout: float) -> str:
        assert url == "http://chat"
        assert timeout == 10.0
        return "User: Hi\nAssistant: Hello"

    monkeypatch.setattr("f2clipboard.chat2prompt._fetch_transcript", fake_fetch)

    copied: dict[str, str] = {}

    def fake_copy(text: str) -> None:
        copied["text"] = text

    monkeypatch.setattr(clipboard, "copy", fake_copy)
    chat2prompt_command("http://chat", platform="anthropic", timeout=10.0)
    out = capsys.readouterr().out
    assert "anthropic" in out
    assert "User: Hi" in copied["text"]
    assert "implement" in copied["text"]


def test_fetch_transcript_uses_timeout(monkeypatch):
    called: dict[str, float | None] = {}

    class DummyResponse:
        text = ""

        def raise_for_status(self) -> None:  # pragma: no cover - no errors
            return

    def fake_get(url: str, *, follow_redirects: bool, timeout: float | None):
        called["timeout"] = timeout
        return DummyResponse()

    monkeypatch.setattr("httpx.get", fake_get)
    _fetch_transcript("http://chat", timeout=5)
    assert called["timeout"] == 5


def test_chat2prompt_command_respects_timeout(monkeypatch):
    def fake_fetch(url: str, timeout: float) -> str:
        assert timeout == 2
        return ""

    monkeypatch.setattr("f2clipboard.chat2prompt._fetch_transcript", fake_fetch)
    chat2prompt_command("http://chat", timeout=2, copy_to_clipboard=False)


def test_chat2prompt_timeout_must_be_positive():
    with pytest.raises(typer.BadParameter):
        chat2prompt_command("http://chat", timeout=0, copy_to_clipboard=False)
