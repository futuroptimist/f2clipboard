import re
import subprocess
import sys

from f2clipboard import __version__
from f2clipboard.config import Settings


def test_version_string():
    assert isinstance(__version__, str)


def test_cli_help():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "f2clipboard.cli",
            "--help",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage" in result.stdout
    assert "codex-task" in result.stdout
    assert "files" in result.stdout


def test_cli_version():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "f2clipboard.cli",
            "--version",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert __version__ in result.stdout


def test_codex_task_help():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "f2clipboard.cli",
            "codex-task",
            "--help",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    clean_output = re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", result.stdout)
    assert "Parse a Codex task page" in clean_output
    assert "--clipboard" in clean_output
    assert "--no-clipboard" in clean_output
    assert "--log-size-threshold" in clean_output


def test_settings_env(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GITHUB_TOKEN=test\nLOG_SIZE_THRESHOLD=123\nCODEX_COOKIE=cookie\n"  # pragma: allowlist secret
    )
    monkeypatch.chdir(tmp_path)
    settings = Settings()
    assert settings.github_token == "test"
    assert settings.log_size_threshold == 123
    assert settings.codex_cookie == "cookie"
