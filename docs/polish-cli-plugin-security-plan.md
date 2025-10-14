# CLI & Plugin Polish Initiative Plan

## 1. Snapshot

### Active CLI entry points
- `f2clipboard.cli:app` – Typer root that registers the current subcommands: `codex-task`,
  `chat2prompt`, `files`, `merge-checks`, `merge-resolve`, and `plugins`. Global flag surface is
  limited to `--version` via the callback.
- Legacy `f2clipboard.py` – argparse shim that powers the Typer `files` command by proxy. It exposes
  `--dir`, `--pattern`, `--include`, `--exclude`, `--dry-run`, `--all`, `--output`, and `--max-size`.
  Help text highlights Markdown clipboard export and interactive selection.
- Helper flows inside the package:
  - `f2clipboard.codex_task` (`codex-task` command): takes a positional Codex task URL plus
    `--clipboard/--no-clipboard`, `--log-size-threshold`, `--openai-model`, and `--anthropic-model`
    overrides.
  - `f2clipboard.files` (`files` command wrapper): Typer-facing options mirror the legacy parser but
    rely on `--dry-run`/`--output` instead of a `--no-clipboard` toggle. This is the primary parity
    gap versus `codex-task`, which presents an explicit clipboard flag pair in its help output.
  - `f2clipboard.chat2prompt`, `merge_checks`, and `merge_resolve` surface additional flows that are
    callable via the Typer root yet not part of the original legacy shim.

### Planned plugin interface (`f2clipboard.plugins`)
- Discovery performed through Python entry points named `f2clipboard.plugins`; each entry provides a
  module-level factory returning a plugin object.
- Expected hooks:
  - `register_cli(app: typer.Typer)` – add commands/flags to the shared Typer application without
    mutating global state outside the provided handle.
  - `provide_clipboard(settings: Settings) -> ClipboardProvider` – optionally expose clipboard
    backends or enrich existing providers.
  - Optional lifecycle hooks (`configure(settings)`, `shutdown()`) to give plugins structured
    extension points.
- Configuration injection: the core app instantiates a `Settings` object and passes immutable views
  into hooks. Plugin-specific config is drawn from `[tool.f2clipboard.plugins.<name>]` in
  `pyproject.toml` or namespaced environment variables and delivered as keyword arguments by the
  registry.
- Isolation guardrails:
  - Plugins execute inside try/except wrappers; failures raise `PluginLoadError` without crashing the
    CLI.
  - Each plugin runs with a dedicated logger carrying the plugin name and redaction filters.
  - Clipboard providers supplied by plugins are wrapped in sandbox adapters that enforce timeouts and
    resource limits before the core command consumes them.

### Token usage map
- `GITHUB_TOKEN`
  - Consumed by `f2clipboard.codex_task` when calling the REST API for check runs and by
    `f2clipboard.merge_resolve` to fetch PR metadata and post summary comments.
  - Must be explicitly opted in via environment or `.env`; absent tokens skip authenticated calls and
    emit warnings instead of failing.
- `OPENAI_API_KEY` / `OPENAI_MODEL`
  - Read by `f2clipboard.config.Settings` and used inside `f2clipboard.llm` for log summarisation,
    merge-conflict patch suggestions, and Jira plugin summaries.
  - `merge_resolve` also inspects the key to decide whether to attempt automated conflict patches.
  - Disabled by default; behaviour gracefully falls back to truncation when the key is missing.
- `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL`
  - Mirror the OpenAI usage across `Settings`, `llm`, and `merge_resolve` as an alternative LLM.
  - Plugins can rely on the same config surface; they must tolerate `None` keys and skip remote
    requests unless the user opts in.

### Testing & coverage posture
- Current baseline: `pytest -q` runs the unit suite (CLI invocations, Codex workflow, plugins, merge
  utilities, and secret redaction).
- Target posture: instrument `pytest --cov=f2clipboard --cov-report=term-missing` and wire coverage
  upload into CI once the core refactors land.
- High-value smoke suites to keep green:
  - CLI invocation matrix covering `codex-task`, `files`, `merge-checks`, `merge-resolve`, and future
    plugin commands.
  - Plugin discovery and failure-handling tests ensuring registry resilience.
  - Clipboard provider contract checks (system tools mocked or skipped when binaries are missing).

