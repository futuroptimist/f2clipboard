import os
import tempfile
from unittest.mock import patch

import pytest

from f2clipboard import (
    EXCLUDED_EXTENSIONS,
    format_files_for_clipboard,
    is_binary_or_image_file,
    list_files,
    parse_gitignore,
    select_files,
)


@pytest.fixture
def temp_directory():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        os.makedirs(os.path.join(tmpdir, "src"))
        os.makedirs(os.path.join(tmpdir, "assets"))

        # Create text files
        with open(os.path.join(tmpdir, "file1.txt"), "w") as f:
            f.write("test content 1")
        with open(os.path.join(tmpdir, "src/file2.py"), "w") as f:
            f.write("test content 2")
        with open(os.path.join(tmpdir, "src/app.js"), "w") as f:
            f.write("test content 3")
        with open(os.path.join(tmpdir, "src/styles.css"), "w") as f:
            f.write("test content 4")

        # Create binary/image files
        with open(os.path.join(tmpdir, "assets/test.jpg"), "wb") as f:
            f.write(b"fake jpg content")
        with open(os.path.join(tmpdir, "assets/icon.png"), "wb") as f:
            f.write(b"fake png content")

        # Create .gitignore
        with open(os.path.join(tmpdir, ".gitignore"), "w") as f:
            f.write("*.log\nnode_modules/\n")

        yield tmpdir


def test_parse_gitignore(temp_directory):
    """Test .gitignore parsing functionality."""
    patterns = parse_gitignore(os.path.join(temp_directory, ".gitignore"))
    assert ".git" in patterns  # Should always include .git
    assert "*.log" in patterns
    assert "node_modules/" in patterns


def test_is_binary_or_image_file():
    """Test binary/image file detection."""
    assert is_binary_or_image_file("test.jpg")
    assert is_binary_or_image_file("icon.PNG")  # Test case insensitivity
    assert is_binary_or_image_file("doc.pdf")
    assert not is_binary_or_image_file("script.py")
    assert not is_binary_or_image_file("readme.md")


def test_list_files(temp_directory):
    """Test file listing with various patterns."""
    # Test all files
    all_files = list(list_files(temp_directory, "*", []))
    assert (
        len(all_files) == 5
    )  # Should find .gitignore, file1.txt, file2.py, app.js, and styles.css
    assert any(f.endswith(".gitignore") for f in all_files)
    assert any(f.endswith("file1.txt") for f in all_files)
    assert any(f.endswith("file2.py") for f in all_files)
    assert any(f.endswith("app.js") for f in all_files)
    assert any(f.endswith("styles.css") for f in all_files)

    # Test specific pattern
    txt_files = list(list_files(temp_directory, "*.txt", []))
    assert len(txt_files) == 1
    assert txt_files[0].endswith("file1.txt")

    # Test multi-pattern matching with braces
    script_files = list(list_files(temp_directory, "*.{py,js}", []))
    assert len(script_files) == 2
    assert any(f.endswith("file2.py") for f in script_files)
    assert any(f.endswith("app.js") for f in script_files)

    # Test multi-pattern matching with commas
    style_files = list(list_files(temp_directory, "*.{css,scss}", []))
    assert len(style_files) == 1
    assert style_files[0].endswith("styles.css")

    # Test with .gitignore patterns
    ignore_patterns = parse_gitignore(os.path.join(temp_directory, ".gitignore"))
    with open(os.path.join(temp_directory, "test.log"), "w") as f:
        f.write("log content")
    files_with_ignore = list(list_files(temp_directory, "*", ignore_patterns))
    assert not any(f.endswith(".log") for f in files_with_ignore)


def test_format_files_for_clipboard(temp_directory):
    """Test clipboard formatting."""
    selected_files = [
        os.path.join(temp_directory, "file1.txt"),
        os.path.join(temp_directory, "src/file2.py"),
    ]
    ignore_patterns = parse_gitignore(os.path.join(temp_directory, ".gitignore"))

    result = format_files_for_clipboard(selected_files, temp_directory, ignore_patterns)

    # Check structure markers
    assert result.startswith("^^^")
    assert result.endswith("^^^\n")

    # Check project structure section
    assert "## Project Structure" in result
    assert "- [x] file1.txt" in result  # Root level file
    # Both files are selected, so they should be marked with [x]
    assert "- [x] file2.py" in result  # File in src directory
    assert "- src" in result  # Check directory structure

    # Check file contents section
    assert "## Selected Files" in result
    assert "test content 1" in result
    assert "test content 2" in result


