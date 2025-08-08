import subprocess
import sys

from typer.testing import CliRunner

from f2clipboard import __version__, app
from f2clipboard.config import Settings

runner = CliRunner()


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
    result = runner.invoke(app, ["codex-task", "--help"])
    assert result.exit_code == 0
    assert "Parse a Codex task page" in result.stdout
    assert "--clipboard" in result.stdout
    assert "--no-clipboard" in result.stdout
    assert "--log-size-threshold" in result.stdout


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
