import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from f2clipboard import (
    parse_gitignore,
    is_binary_or_image_file,
    list_files,
    format_files_for_clipboard,
    EXCLUDED_EXTENSIONS
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
    assert len(all_files) == 3  # Should find .gitignore, file1.txt and file2.py
    assert any(f.endswith(".gitignore") for f in all_files)
    assert any(f.endswith("file1.txt") for f in all_files)
    assert any(f.endswith("file2.py") for f in all_files)
    
    # Test specific pattern
    txt_files = list(list_files(temp_directory, "*.txt", []))
    assert len(txt_files) == 1
    assert txt_files[0].endswith("file1.txt")
    
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
        os.path.join(temp_directory, "src/file2.py")
    ]
    ignore_patterns = parse_gitignore(os.path.join(temp_directory, ".gitignore"))
    
    result = format_files_for_clipboard(selected_files, temp_directory, ignore_patterns)
    
    # Check structure markers
    assert result.startswith("^^^")
    assert result.endswith("^^^\n")
    
    # Check project structure section
    assert "## Project Structure" in result
    assert "- [x] file1.txt" in result  # Root level file
    assert "- [ ] file2.py" in result   # File in src directory
    assert "- src" in result            # Check directory structure
    
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

@patch('builtins.input')
@patch('clipboard.copy')
def test_main_workflow(mock_clipboard, mock_input, temp_directory):
    """Test the main workflow with mocked inputs."""
    # Mock user inputs
    mock_input.side_effect = [
        temp_directory,  # directory path
        "*.txt",        # file pattern
        "1",           # select first file
        "done"         # finish selection
    ]
    
    # Import main function only when needed to avoid immediate execution
    from f2clipboard import main
    
    # Run main function
    with patch('sys.stdout'):  # Suppress print statements
        main()
    
    # Verify clipboard was called
    assert mock_clipboard.called
    clipboard_content = mock_clipboard.call_args[0][0]
    assert "## Project Structure" in clipboard_content
    assert "## Selected Files" in clipboard_content