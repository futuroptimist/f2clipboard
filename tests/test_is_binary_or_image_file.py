from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

spec = spec_from_file_location(
    "legacy_f2clipboard", Path(__file__).resolve().parents[1] / "f2clipboard.py"
)
module = module_from_spec(spec)
spec.loader.exec_module(module)


def test_is_binary_or_image_file_identifies_heic():
    assert module.is_binary_or_image_file("photo.heic")


def test_is_binary_or_image_file_allows_text():
    assert not module.is_binary_or_image_file("notes.txt")


def test_is_binary_or_image_file_skips_ds_store():
    assert module.is_binary_or_image_file(".DS_Store")
