import importlib.util
import types
from pathlib import Path

from typer.testing import CliRunner

from f2clipboard import app
from f2clipboard import files as files_module


def _load_legacy_module():
    spec = importlib.util.spec_from_file_location(
        "legacy_f2clipboard", Path(__file__).resolve().parents[1] / "f2clipboard.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_files_command_forwards_max_size(monkeypatch, tmp_path):
    called = {}

    def fake_main(argv):
        called["argv"] = argv

    class FakeLoader:
        def exec_module(self, module):
            module.main = fake_main

    class FakeSpec:
        loader = FakeLoader()

    monkeypatch.setattr(
        files_module, "spec_from_file_location", lambda name, path: FakeSpec()
    )
    monkeypatch.setattr(
        files_module, "module_from_spec", lambda spec: types.SimpleNamespace()
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["files", "--dir", str(tmp_path), "--max-size", "5"],
    )
    assert result.exit_code == 0
    assert called["argv"] == [
        "--dir",
        str(tmp_path),
        "--pattern",
        "*",
        "--max-size",
        "5",
    ]


def test_legacy_main_max_size(tmp_path, capsys):
    (tmp_path / "small.txt").write_text("a")
    (tmp_path / "large.txt").write_text("b" * 10)
    legacy = _load_legacy_module()

    legacy.main(
        [
            "--dir",
            str(tmp_path),
            "--pattern",
            "*.txt",
            "--all",
            "--dry-run",
            "--max-size",
            "5",
        ]
    )
    out = capsys.readouterr().out
    selected = out.split("## Selected Files\n", 1)[1]
    assert "small.txt" in selected
    assert "large.txt" not in selected
