import argparse
import fnmatch
import os
import shutil

import clipboard

# Add common image and binary file extensions to exclude
EXCLUDED_EXTENSIONS = {
    # Images
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".webp",
    ".ico",
    ".svg",
    # Other binary files
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    # Video
    ".mp4",
    ".avi",
    ".mov",
    ".wmv",
    ".flv",
    ".mkv",
    # Audio
    ".mp3",
    ".wav",
    ".ogg",
    ".m4a",
    ".flac",
    # Font files
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    # Binary executables
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    # Design files
    ".psd",
    ".ai",
    ".sketch",
}


def parse_gitignore(gitignore_path=".gitignore"):
    """Parse the .gitignore file and return a list of patterns, including '.git' always."""
    patterns = [".git"]  # Always ignore .git directory
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as file:
            lines = file.readlines()

        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                patterns.append(stripped)
    return patterns


def is_binary_or_image_file(filename):
    """Check if the file has an excluded extension."""
    return any(filename.lower().endswith(ext) for ext in EXCLUDED_EXTENSIONS)


def expand_pattern(pattern):
    """Expand brace patterns like *.{py,js} into a list of patterns like [*.py, *.js]."""
    if "{" not in pattern or "}" not in pattern:
        return [pattern]

    prefix = pattern[: pattern.find("{")]
    suffix = pattern[pattern.find("}") + 1 :]
    options = [
        opt.strip()
        for opt in pattern[pattern.find("{") + 1 : pattern.find("}")].split(",")
    ]
    return [f"{prefix}{opt}{suffix}" for opt in options]


def list_files(directory, pattern="*", ignore_patterns=[]):
    """Recursively list files in a directory matching the pattern, skipping ignored and binary/image files."""
    # Expand brace patterns into multiple patterns
    patterns = expand_pattern(pattern)

    for root, dirs, files in os.walk(directory):
        # Skip directories in ignore patterns
        dirs[:] = [
            d
            for d in dirs
            if not any(
                fnmatch.fnmatch(os.path.join(root, d), os.path.join(root, pat))
                for pat in ignore_patterns
            )
        ]

        for basename in files:
            filename = os.path.join(root, basename)

            # Skip files that match ignore patterns
            if any(
                fnmatch.fnmatch(filename, os.path.join(root, pat))
                for pat in ignore_patterns
            ):
                continue

            # Skip binary/image files
            if is_binary_or_image_file(basename):
                continue

            # Match if the file matches any of the expanded patterns
            if any(fnmatch.fnmatch(basename, pat) for pat in patterns):
                yield filename


def select_files(files):
    """Display files in a multi-column format and let the user select files to add to the copy list."""
    files = list(files)  # Convert generator to list
    if not files:
        print(
            "\n⚠️ No suitable files found. Note: Binary and image files are automatically excluded."
        )
        return []

    selected_files = []
    term_width = shutil.get_terminal_size().columns
    max_filename_length = max(len(os.path.basename(file)) for file in files) + 5
    files_per_row = max(1, term_width // max_filename_length)

    print("\n🌟 Welcome to the File to Clipboard Wizard! 🌟")
    print("👉 Please select files to add to your copy list (type 'done' to finish):")
    print("📝 Note: Binary and image files are automatically excluded.")

    for i, file in enumerate(files, 1):
        file_display = f"{i}. {os.path.basename(file):<{max_filename_length}}"
        end_char = "\n" if i % files_per_row == 0 or i == len(files) else ""
        print(file_display, end=end_char)

    print(
        "\n📝 You can enter multiple file numbers separated by commas (e.g., 1, 4, 5)."
    )

    while True:
        choice = input(
            "\n🔍 Enter file numbers to add, 'list' to review, or 'done' to finalize: "
        )
        if choice.lower() == "done":
            break
        elif choice.lower() == "list":
            print("\n📋 Current copy list:")
            for file in selected_files:
                print(f"  {os.path.basename(file)}")
        else:
            try:
                indices = [
                    int(x.strip()) - 1 for x in choice.split(",") if x.strip().isdigit()
                ]
                for index in indices:
                    if 0 <= index < len(files):
                        selected_file = files[index]
                        if selected_file not in selected_files:
                            selected_files.append(selected_file)
                            print(f"✅ Added {selected_file} to copy list.")
                        else:
                            print(f"❗ {selected_file} already in copy list.")
                    else:
                        print("❌ One or more invalid file numbers provided.")
            except ValueError:
                print("❌ Please enter valid numbers separated by commas.")

    return selected_files


def format_files_for_clipboard(files, directory, ignore_patterns):
    """Format file paths and contents for clipboard in Markdown format."""
    result = "^^^\n"

    # Add checkbox section showing project structure and selected files
    result += "## Project Structure\n\n"
    for root, dirs, file_list in os.walk(directory):
        dirs[:] = [
            d
            for d in dirs
            if not any(
                fnmatch.fnmatch(os.path.join(root, d), os.path.join(root, pat))
                for pat in ignore_patterns
            )
        ]
        level = root.replace(directory, "").count(os.sep)
        indent = " " * 4 * (level)
        relative_root = os.path.relpath(root, directory)
        if relative_root == ".":
            result += f'{indent}- {os.path.basename(directory) or "."}\n'
        else:
            result += f"{indent}- {relative_root}\n"
        subindent = " " * 4 * (level + 1)
        for f in file_list:
            if is_binary_or_image_file(f):
                continue
            relative_path = os.path.relpath(os.path.join(root, f), directory)
            if not any(fnmatch.fnmatch(relative_path, pat) for pat in ignore_patterns):
                if os.path.join(root, f) in files:
                    result += f"{subindent}- [x] {f}\n"
                else:
                    result += f"{subindent}- [ ] {f}\n"

    result += "\n## Selected Files\n\n"
    for file in files:
        relative_path = os.path.relpath(file, directory)
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            result += f"{relative_path}:\n\n```\n{content}\n```\n\n"
        except UnicodeDecodeError:
            result += f"{relative_path}:\n\n```\n[ERROR: Could not decode file contents]\n```\n\n"
        except Exception as e:
            result += f"{relative_path}:\n\n```\n[ERROR: {e}]\n```\n\n"
    result += "^^^\n"
    return result


def build_parser():
    parser = argparse.ArgumentParser(
        description="Copy selected files to the clipboard in Markdown format."
    )
    parser.add_argument(
        "--dir",
        default=".",
        help="Directory to search for files (default: current directory)",
    )
    parser.add_argument(
        "--pattern", default="*", help="File glob pattern to match (e.g. *.py or *.py)"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional glob patterns to ignore (may be repeated)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print formatted Markdown instead of copying to clipboard",
    )
    parser.add_argument(
        "--output",
        help="Write formatted Markdown to this file",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    directory = args.dir
    pattern = args.pattern
    ignore_patterns = parse_gitignore()
    if args.exclude:
        ignore_patterns.extend(args.exclude)
    files = list_files(directory, pattern, ignore_patterns)
    selected_files = select_files(files)

    if selected_files:
        clipboard_content = format_files_for_clipboard(
            selected_files, directory, ignore_patterns
        )
        if args.output:
            with open(args.output, "w") as fh:
                fh.write(clipboard_content)
        if args.dry_run:
            print(clipboard_content)
        else:
            clipboard.copy(clipboard_content)
            print(
                "🚀 The formatted files have been copied to your clipboard. Ready to paste!"
            )
    else:
        print("🚫 No files selected.")


if __name__ == "__main__":
    main()
