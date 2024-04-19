# f2clipboard

`f2clipboard` is a Python utility that allows users to select files from a specified directory and copy their contents formatted in Markdown to the clipboard. This is especially useful for developers who need to quickly share file contents or for tasks that involve formatting file paths and contents for documentation or reporting.

## Installation

Before running `f2clipboard`, you need to install the required Python packages. This can be done via pip:

```bash
pip install clipboard
```

## Requirements

- Python 3.x
- clipboard (Python package)

## Usage

To use `f2clipboard`, follow these steps:

1. **Run the Script**: Navigate to the directory where `f2clipboard.py` is located and run:

   ```bash
   python f2clipboard.py
   ```

2. **Enter Directory Path**: When prompted, enter the path to the directory you wish to search for files. You can enter `.` to denote the current directory:

   ```plaintext
   📁 Enter the directory path to search files: .
   ```

3. **Enter File Pattern**: Specify the pattern of the files you want to search (e.g., `*.txt`). If you want to search for all files, just enter `*`:

   ```plaintext
   🔎 Enter the file pattern to search (e.g., '*.txt'): *
   ```

4. **Select Files**: You will see a list of files. Enter the numbers of the files you want to add to your clipboard, separated by commas:

   ```plaintext
   🔍 Enter file numbers to add, 'list' to review, or 'done' to finalize: 1, 4, 5
   ```

5. **Review and Finalize**: If you need to review your selection, type `list`. Once you are done selecting files, type `done` to copy the formatted content to the clipboard.

   ```plaintext
   🔍 Enter file numbers to add, 'list' to review, or 'done' to finalize: done
   ```

## Known Limitations

- The script assumes that all files are text-based and encodable in UTF-8.
- Larger files may not be efficiently handled due to clipboard size limitations.
