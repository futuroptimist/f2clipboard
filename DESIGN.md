# Design Decisions

This repository originally exposed a single `f2clipboard.py` module that offered
a small argparse based CLI. To bootstrap the next iteration we introduced a
package under `f2clipboard/` which houses a Typer application and future
workflow modules.

The old script remains for now but is no longer imported by default. Tests were
updated to validate only the new package and CLI. `pyproject.toml` now exports
the Typer app via `f2clipboard.cli:main`.

Configuration is handled via a small `Settings` class that reads environment
variables from a `.env` file using Pydantic v2. The `codex-task` command is a
placeholder that will eventually scrape Codex, query GitHub and summarise logs.
