# f2clipboard Polish Initiative Plan

## 1. Snapshot

### CLI entry points and flag surface
- **`f2clipboard.cli:app` (Typer root)**
  - Global: `--version` eager flag from `_main` callback.
  - Commands: `codex-task`, `chat2prompt`, `files`, `merge-checks`, `merge-resolve`, `plugins`.
  - Plugin autoloading via `importlib.metadata.entry_points(group="f2clipboard.plugins")` on
    import.
- **`f2clipboard.codex_task:codex_task_command`** (`f2clipboard codex-task ...`)
  - Arguments & options: positional `url`, `--clipboard/--no-clipboard`, `--log-size-threshold`,
    `--openai-model`, `--anthropic-model` (plus environment-driven defaults through `Settings`).
  - Help highlights clipboard toggle and summarisation knobs but lacks output path controls.
- **`f2clipboard.files:files_command`** (`f2clipboard files ...` wrapping `f2clipboard.py`)
  - Options mirror the legacy argparse CLI: `--dir`, `--pattern`, repeatable `--include`/`--exclude`,
    `--max-size`, `--dry-run`, `--all`, `--output`.
  - Gap with `codex-task`: `files` help does not expose a `--clipboard` toggle (clipboard is managed
    inside the shim) and lacks JSON/summary flags; conversely `codex-task` does not offer
    `--output`/`--dry-run` parity. Consolidating shared UX (clipboard toggles, dry-run, output
    redirection) is a key polish target.
- **`f2clipboard.py` legacy shim (`python -m f2clipboard.py ...`)**
  - Maintains argparse-driven workflow with the same flags surfaced by `files_command`.
  - Handles interactive selection, Markdown formatting, clipboard copy, and optional file output.
- **Helper modules**
  - `f2clipboard.chat2prompt`, `merge_checks`, `merge_resolve` expose Typer commands attached to the
    root app; they currently rely on module-level registration without subpackages.

### Plugin interface direction (`f2clipboard.plugins`)
- Current state: `f2clipboard.__init__._load_plugins()` imports entry points named
  `f2clipboard.plugins`. Existing `plugins.jira` module registers via a `register(app)` callable.
- Planned interface:
  - Entry point target resolves to an object exposing `register_cli(app: typer.Typer) -> None` to add
    commands and sub-apps.
  - Optional `provide_clipboard(settings: Settings) -> ClipboardProvider` hook enabling pluggable
    clipboard backends (discoverable through a registry keyed by capability, e.g., `"read"`,
    `"write"`, format negotiation).
  - Configuration injection: the core will instantiate `Settings` once, redacting secrets, and pass
    a scoped view or dependency container into plugin hooks.
  - Isolation guardrails: load each plugin in a try/except sandbox, record provenance (version,
    module path), and allow `--plugins-disable <name>` overrides to short-circuit misbehaving
    integrations. Future-proof with context managers to reset Typer state on failures.

### Token usage map and opt-in configuration
- **`GITHUB_TOKEN`**
  - Consumed by `f2clipboard.codex_task` (GitHub REST calls) and `f2clipboard.merge_resolve`
    (fetching pull requests, posting resolutions). Loaded via `Settings.github_token`.
  - Optional: behaviour falls back to unauthenticated requests but rate limiting increases; plan to
    document explicit opt-in with `.env` or environment export.
- **`OPENAI_API_KEY` / `OPENAI_MODEL`**
  - Used inside `f2clipboard.llm` for log summarisation and conflict patching, indirectly exercised
    by `codex_task` and `merge_resolve` when summarisation is triggered.
  - Optional: absence triggers truncation or feature disablement. Add CLI hints and `Settings`
    validation errors only when features are explicitly requested.
- **`ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL`**
  - Same call sites as OpenAI, providing an alternative LLM backend. Mutually exclusive preference is
    inferred by checking `settings.openai_api_key` first, then Anthropics.
- **Plugin tokens**
  - `f2clipboard.plugins.jira` instantiates `Settings` but currently relies on whichever LLM key is
    configured. Plugin registry should advertise required environment variables in metadata to guide
    users toward opt-in configuration.

### Testing & coverage posture
- Current baseline: `pytest -q` covering CLI smoke tests (`tests/test_basic.py`), secret redaction,
  and merge resolution logic. No coverage instrumentation yet.
- Target: introduce `pytest --cov=f2clipboard --cov-report=xml` once packaging layout stabilises; wire
  into CI for gating.
