# CLI & Plugin Polish Initiative Plan

## 1. Snapshot

### Active CLI entry points
- `f2clipboard.cli:app` – Typer root that wires the shipped subcommands: `codex-task`, `chat2prompt`,
  `files`, `merge-checks`, `merge-resolve`, and `plugins`. The callback only exposes the global
  `--version` switch today, so every new top-level flag must be registered explicitly.
- Legacy `f2clipboard.py` – argparse shim invoked by the `files` command. It accepts `--dir`,
  `--pattern`, multiple `--include/--exclude`, `--max-size`, `--dry-run`, `--all`, and `--output`.
  Help text emphasises Markdown clipboard export and interactive selection.
- Helper flows surfaced through Typer:
  - `f2clipboard.codex_task` (`codex-task` command): positional Codex task URL plus
    `--clipboard/--no-clipboard`, `--log-size-threshold`, `--openai-model`, and `--anthropic-model`
    overrides.
  - `f2clipboard.files` (`files` command wrapper): Typer-facing options mirror the legacy parser but
    favour `--dry-run`/`--output` without exposing a `--clipboard` toggle. This is the visible parity
    gap versus `codex-task`, whose help output explicitly offers clipboard opt-out.
  - `f2clipboard.chat2prompt`, `merge_checks`, and `merge_resolve` remain callable via
    `f2clipboard.cli:app` yet never existed on the argparse shim.

### Planned plugin interface (`f2clipboard.plugins`)
- Discovery: standard Python entry points registered under the `f2clipboard.plugins` group point to
  modules inside the `f2clipboard.plugins` namespace. The loader instantiates a registry that imports
  each entry lazily and records metadata (distribution, version, path).
- Expected hooks exposed by every plugin module:
  - `register_cli(app: typer.Typer) -> None` – receive the shared Typer app to append commands and
    options without mutating unrelated globals.
  - `provide_clipboard(settings: Settings) -> ClipboardProvider | None` – optionally supply a
    clipboard backend; returning `None` signals no contribution.
  - Optional lifecycle hooks such as `configure(settings)` and `shutdown()` give structured entry and
    exit points without requiring subclass hierarchies.
- Configuration injection: the registry constructs a `Settings` instance once, then passes
  read-only views plus plugin-specific keyword arguments sourced from `[tool.f2clipboard.plugins]`
  sections in `pyproject.toml` or environment variables following the `F2CLIPBOARD_PLUGIN_<NAME>__`
  prefix. Plugins must tolerate missing keys and degrade gracefully.
- Isolation guardrails:
  - Entry loading wrapped in `try/except`, converting failures into `PluginLoadError` records while
    continuing boot.
  - Per-plugin loggers pre-configured with the central redaction filter to prevent leakage.
  - Clipboard providers executed through timeout-aware adapters so one misbehaving plugin cannot hang
    the CLI.

### Token usage map
- `GITHUB_TOKEN`
  - Consumed by `f2clipboard.codex_task` when calling the GitHub REST API for PR check runs and by
    `f2clipboard.merge_resolve` when fetching metadata or posting summaries. Absent tokens downgrade
    to unauthenticated requests with warning banners instead of fatal exits.
- `OPENAI_API_KEY` / `OPENAI_MODEL`
  - Parsed by `f2clipboard.config.Settings` and used inside `f2clipboard.llm` for log summaries,
    merge-conflict patch suggestions, and Jira plugin output. `merge_resolve` gates its automated
    patch flow on this configuration.
- `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL`
  - Parallel to the OpenAI flow across `Settings`, `llm`, and `merge_resolve`, acting as a drop-in
    alternative when Anthropic access is configured.
- Opt-in expectations: tokens are only read when present in the environment or `.env`; tests and
  runtime paths must treat `None` as the default state and prefer truncation/logging fallbacks.

### Testing & coverage posture
- Current baseline: `pytest -q` covers CLI invocation smoke tests, Codex workflow helpers, plugin
  registry behaviour, merge utilities, and redaction helpers.
- Target posture: `pytest --cov=f2clipboard --cov-report=term-missing` once coverage instrumentation
  is wired into CI.