## 2. Refactors

### Package layout split
- Relocate Typer bootstrap code to `f2clipboard/cli/__init__.py` exporting `app` and
  `main(argv: list[str] | None)`. Keep command modules as siblings under `f2clipboard/cli/commands/`
  to clarify boundaries.
- Move shared logic (GitHub clients, HTML parsing, LLM orchestration, redaction utilities) into
  `f2clipboard/core/` modules, enabling reuse across CLI and plugins.
- House optional integrations under `f2clipboard/plugins/<name>/` with a thin registry orchestrating
  entry-point loading, metadata (version/path), and optional capability flags.

### Clipboard provider protocol
- Define `ClipboardProvider` in `f2clipboard/core/clipboard.py` with:
  - `read() -> str` and `write(markdown: str) -> None` methods.
  - Capability flags (`supports_rich_text`, `supports_files`) exposed as properties or attributes.
- Backend implementations:
  1. Darwin: shell out to `pbcopy`/`pbpaste`.
  2. X11: use `xclip -selection clipboard`.
  3. Wayland: fall back to `wl-copy`/`wl-paste`.
  4. Windows: wrap `ctypes` `OpenClipboard`/`SetClipboardData` or `pyperclip` with Windows backend.
  5. Pure-Python fallback leveraging `pyperclip` with in-memory store for headless environments.
- Resolution strategy: detect OS, probe availability of system binaries, then cascade through the
  provider list until one succeeds; cache the winning provider per session.
- Smoke tests: mark platform-specific tests with `pytest.mark.skipif` when commands or OS support are
  absent; add fallback-only tests to ensure default behaviour remains stable.

### Structured error model
- Create `f2clipboard/core/errors.py` defining:
  - `F2ClipboardError` base class.
  - `ClipboardError`, `PluginLoadError`, `TokenError`, and contextual subclasses used across core and
    CLI.
- Introduce a JSON-friendly `Result` dataclass (`status`, `summary`, `actions`) located in
  `f2clipboard/core/result.py`. Commands emit this payload when `--json` is passed or stdout is
  redirected, while preserving human-readable output otherwise.
- Update CLI commands to catch domain exceptions, populate `Result`, and exit with structured
  messages for automation consumers.

## 3. Security

- Centralise secret redaction in `f2clipboard/core/redaction.py`, exposing helpers to scrub strings
  before logging, summarisation, or CLI printing. Maintain blocklists for PATs, bearer tokens,
  credentialed URLs, SSH keys, and plugin-declared secret patterns.
- Expand tests with fixture-driven cases that feed sample logs, Markdown summaries, PR comments, and
  diff payloads through the redactor, asserting zero leakage in console output or returned data.
- Guarantee that all LLM-bound text (summaries, patch prompts, plugin payloads) flows through the
  redactor and add assertions verifying sanitised transcripts during tests.

## 4. Docs & DX

- Publish parallel usage snippets comparing `f2clipboard codex-task …` and `f2clipboard files …`,
  including examples that pipe `--json` responses into utilities like `jq` once the structured result
  format lands.
- Author `docs/plugins/authoring.md` describing entry-point metadata, lifecycle hooks, sample tests,
  and publishing tips (PyPI classifiers, semantic versioning, changelog expectations).
- Document `pipx install f2clipboard` in README: installation, cache directories, upgrade (`pipx
  upgrade f2clipboard`), and uninstall steps.
- Ship shell completion scripts via `f2clipboard cli install-completion` (Bash, Zsh, Fish). Add
  activation instructions to README and surface the command in `--help`.

## 5. Orthogonality guide

- Treat polish tasks as the default when addressing:
  - CLI ergonomics (missing flags, inconsistent help text, confusing defaults).
  - Plugin API scaffolding or registry hardening.
  - Security guardrails (redaction breadth, token gating).
  - Documentation or DX gaps discovered during weekly workflows.
- Reserve feature/fix work for efforts that introduce new command surfaces, add first-party plugin
  functionality, or remediate regressions validated by failing tests or bug reports.
