from pathlib import Path

import yaml


def test_dependabot_pilot_scope_and_limits():
    config = yaml.safe_load(Path(".github/dependabot.yml").read_text())

    assert config["version"] == 2
    updates = config["updates"]
    assert len(updates) == 2
    assert {entry["package-ecosystem"] for entry in updates} == {
        "pip",
        "github-actions",
    }
    for entry in updates:
        assert entry["directory"] == "/"
        assert entry["schedule"]["interval"] == "weekly"
        assert entry["open-pull-requests-limit"] == 2
