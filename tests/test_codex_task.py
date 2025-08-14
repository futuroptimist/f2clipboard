import asyncio
import gzip

import pytest

from f2clipboard.codex_task import (
    _decode_log,
    _download_log,
    _extract_pr_url,
    _fetch_check_runs,
    _fetch_task_html,
    _parse_pr_url,
    _process_task,
    codex_task_command,
)
from f2clipboard.config import Settings


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


def test_parse_pr_url_trailing_slash() -> None:
    assert _parse_pr_url("https://github.com/owner/repo/pull/42/") == (
        "owner",
        "repo",
        42,
    )


def test_fetch_check_runs_parses_response(monkeypatch):
    class DummyResponse:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self) -> None:  # pragma: no cover - no error path
            pass

        def json(self):
            return self._data

    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.calls: list[str] = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            pass

        async def get(self, path: str):
            self.calls.append(path)
            if path == "/repos/o/r/pulls/1":
                return DummyResponse({"head": {"sha": "abc"}})
            if path == "/repos/o/r/commits/abc/check-runs":
                return DummyResponse({"check_runs": [{"id": 99, "name": "CI"}]})
            raise AssertionError(f"Unexpected path {path}")

    monkeypatch.setattr("f2clipboard.codex_task.httpx.AsyncClient", DummyClient)
    runs = asyncio.run(_fetch_check_runs("https://github.com/o/r/pull/1", None))
    assert runs == [{"id": 99, "name": "CI"}]


def test_fetch_check_runs_includes_token(monkeypatch):
    captured: dict[str, dict[str, str]] = {}

    class DummyResponse:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self) -> None:  # pragma: no cover - no error path
            pass

        def json(self):
            return self._data

    class DummyClient:
        def __init__(self, *args, **kwargs):
            captured["headers"] = kwargs.get("headers", {})

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            pass

        async def get(self, path: str):
            if path == "/repos/o/r/pulls/1":
                return DummyResponse({"head": {"sha": "abc"}})
            return DummyResponse({"check_runs": []})

    monkeypatch.setattr("f2clipboard.codex_task.httpx.AsyncClient", DummyClient)
    asyncio.run(_fetch_check_runs("https://github.com/o/r/pull/1", "tok"))
    assert captured["headers"]["Authorization"] == "Bearer tok"


def test_decode_log_handles_gzip():
    data = gzip.compress(b"hello")
    assert _decode_log(data) == "hello"


def test_decode_log_plain():
    assert _decode_log(b"plain") == "plain"


def test_decode_log_invalid_utf8():
    assert _decode_log(b"\xff\xfe") == "��"


def test_download_log_handles_gzip():
    class DummyResponse:
        def __init__(self, data: bytes):
            self.content = data

        def raise_for_status(self) -> None:  # pragma: no cover - no error path
            pass

    class DummyClient:
        async def get(self, path: str):
            assert path == "/repos/o/r/check-runs/1/logs"
            return DummyResponse(gzip.compress(b"log"))

    result = asyncio.run(_download_log(DummyClient(), "o", "r", 1))
    assert result == "log"


def test_process_task_summarises_large_log(monkeypatch):
    async def fake_html(url: str, cookie: str | None = None) -> str:
        return '<a href="https://github.com/o/r/pull/1">PR</a>'

    async def fake_runs(pr_url: str, token: str | None):
        return [{"id": 1, "name": "Job", "conclusion": "failure"}]

    async def fake_log(client, owner, repo, run_id):
        return "log line\n" * 200  # large

    async def fake_summary(text: str, settings: Settings) -> str:
        return "SUMMARY"

    monkeypatch.setattr("f2clipboard.codex_task._fetch_task_html", fake_html)
    monkeypatch.setattr("f2clipboard.codex_task._fetch_check_runs", fake_runs)
    monkeypatch.setattr("f2clipboard.codex_task._download_log", fake_log)
    monkeypatch.setattr("f2clipboard.codex_task.summarise_log", fake_summary)

    settings = Settings()
    settings.log_size_threshold = 100
    result = asyncio.run(_process_task("http://task", settings))
    assert "SUMMARY" in result
    assert "<details>" in result


def test_process_task_small_log_skips_summarise(monkeypatch):
    async def fake_html(url: str, cookie: str | None = None) -> str:
        return '<a href="https://github.com/o/r/pull/1">PR</a>'

    async def fake_runs(pr_url: str, token: str | None):
        return [{"id": 1, "name": "Job", "conclusion": "failure"}]

    async def fake_log(client, owner, repo, run_id):
        return "short"

    called: list[str] = []

    async def fake_summary(text: str, settings: Settings) -> str:
        called.append("yes")
        return "SUMMARY"

    monkeypatch.setattr("f2clipboard.codex_task._fetch_task_html", fake_html)
    monkeypatch.setattr("f2clipboard.codex_task._fetch_check_runs", fake_runs)
    monkeypatch.setattr("f2clipboard.codex_task._download_log", fake_log)
    monkeypatch.setattr("f2clipboard.codex_task.summarise_log", fake_summary)

    settings = Settings()
    settings.log_size_threshold = 100
    result = asyncio.run(_process_task("http://task", settings))
    assert "short" in result
    assert not called


