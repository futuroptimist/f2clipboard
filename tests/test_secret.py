import asyncio

from f2clipboard.codex_task import _process_task
from f2clipboard.config import Settings
from f2clipboard.secret import redact_secrets


def test_redact_secrets():
    token = "ghp_" + "a" * 36
    text = f"TOKEN=abcdef123456 {token}"
    redacted = redact_secrets(text)
    assert "abcdef123456" not in redacted
    assert "ghp_REDACTED" in redacted
    assert "TOKEN=***" in redacted


def test_process_task_redacts(monkeypatch):
    async def fake_html(url: str) -> str:
        return '<a href="https://github.com/o/r/pull/1">PR</a>'

    async def fake_runs(pr_url: str, token: str | None):
        return [{"id": 1, "name": "Job", "conclusion": "failure"}]

    async def fake_log(client, owner, repo, run_id):
        return "TOKEN=abcdef123456"

    async def fake_summary(text: str, settings: Settings) -> str:
        assert "abcdef123456" not in text
        return "SUMMARY"

    monkeypatch.setattr("f2clipboard.codex_task._fetch_task_html", fake_html)
    monkeypatch.setattr("f2clipboard.codex_task._fetch_check_runs", fake_runs)
    monkeypatch.setattr("f2clipboard.codex_task._download_log", fake_log)
    monkeypatch.setattr("f2clipboard.codex_task.summarise_log", fake_summary)

    settings = Settings()
    settings.log_size_threshold = 0
    result = asyncio.run(_process_task("http://task", settings))
    assert "abcdef123456" not in result
    assert "SUMMARY" in result
