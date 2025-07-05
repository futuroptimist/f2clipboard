import os
import runpy
import sys
from unittest.mock import patch

import pytest

from f2clipboard import (
    expand_pattern,
    parse_gitignore,
    select_files,
    format_files_for_clipboard,
)


def test_parse_gitignore_missing(tmp_path):
    patterns = parse_gitignore(os.path.join(tmp_path, "none"))
    assert patterns == [".git"]


@pytest.mark.parametrize(
    "pattern,expected",
    [
        ("*.{py,js}", ["*.py", "*.js"]),
        ("*.txt", ["*.txt"]),
    ],
)
def test_expand_pattern(pattern, expected):
    assert expand_pattern(pattern) == expected


@patch("shutil.get_terminal_size")
@patch("builtins.input")
def test_select_files_no_files(mock_input, mock_term_size):
    mock_term_size.return_value = os.terminal_size((80, 24))
    result = select_files([])
    assert result == []


@patch("shutil.get_terminal_size")
@patch("builtins.input")
def test_select_files_dedup_and_list(mock_input, mock_term_size, tmp_path):
    mock_term_size.return_value = os.terminal_size((80, 24))
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"
    file1.write_text("1")
    file2.write_text("2")
    mock_input.side_effect = ["1", "list", "1", "done"]
    files = [str(file1), str(file2)]
    with patch("builtins.print"):
        result = select_files(files)
    assert result == [str(file1)]


@patch("shutil.get_terminal_size")
@patch("builtins.input")
def test_select_files_invalid_input(mock_input, mock_term_size, tmp_path):
    mock_term_size.return_value = os.terminal_size((80, 24))
    file1 = tmp_path / "a.txt"
    file1.write_text("1")
    mock_input.side_effect = ["0", "oops", "done"]
    with patch("builtins.print"):
        result = select_files([str(file1)])
    assert result == []


def test_format_files_for_clipboard_exception(tmp_path):
    err_file = tmp_path / "err.txt"
    err_file.write_text("boom")

    def bad_open(*args, **kwargs):
        raise OSError("fail")

    with patch("builtins.open", side_effect=bad_open):
        result = format_files_for_clipboard([str(err_file)], str(tmp_path), [])
    assert "[ERROR:" in result


@patch("clipboard.copy")
@patch("f2clipboard.select_files", return_value=[])
def test_main_no_files(mock_select, mock_clipboard, temp_directory, capsys):
    from f2clipboard import main

    main(["--dir", temp_directory, "--pattern", "*.md"])
    captured = capsys.readouterr().out
    assert "No files selected" in captured
    mock_clipboard.assert_not_called()


@patch("clipboard.copy")
@patch("builtins.input")
def test_run_module_exec(mock_input, mock_clipboard, temp_directory):
    mock_input.side_effect = ["1", "done"]
    argv = ["f2clipboard", "--dir", temp_directory, "--pattern", "*.txt"]
    with patch.object(sys, "argv", argv):
        runpy.run_module("f2clipboard", run_name="__main__")
    assert mock_clipboard.called