def test_process_task_ignores_non_failed_runs(monkeypatch):
    async def fake_html(url: str, cookie: str | None = None) -> str:
        return '<a href="https://github.com/o/r/pull/1">PR</a>'

    async def fake_runs(pr_url: str, token: str | None):
        return [
            {"id": 1, "name": "Neutral", "conclusion": "neutral"},
            {"id": 2, "name": "Pending", "conclusion": None},
            {"id": 3, "name": "Fail", "conclusion": "failure"},
        ]

    async def fake_log(client, owner, repo, run_id):
        return f"log {run_id}"

    monkeypatch.setattr("f2clipboard.codex_task._fetch_task_html", fake_html)
    monkeypatch.setattr("f2clipboard.codex_task._fetch_check_runs", fake_runs)
    monkeypatch.setattr("f2clipboard.codex_task._download_log", fake_log)

    settings = Settings()
    result = asyncio.run(_process_task("http://task", settings))
    assert "log 3" in result
    assert "log 1" not in result
    assert "log 2" not in result


def test_codex_task_command_copies_to_clipboard(monkeypatch, capsys):
    async def fake_process(url: str, settings: Settings) -> str:
        return "MD"

    monkeypatch.setattr("f2clipboard.codex_task._process_task", fake_process)
    copied: dict[str, str] = {}

    def fake_copy(text: str) -> None:
        copied["text"] = text

    monkeypatch.setattr("f2clipboard.codex_task.clipboard.copy", fake_copy)
    codex_task_command("http://task")
    out = capsys.readouterr().out
    assert "MD" in out
    assert copied["text"] == "MD"


def test_codex_task_command_skips_clipboard(monkeypatch, capsys):
    async def fake_process(url: str, settings: Settings) -> str:
        return "MD"

    monkeypatch.setattr("f2clipboard.codex_task._process_task", fake_process)
    copied: dict[str, str] = {}

    def fake_copy(text: str) -> None:
        copied["text"] = text

    monkeypatch.setattr("f2clipboard.codex_task.clipboard.copy", fake_copy)
    codex_task_command("http://task", copy_to_clipboard=False)
    out = capsys.readouterr().out
    assert "MD" in out
    assert not copied


def test_codex_task_command_overrides_threshold(monkeypatch, capsys):
    async def fake_process(url: str, settings: Settings) -> str:
        return str(settings.log_size_threshold)

    monkeypatch.setattr("f2clipboard.codex_task._process_task", fake_process)
    codex_task_command("http://task", copy_to_clipboard=False, log_size_threshold=1234)
    out = capsys.readouterr().out
    assert "1234" in out


def test_codex_task_command_initialises_settings_once(monkeypatch):
    calls: list[int | None] = []

    class DummySettings:
        def __init__(self, LOG_SIZE_THRESHOLD: int = 150_000):
            calls.append(LOG_SIZE_THRESHOLD)
            self.log_size_threshold = LOG_SIZE_THRESHOLD

    async def fake_process(url: str, settings: DummySettings) -> str:
        return ""

    monkeypatch.setattr("f2clipboard.codex_task.Settings", DummySettings)
    monkeypatch.setattr("f2clipboard.codex_task._process_task", fake_process)

    codex_task_command("http://task", copy_to_clipboard=False, log_size_threshold=5)
    assert calls == [5]


@pytest.mark.vcr()
def test_fetch_task_html_records_example():
    html = asyncio.run(_fetch_task_html("https://example.com"))
    assert "Example Domain" in html


def test_fetch_task_html_uses_playwright(monkeypatch):
    class DummyPage:
        async def goto(self, url: str) -> None:  # pragma: no cover - trivial
            self.url = url

        async def content(self) -> str:
            return "<html>private</html>"

    class DummyContext:
        async def add_cookies(self, cookies):  # pragma: no cover - trivial
            self.cookies = cookies

        async def new_page(self) -> DummyPage:
            return DummyPage()

    class DummyBrowser:
        async def new_context(self) -> DummyContext:
            return DummyContext()

        async def close(self) -> None:  # pragma: no cover - trivial
            pass

    class DummyPW:
        def __init__(self) -> None:  # pragma: no cover - trivial
            self.chromium = self

        async def launch(self, headless: bool = True) -> DummyBrowser:
            return DummyBrowser()

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            pass

    def fake_async_playwright():
        return DummyPW()

    monkeypatch.setattr(
        "f2clipboard.codex_task.async_playwright", fake_async_playwright
    )
    html = asyncio.run(_fetch_task_html("https://example.com/task", cookie="secret"))
    assert "private" in html
