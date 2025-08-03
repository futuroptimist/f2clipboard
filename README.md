# f2clipboard v2 – "flows to clipboard"

[![CI](https://github.com/futuroptimist/f2clipboard/actions/workflows/lint-test.yml/badge.svg)](https://github.com/futuroptimist/f2clipboard/actions/workflows/lint-test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Problem
Repetitive web-based engineering chores (triaging CI failures, gathering logs, summarising errors) steal focus and time. Existing tooling (e.g. OpenAI Operator) is deprecated or proprietary.

## Vision
A single CLI command
```bash
f2clipboard codex-task https://chatgpt.com/codex/tasks/task_123…
```
should:

Parse the Codex task page (authenticated session or scraped HTML via Playwright).

Locate the linked GitHub PR (“View PR” button).

Query the GitHub API for the check-suite:

For every failed check → download full raw logs.

For every successful check → ignore.

If a log exceeds 150 kB → invoke an LLM (configurable, OpenAI or Anthropic) to summarise the failure.

Emit a Markdown snippet ready for pasting back into Codex:

Each failed check becomes a fenced code-block labelled with job name & link.

Oversized logs are replaced by the summary plus a collapsible <details> section with the first 100 lines for context.

The original local file workflow is still available via the `files` command:

```bash
f2clipboard files --dir path/to/project
```

## Roadmap
### M0 (bootstrap)
- [x] Ship basic CLI with `codex-task` command and help text.
- [x] Support GitHub personal-access tokens via `.env`.
- [x] Fetch PR URL from Codex task HTML (unauthenticated test page).

### M1 (minimum lovable product)
- [ ] Parse check-suites with GitHub REST v3.
- [ ] Download raw logs; gzip-decode when necessary.
- [ ] Size-gate logs → summarise via LLM.
- [ ] Write Markdown artefact to `stdout` **and** clipboard.

### M2 (hardening)
- [ ] Playwright headless login for private Codex tasks.
- [ ] Secret scanning & redaction (via `talisman` or custom regex).
- [ ] Unit tests (pytest + `pytest-recording` vcr).

### M3 (extensibility)
- [ ] Plugin interface (`entry_points = "f2clipboard.plugins"`).
- [ ] First plugin: Jira ticket summariser.
- [ ] VS Code task provider / GitHub Action marketplace listing.

## Getting Started

```bash
git clone https://github.com/futuroptimist/f2clipboard
cd f2clipboard
pip install -e ".[dev]"
cp .env.example .env  # fill in your tokens
```

Generate a Markdown snippet for a Codex task:

```bash
f2clipboard codex-task https://chatgpt.com/codex/tasks/task_123
```

Copy selected files from a local repository:

```bash
f2clipboard files --dir path/to/project
```

## Contributing

See [AGENTS.md](AGENTS.md) for LLM-specific guidelines and [CONTRIBUTING.md](CONTRIBUTING.md) for the standard contribution workflow. Prompt templates live in [docs/prompts-codex.md](docs/prompts-codex.md).