- Highest-value smoke suites to harden:
  - CLI invocation snapshots: `f2clipboard --help`, `codex-task --help`, `files --help` verifying
    consistent option sets and JSON output when added.
  - Plugin loading: simulate entry point discovery, ensure isolation and metadata reporting.
  - Clipboard providers: capability probing, platform-conditional skips when native tooling (pbcopy,
    xclip, wl-copy, win32 APIs) is unavailable.

## 2. Refactors

### Package layout split
- Move Typer wiring into `f2clipboard/cli/` (`__init__.py` exporting `app`, submodules per command).
- Core workflows (Codex harvesting, merge helpers, summarisation, clipboard orchestration) relocate
  into `f2clipboard/core/`, emphasising pure logic with minimal IO.
- Plugins reside under `f2clipboard/plugins/<name>/`, each exposing metadata and hook functions; add
  lightweight registries (`f2clipboard/plugins/registry.py`) for discovery and lifecycle helpers.

### ClipboardProvider protocol
- Define `ClipboardProvider` (e.g., `Protocol` or `ABC`) with:
  - `read() -> str | None`
  - `write(markdown: str) -> None`
  - Capability flags such as `supports_html`, `supports_image`, `supports_read` to guide fallbacks.
- Backend matrix & resolution order:
  1. Darwin: shell out to `pbcopy`/`pbpaste`.
  2. Wayland: `wl-copy`/`wl-paste` when `$WAYLAND_DISPLAY` present.
  3. X11: `xclip` or `xsel`.
  4. Windows: `win32clipboard` via `pywin32` when available.
  5. Pure-Python fallback (current `pyperclip` or `clipboard` module) as a final option.
- Strategy: probe environment variables and command availability, log diagnostics, skip platform
  tests when tooling is missing. Provide smoke tests per backend using monkeypatched subprocess
  invocations.

### Error hierarchy & structured results
- Introduce `f2clipboard.core.errors` with base `F2ClipboardError` and specialisations:
  - `ClipboardError`, `PluginLoadError`, `TokenError`, `LLMError`, etc.
- Create `Result` dataclass (JSON-serialisable) carrying `status` (`"ok"|"error"`), `summary`, and
  optional `actions` list for follow-up steps. Commands emit this payload when `--json` is passed or
  when stdout is redirected (detect via `sys.stdout.isatty()`), while preserving friendly TTY output.
- Update Typer commands to catch domain errors, convert to structured results, and ensure exit codes
  align with status.

## 3. Security

- Centralise redaction by wrapping logging, CLI echoing, and Markdown generation with a shared
  utility (e.g., `f2clipboard.core.redaction.Redactor`) seeded with the existing `SECRET_PATTERNS`.
  Expand blocklist to cover credentialled URLs, SSH keys, and bearer tokens with heuristics.
- Add fixture-driven tests covering:
  - CLI output paths (`typer` runner captures), Markdown transcripts, and diff rendering to confirm
    secrets never surface.
  - Varied token formats (GitHub, OpenAI, OAuth, basic auth URLs, private keys) plus negative cases
    to avoid over-redaction.
- Ensure all LLM-facing messages (`summarise_log`, merge-conflict patches, plugin prompts) pass
  through the redactor and assert sanitised payloads in async tests to prevent leakage via API calls
  or saved transcripts.

## 4. Docs & Developer Experience

- Publish side-by-side command samples comparing `f2clipboard codex-task …` and `f2clipboard files …`,
  including JSON output piping once structured results land (e.g., `f2clipboard codex-task --json |
  jq '.summary'`).
- Add `docs/plugins/authoring.md` detailing entry point metadata, hook signatures, dependency
  isolation, contract tests, and packaging guidance for PyPI distribution.
- Expand README with `pipx install f2clipboard`, location of pipx-managed binaries, upgrade
  (`pipx upgrade f2clipboard`) and uninstall steps.
- Ship Typer-managed shell completions via `f2clipboard cli install-completion --shell bash|zsh|fish`
  and document activation snippets (e.g., sourcing generated files in shell profiles).

## 5. Orthogonality Guide

- Choose polish initiatives when addressing:
  - CLI ergonomics gaps (flag parity, UX consistency, completion scripts).
  - Plugin API scaffolding, discovery robustness, or metadata exposure.
  - Security guardrails such as token redaction, permission scoping, or audit logging.
  - Documentation debt that slows weekly workflows or onboarding (CLI guides, plugin docs, pipx).
- Defer to feature/fix work when introducing net-new commands, adding API integrations, or resolving
  user-reported failures with reproducible test cases that currently fail.
