import shutil
import os
import fnmatch
import clipboard

def parse_gitignore(gitignore_path='.gitignore'):
    """Parse the .gitignore file and return a list of patterns, including '.git' always."""
    patterns = ['.git']  # Always ignore .git directory
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as file:
            lines = file.readlines()
        
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                patterns.append(stripped)
    return patterns

def list_files(directory, pattern='*', ignore_patterns=[]):
    """Recursively list files in a directory matching the pattern, skipping ignored patterns."""
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(os.path.join(root, d), os.path.join(root, pat)) for pat in ignore_patterns)]
        for basename in files:
            filename = os.path.join(root, basename)
            if fnmatch.fnmatch(basename, pattern) and not any(fnmatch.fnmatch(filename, os.path.join(root, pat)) for pat in ignore_patterns):
                yield filename

def select_files(files):
    """Display files in a multi-column format and let the user select files to add to the copy list."""
    selected_files = []
    term_width = shutil.get_terminal_size().columns
    max_filename_length = max(len(os.path.basename(file)) for file in files) + 5
    files_per_row = term_width // max_filename_length

    print("\n🌟 Welcome to the File to Clipboard Wizard! 🌟")
    print("👉 Please select files to add to your copy list (type 'done' to finish):")

    for i, file in enumerate(files, 1):
        file_display = f"{i}. {os.path.basename(file):<{max_filename_length}}"
        end_char = '\n' if i % files_per_row == 0 or i == len(files) else ''
        print(file_display, end=end_char)

    print("\n📝 You can enter multiple file numbers separated by commas (e.g., 1, 4, 5).")

    while True:
        choice = input("\n🔍 Enter file numbers to add, 'list' to review, or 'done' to finalize: ")
        if choice.lower() == 'done':
            break
        elif choice.lower() == 'list':
            print("\n📋 Current copy list:")
            for file in selected_files:
                print(f"  {os.path.basename(file)}")
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',') if x.strip().isdigit()]
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



def format_files_for_clipboard(files):
    """Format file paths and contents for clipboard in Markdown format."""
    result = "^^^\n"
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            result += f"{os.path.basename(file)}:\n\n```\n{content}\n```\n\n"
        except UnicodeDecodeError:
            result += f"{os.path.basename(file)}:\n\n```\n[ERROR: Could not decode file contents]\n```\n\n"
        except Exception as e:
            result += f"{os.path.basename(file)}:\n\n```\n[ERROR: {e}]\n```\n\n"
    result += "^^^\n"
    return result


def main():
    directory = input("📁 Enter the directory path to search files: ")
    pattern = input("🔎 Enter the file pattern to search (e.g., '*.txt'): ")
    ignore_patterns = parse_gitignore()
    files = list(list_files(directory, pattern, ignore_patterns))
    if not files:
        print("⚠️ No files found. Please check your directory/path or pattern.")
        return
    
    selected_files = select_files(files)
    
    if selected_files:
        clipboard_content = format_files_for_clipboard(selected_files)
        clipboard.copy(clipboard_content)
        print("🚀 The formatted files have been copied to your clipboard. Ready to paste!")
    else:
        print("🚫 No files selected.")

if __name__ == "__main__":
    main()
