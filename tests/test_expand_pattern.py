from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

spec = spec_from_file_location(
    "legacy_f2clipboard", Path(__file__).resolve().parents[1] / "f2clipboard.py"
)
module = module_from_spec(spec)
spec.loader.exec_module(module)


def test_expand_pattern_strips_whitespace():
    assert module.expand_pattern("*.{py, js}") == ["*.py", "*.js"]


def test_expand_pattern_no_braces():
    assert module.expand_pattern("*.py") == ["*.py"]


def test_expand_pattern_ignores_empty_entries():
    assert module.expand_pattern("*.{py,}") == ["*.py"]