- Highest-value smoke suites:
  - CLI invocation matrix spanning `codex-task`, `files`, `merge-checks`, `merge-resolve`, and future
    plugin commands.
  - Plugin discovery and failure-handling tests validating registry resilience.
  - Clipboard provider contract checks that skip gracefully when system binaries are absent.

## 2. Refactors

### Package layout split
- Relocate Typer bootstrap code to `f2clipboard/cli/__init__.py`, exporting `app` and
  `main(argv: list[str] | None)`. Organise command modules under `f2clipboard/cli/commands/` for
  clearer ownership boundaries.
- Move reusable logic (GitHub clients, HTML parsing, LLM orchestration, redaction utilities) into
  `f2clipboard/core/` modules to decouple CLI glue from domain behaviour.
- Host optional integrations under `f2clipboard/plugins/<name>/` with a light-weight registry that
  surfaces discovery metadata and injects lifecycle hooks.

### Clipboard provider protocol
- Introduce `ClipboardProvider` in `f2clipboard/core/clipboard.py` with:
  - `read() -> str` and `write(markdown: str) -> None` methods.
  - Capability flags (e.g., `supports_rich_text`, `supports_files`) advertised as read-only
    properties.
- Backend implementations:
  1. Darwin – shell out to `pbcopy`/`pbpaste`.
  2. X11 – call `xclip -selection clipboard`.
  3. Wayland – rely on `wl-copy`/`wl-paste`.
  4. Windows – wrap `ctypes` clipboard calls or delegate to `pyperclip`'s Windows backend.
  5. Pure-Python fallback – in-memory provider used for tests and headless runners.
- Resolution order: detect platform, probe for system binaries, then iterate through providers until
  one succeeds; cache the winner per session. Smoke tests should skip when commands are missing while
  verifying fallback correctness.

### Structured error model
- Create `f2clipboard/core/errors.py` containing:
  - `F2ClipboardError` base.
  - `ClipboardError`, `PluginLoadError`, `TokenError`, and contextual subclasses used across core and
    CLI layers.
- Add a JSON-serialisable `Result` dataclass in `f2clipboard/core/result.py` holding `status`,
  `summary`, and `actions`. Commands emit this structure when `--json` is passed or when stdout is
  detected as non-tty, otherwise retain friendly prose.
- Update CLI commands to catch domain exceptions, populate `Result`, and exit with structured
  messages for automation consumers.

## 3. Security

- Centralise secret redaction in `f2clipboard/core/redaction.py`, wrapping logging, summarisation, and
  CLI output helpers. Maintain blocklists for PATs, bearer tokens, credentialed URLs, and SSH key
  material, with plugin-provided patterns merged in.
- Build fixture-driven tests that feed representative logs, Markdown summaries, PR comments, and diff
  payloads through the redactor, asserting no secret leaks in console output or returned values.
- Ensure all LLM-bound text (summaries, patch prompts, plugin payloads) passes through the redactor
  and add assertions that sanitised transcripts reach the model layer.

## 4. Docs & DX

- Provide side-by-side command samples for `f2clipboard codex-task …` and `f2clipboard files …`,
  including piping `--json` responses into tools such as `jq` once structured output lands.
- Author a plugin guide under `docs/plugins/authoring.md` covering discovery metadata, lifecycle
  hooks, testing strategies, and PyPI distribution playbooks.
- Document the `pipx install f2clipboard` workflow in the README, detailing the pipx cache location,
  upgrade (`pipx upgrade f2clipboard`), and uninstall steps.
- Ship shell completion scripts (Bash, Zsh, Fish) via `f2clipboard cli install-completion` and note
  activation steps in the README.

## 5. Orthogonality guide

- Choose a polish task when addressing:
  - CLI ergonomics (missing flags, inconsistent help, confusing defaults).
  - Plugin API scaffolding, registry resilience, or clipboard provider coverage.
  - Security guardrails such as redaction breadth or token gating.
  - Documentation or DX gaps discovered during weekly workflows.
- Reserve feature/fix work for net-new surfaces, first-party plugin additions, or regressions proven
  by failing tests.
