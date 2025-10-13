---
title: 'Codex Polish Prompt'
slug: 'codex-polish'
---

Copy one of the prompts below into Codex.

## Prompt

```
SYSTEM:
You are an automated contributor for the futuroptimist/f2clipboard repository. Obey all guidance in
AGENTS.md and README.md. Keep changes small, polish-focused, and well-tested.

USER:
You are scoping a polish initiative that sharpens CLI ergonomics, enables a plugin ecosystem, and
hardens security for f2clipboard. Produce a Markdown plan with the following sections and details:

1. Snapshot
   - Enumerate the active CLI entry points: `f2clipboard.cli:app` (Typer root), the legacy
     `f2clipboard.py` shim surfaced by `files`, and helper flows such as `f2clipboard.codex_task`.
     Capture their current flag surfaces and call out any parity gaps between `codex-task` and
     `files` help output.
   - Outline the planned plugin interface under the future `f2clipboard.plugins` namespace, using a
     discovery registry (Python entry points named `f2clipboard.plugins`). Document expected hooks
     like `register_cli(app)` and `provide_clipboard(settings)`, how configuration is injected, and
     isolation guardrails.
   - Itemise token usage across the project—`GITHUB_TOKEN` for GitHub automation plus either
     `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` for LLM access. Map which modules consume each token and
     call out required opt-in configuration.
   - Summarise the testing and coverage posture: current `pytest -q` baseline, desired
     `pytest --cov` target once instrumentation lands, and the highest-value smoke suites (CLI
     invocation, plugin loading, clipboard providers).

2. Refactors
   - Describe the desired package layout split: CLI glue in `f2clipboard/cli/` exporting `app`, core
     logic in `f2clipboard/core/`, and optional integrations within `f2clipboard/plugins/<name>/`
     plus lightweight registries.
   - Define a `ClipboardProvider` protocol exposing `read()` and `write(markdown: str)` with
     capability flags. Specify backends for Darwin (`pbcopy`), X11 (`xclip`), Wayland (`wl-copy`),
     and Windows (`win32`), followed by a pure-Python fallback. Include an ordered resolution
     strategy and note smoke tests that skip when system tooling is absent.
   - Introduce a structured error hierarchy in `f2clipboard.core.errors` (e.g., `ClipboardError`,
     `PluginLoadError`, `TokenError`) and a JSON-serialisable `Result` dataclass carrying `status`,
     `summary`, and `actions`. Ensure commands can emit this payload when `--json` is passed or when
     stdout is piped.

3. Security
   - Centralise secret redaction in a reusable utility that wraps logging, summarisation, and CLI
     output. Blocklist token patterns, credentialled URLs, and SSH material.
   - Build exhaustive fixture-driven test vectors proving that secrets never appear in console
     output, Markdown summaries, or generated diffs.
   - Guarantee that LLM-facing summaries apply the redactor, asserting sanitized transcripts during
     tests so tokens cannot leak.

4. Docs & DX
   - Provide side-by-side command examples for `f2clipboard codex-task ...` and `f2clipboard files
     ...`, including piping JSON output into other tools.
   - Outline a plugin authoring guide (to live under `docs/plugins/`) covering discovery metadata,
     lifecycle hooks, testing strategies, and PyPI distribution.
   - Document the `pipx install f2clipboard` workflow, cache location, and upgrade/uninstall steps.
   - Ship shell completion scripts (Bash, Zsh, Fish) via `f2clipboard cli install-completion` and
     explain activation steps in README.

5. Orthogonality guide
   - List criteria for when to choose a polish task (e.g., ergonomic gaps in the CLI, plugin API
     scaffolding, lagging security guardrails, documentation debt on weekly workflows).
   - Contrast with feature/fix work that introduces new surfaces or addresses a repro with failing
     tests.

OUTPUT:
Return the Markdown polish plan only.
```

## Upgrade Prompt

```
SYSTEM:
You are reviewing the "Prompt" section of docs/prompts/codex/polish.md for futuroptimist/
f2clipboard. Obey AGENTS.md and repository conventions.

USER:
Analyse the existing polish prompt above and propose an improved replacement. Preserve the same two
section headings (Prompt, Upgrade Prompt) and keep all information requirements intact, but enhance
clarity, concision, and actionability. Call out any missing safeguards or tests that should be added
while staying within polish scope.

OUTPUT:
Return the revised prompt text, ready to replace the original "Prompt" block.
```
