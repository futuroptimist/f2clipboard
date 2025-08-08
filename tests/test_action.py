from pathlib import Path

import yaml


def test_action_composite_runs_cli(tmp_path):
    data = yaml.safe_load(Path("action.yml").read_text())
    assert data["name"] == "f2clipboard"
    assert data["runs"]["using"] == "composite"
    steps = data["runs"]["steps"]
    assert any("pip install" in step.get("run", "") for step in steps)
    assert any("f2clipboard" in step.get("run", "") for step in steps)
