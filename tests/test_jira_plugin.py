import json

from typer.testing import CliRunner

from f2clipboard import app
from f2clipboard.plugins.jira import register


def test_jira_plugin_from_file(tmp_path, monkeypatch):
    register(app)
    issue = {
        "fields": {
            "summary": "Test issue",
            "description": "Detailed description of issue",
        }
    }
    path = tmp_path / "issue.json"
    path.write_text(json.dumps(issue))
    monkeypatch.setattr("f2clipboard.plugins.jira.clipboard.copy", lambda _: None)

    runner = CliRunner()
    result = runner.invoke(app, ["jira", str(path)])
    assert result.exit_code == 0
    assert "Test issue" in result.stdout