@pytest.mark.parametrize("extension", EXCLUDED_EXTENSIONS)
def test_excluded_extensions(extension, temp_directory):
    """Test that all excluded extensions are properly filtered."""
    test_file = os.path.join(temp_directory, f"test{extension}")
    with open(test_file, "w") as f:
        f.write("test content")

    files = list(list_files(temp_directory, "*", []))
    assert not any(f.endswith(extension) for f in files)


def test_unicode_decode_error_handling(temp_directory):
    """Test handling of files that can't be decoded as UTF-8."""
    # Create a binary file that will cause UnicodeDecodeError
    binary_file = os.path.join(temp_directory, "binary.txt")
    with open(binary_file, "wb") as f:
        f.write(b"\x80\x81\x82")  # Invalid UTF-8 bytes

    selected_files = [binary_file]
    result = format_files_for_clipboard(selected_files, temp_directory, [])
    assert "[ERROR: Could not decode file contents]" in result


@patch("builtins.input")
@patch("clipboard.copy")
def test_main_workflow(mock_clipboard, mock_input, temp_directory):
    """Test the main workflow with mocked inputs."""
    mock_input.side_effect = ["1", "done"]

    from f2clipboard import main

    with patch("sys.stdout"):
        main(["--dir", temp_directory, "--pattern", "*.txt"])

    # Verify clipboard was called
    assert mock_clipboard.called
    clipboard_content = mock_clipboard.call_args[0][0]
    assert "## Project Structure" in clipboard_content
    assert "## Selected Files" in clipboard_content


@patch("builtins.input")
@patch("clipboard.copy")
def test_main_workflow_multi_pattern(mock_clipboard, mock_input, temp_directory):
    """Test the main workflow with multi-pattern input."""
    mock_input.side_effect = ["1,2", "done"]

    from f2clipboard import main

    with patch("sys.stdout"):
        main(["--dir", temp_directory, "--pattern", "*.{py,js}"])

    # Verify clipboard was called and contains both types of files
    assert mock_clipboard.called
    clipboard_content = mock_clipboard.call_args[0][0]
    assert "## Project Structure" in clipboard_content
    assert "## Selected Files" in clipboard_content
    assert "file2.py" in clipboard_content
    assert "app.js" in clipboard_content


# New tests to improve coverage


def test_parse_gitignore_missing(tmp_path):
    """parse_gitignore should return only '.git' when file is missing."""
    missing_path = tmp_path / "missing.gitignore"
    assert parse_gitignore(str(missing_path)) == [".git"]


@patch("builtins.print")
def test_select_files_no_files(mock_print):
    """select_files should warn when no files are found."""
    assert select_files([]) == []
    mock_print.assert_any_call(
        "\n\u26a0\ufe0f No suitable files found. Note: Binary and image files are automatically excluded."
    )


@patch("builtins.input")
@patch("builtins.print")
def test_select_files_duplicate_and_list(mock_print, mock_input, tmp_path):
    """Selecting the same file twice should print a duplicate warning and list works."""
    file1 = tmp_path / "a.txt"
    file1.write_text("data")
    file2 = tmp_path / "b.txt"
    file2.write_text("data")
    mock_input.side_effect = ["1", "list", "1", "2", "done"]
    files = [str(file1), str(file2)]
    selected = select_files(files)
    assert selected == files
    # ensure list branch executed
    mock_print.assert_any_call("\n📋 Current copy list:")
    # duplicate warning should appear
    mock_print.assert_any_call(f"❗ {str(file1)} already in copy list.")


def test_format_files_for_clipboard_ioerror(tmp_path):
    """Any other exception should be captured in output."""
    good = tmp_path / "good.txt"
    good.write_text("ok")
    bad = tmp_path / "bad.txt"
    bad.write_text("oops")
    real_open = open

    def fake_open(path, *args, **kwargs):
        if path == str(bad):
            raise OSError("boom")
        return real_open(path, *args, **kwargs)

    with patch("builtins.open", side_effect=fake_open):
        result = format_files_for_clipboard([str(good), str(bad)], str(tmp_path), [])

    assert "[ERROR: boom]" in result


@patch("builtins.input", return_value="done")
@patch("builtins.print")
def test_main_no_selection(mock_print, mock_input, tmp_path):
    """When no files match, main should notify user."""
    empty_dir = tmp_path
    from f2clipboard import main

    with patch("sys.stdout"):
        main(["--dir", str(empty_dir), "--pattern", "nomatch*"])

    mock_print.assert_any_call("🚫 No files selected.")


def test_init_all():
    """Ensure __all__ exposes main."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("pkg", "__init__.py")
    pkg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pkg)
    assert "main" in pkg.__all__
