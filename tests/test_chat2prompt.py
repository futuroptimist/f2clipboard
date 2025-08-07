import clipboard

from f2clipboard.chat2prompt import _extract_text, chat2prompt_command


def test_extract_text_removes_html():
    html = "<div>Hello <b>World</b></div>"
    assert _extract_text(html) == "Hello World"


def test_extract_text_unescapes_entities():
    html = "Tom &amp; Jerry"
    assert _extract_text(html) == "Tom & Jerry"


def test_chat2prompt_command_copies_prompt(monkeypatch, capsys):
    def fake_fetch(url: str) -> str:
        assert url == "http://chat"
        return "User: Hi\nAssistant: Hello"

    monkeypatch.setattr("f2clipboard.chat2prompt._fetch_transcript", fake_fetch)

    copied: dict[str, str] = {}

    def fake_copy(text: str) -> None:
        copied["text"] = text

    monkeypatch.setattr(clipboard, "copy", fake_copy)
    chat2prompt_command("http://chat", platform="anthropic")
    out = capsys.readouterr().out
    assert "anthropic" in out
    assert "User: Hi" in copied["text"]
    assert "implement" in copied["text"]
