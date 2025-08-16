from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def load_module():
    spec = spec_from_file_location(
        "legacy_f2clipboard", Path(__file__).resolve().parents[1] / "f2clipboard.py"
    )
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_gitignore_strips_inline_comments(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("foo\nbar # note\nbaz\\#qux\n")
    module = load_module()
    assert module.parse_gitignore(str(gitignore)) == [".git", "foo", "bar", "baz#qux"]
