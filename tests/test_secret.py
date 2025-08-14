import asyncio

import pytest

from f2clipboard.codex_task import _process_task
from f2clipboard.config import Settings
from f2clipboard.secret import redact_secrets


def test_redact_secrets():
    token = "ghp_" + "a" * 36
    openai_token = "sk-" + "b" * 48
    slack_token = "xoxb-" + "c" * 40
    text = f"TOKEN=abcdef123456 {token} {openai_token} {slack_token}"  # pragma: allowlist secret
    redacted = redact_secrets(text)
    assert "abcdef123456" not in redacted  # pragma: allowlist secret
    assert "ghp_REDACTED" in redacted
    assert "TOKEN=***" in redacted
    assert "sk-REDACTED" in redacted
    assert "xoxb-REDACTED" in redacted


def test_redact_github_pat():
    token = "github_pat_" + "c" * 50  # pragma: allowlist secret
    redacted = redact_secrets(token)
    assert "c" * 10 not in redacted  # pragma: allowlist secret
    assert "github_pat_REDACTED" in redacted


@pytest.mark.parametrize("prefix", ["gho_", "ghu_", "ghs_", "ghr_"])
def test_redact_other_github_tokens(prefix):
    token = prefix + "d" * 36  # pragma: allowlist secret
    redacted = redact_secrets(token)
    assert token not in redacted  # pragma: allowlist secret
    assert f"{prefix[:3]}_REDACTED" in redacted


def test_redact_aws_access_key():
    key = "AKIA" + "A" * 16  # pragma: allowlist secret
    redacted = redact_secrets(f"creds: {key}")
    assert key not in redacted  # pragma: allowlist secret
    assert "AKIA_REDACTED" in redacted


def test_redact_preserves_whitespace():
    text = "TOKEN = abcdef123456\napi_key:\tsecret1234"  # pragma: allowlist secret
    redacted = redact_secrets(text)
    assert "TOKEN = ***" in redacted
    assert "api_key:\t***" in redacted


def test_redact_bearer_token():
    text = "Authorization: Bearer abcdef1234567890"  # pragma: allowlist secret
    redacted = redact_secrets(text)
    assert "Bearer ***" in redacted
    assert "abcdef1234567890" not in redacted  # pragma: allowlist secret


def test_redact_other_slack_tokens():
    token = "xoxe-" + "d" * 40  # pragma: allowlist secret
    redacted = redact_secrets(token)
    assert token not in redacted  # pragma: allowlist secret
    assert "xoxe-REDACTED" in redacted


def test_redact_slack_app_token():
    token = "xapp-" + "e" * 40  # pragma: allowlist secret
    redacted = redact_secrets(token)
    assert token not in redacted  # pragma: allowlist secret
    assert "xapp-REDACTED" in redacted


def test_redact_env_token_with_special_chars():
    text = "API_TOKEN=abc/def+ghi=="  # pragma: allowlist secret
    redacted = redact_secrets(text)
    assert "abc/def+ghi==" not in redacted  # pragma: allowlist secret
    assert "API_TOKEN=***" in redacted


@pytest.mark.parametrize(
    "text, expected",
    [
        ('TOKEN="abcdef123456"', 'TOKEN="***"'),
        ("TOKEN='abcdef123456'", "TOKEN='***'"),
    ],
)
def test_redact_env_token_with_quotes(text: str, expected: str) -> None:
    redacted = redact_secrets(text)
    assert "abcdef123456" not in redacted  # pragma: allowlist secret
    assert expected in redacted


def test_process_task_redacts(monkeypatch):
    async def fake_html(url: str, cookie: str | None = None) -> str:
        return '<a href="https://github.com/o/r/pull/1">PR</a>'

    async def fake_runs(pr_url: str, token: str | None):
        return [{"id": 1, "name": "Job", "conclusion": "failure"}]

    async def fake_log(client, owner, repo, run_id):
        return "TOKEN=abcdef123456"

    async def fake_summary(text: str, settings: Settings) -> str:
        assert "abcdef123456" not in text  # pragma: allowlist secret
        return "SUMMARY"

    monkeypatch.setattr("f2clipboard.codex_task._fetch_task_html", fake_html)
    monkeypatch.setattr("f2clipboard.codex_task._fetch_check_runs", fake_runs)
    monkeypatch.setattr("f2clipboard.codex_task._download_log", fake_log)
    monkeypatch.setattr("f2clipboard.codex_task.summarise_log", fake_summary)

    settings = Settings()
    settings.log_size_threshold = 0
    result = asyncio.run(_process_task("http://task", settings))
    assert "abcdef123456" not in result  # pragma: allowlist secret
    assert "SUMMARY" in result
