# Design Decisions

This repository originally exposed a single `f2clipboard.py` module that offered
a small argparse based CLI. To bootstrap the next iteration we introduced a
package under `f2clipboard/` which houses a Typer application and future
workflow modules.

The old script remains for now but is no longer imported by default. Tests were
updated to validate only the new package and CLI. `pyproject.toml` now exports
the Typer app via `f2clipboard.cli:main`.

To retain backwards compatibility, the Typer CLI exposes a `files` command that
delegates to the legacy `f2clipboard.py` script. This keeps the original
"copy local files to clipboard" workflow available alongside the new
`codex-task` experiment without a full rewrite.

Configuration is handled via a small `Settings` class that reads environment
variables from a `.env` file using the `pydantic-settings` package. The
`codex-task` command is a placeholder that will eventually scrape Codex, query
GitHub and summarise logs.
