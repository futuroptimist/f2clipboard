# f2clipboard

[![CI](https://github.com/futuroptimist/f2clipboard/actions/workflows/ci.yml/badge.svg)](https://github.com/futuroptimist/f2clipboard/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/futuroptimist/f2clipboard/branch/main/graph/badge.svg)](https://codecov.io/gh/futuroptimist/f2clipboard)

`f2clipboard` is a lightweight utility for copying multiple files into a single Markdown snippet. It started as a quick way to collect code for pasting into LLM conversations. The project now serves as a small sandbox for experimenting with command line tooling and automation.

This repository is intentionally minimal, but it reuses ideas from the [flywheel](https://github.com/futuroptimist/flywheel) template. If you need a more robust project skeleton with CI workflows and agent documentation, check out flywheel.

## Installation

Before running `f2clipboard`, install the package and its dependency:

```bash
pip install clipboard
pip install -e .
```

## Requirements

- Python 3.x
- clipboard (Python package)

## Usage

Quick usage with the new flag-based interface:

```bash
python -m f2clipboard --dir path/to/project --pattern "*.py"
```

You'll then be prompted to choose which files to copy.

1. **Select Files**: Enter the numbers of the files you want to add to your clipboard, separated by commas:

   ```plaintext
   🔍 Enter file numbers to add, 'list' to review, or 'done' to finalize: 1, 4, 5
   ```

2. **Review and Finalize**: If you need to review your selection, type `list`. Once you are done selecting files, type `done` to copy the formatted content to the clipboard.

   ```plaintext
   🔍 Enter file numbers to add, 'list' to review, or 'done' to finalize: done
   ```

## Known Limitations

- The script assumes that all files are text-based and encodable in UTF-8.
- Larger files may not be efficiently handled due to clipboard size limitations.

## Roadmap

The next iteration of this project will grow into a more featureful CLI application for creating **macro-based workflows**. The vision:

1. **Visual Workflow Builder** – A local web interface (inspired by tools like ComfyUI or Unreal Engine's Blueprints) will let users chain together actions. Each node in the graph will represent a simple step such as running an LLM prompt, executing a shell command, or manipulating files.
2. **LLM as a Building Block** – LLM inference will be treated as a primitive node. Workflows can mix multiple prompts with conventional scripting to automate larger tasks, similar to how Codex or Cursor orchestrate agentic flows.
3. **Configurable Port** – The interface will run on `localhost:<USER_SPECIFIED_PORT>` (default `localhost:8765`). The CLI will accept a `--port` flag so users can override this value.
4. **Flywheel Integration** – Borrow the structure and automated checks from the [flywheel](https://github.com/futuroptimist/flywheel) template so contributors can iterate quickly. This includes linting, tests, documentation validation and optional agent documentation via an `AGENTS.md` file.
5. **Extensibility** – The codebase will remain small and easy to fork. Future contributors (human or LLM) should be able to add new node types or modify the interface with minimal setup.

This roadmap is intentionally high level. The exact implementation details will be refined in future commits, but this document should provide enough context for anyone looking to contribute or experiment.

## Contributing

Please read [AGENTS.md](AGENTS.md) for guidelines on working with language models, running tests, and formatting code. The list of approved models is available in [llms.txt](llms.txt).
