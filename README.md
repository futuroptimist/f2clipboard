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

Normalise the PR link by dropping any query parameters or fragments before
calling the GitHub API.

Query the GitHub API for the check-suite:

For every failed check → download full raw logs.

For every successful check → ignore.

If a log exceeds 150 kB → invoke an LLM (configurable, OpenAI or Anthropic) to summarise the failure.

Secrets such as API tokens are redacted from logs before summarisation or output.

Emit a Markdown snippet ready for pasting back into Codex:

Each failed check becomes a fenced code-block labelled with job name & link.

Oversized logs are replaced by the summary plus a collapsible <details> section with the first 100 lines for context.

The original local file workflow is still available via the `files` command:

```bash
f2clipboard files --dir path/to/project
```

## Roadmap
### M0 (bootstrap)
- [x] Ship basic CLI with `codex-task` command and help text. 💯
- [x] Support GitHub personal-access tokens via `.env`. 💯
- [x] Fetch PR URL from Codex task HTML (unauthenticated test page). 💯

### M1 (minimum lovable product)
- [x] Parse check-suites with GitHub REST v3. 💯
- [x] Download raw logs; gzip-decode when necessary. 💯
- [x] Size-gate logs → summarise via LLM. 💯
- [x] Write Markdown artefact to `stdout` **and** clipboard. 💯

### M2 (hardening)
- [x] Playwright headless login for private Codex tasks. 💯
- [x] Unit tests (pytest + `pytest-recording` vcr). 💯
- [x] Secret scanning & redaction (via custom regex; GitHub
  `ghp_`/`gho_`/`ghu_`/`ghs_`/`ghr_`/`github_pat_`, OpenAI `sk-`, Slack `xoxb-`,
  and `Bearer` tokens) while preserving whitespace around `=` and `:`. 💯
- [x] AWS access key redaction. 💯

### M3 (extensibility)
- [x] Plugin interface (`entry_points = "f2clipboard.plugins"`). 💯
- [x] First plugin: Jira ticket summariser. 💯
- [x] VS Code task provider / GitHub Action marketplace listing. 💯
- [x] CLI command to list registered plugins. 💯

### M4 (quality of life)
- [x] Support excluding file patterns in `files` command via `--exclude`. 💯

## Getting Started

```bash
git clone https://github.com/futuroptimist/f2clipboard
cd f2clipboard
pip install -e ".[dev]"
cp .env.example .env  # fill in your tokens
# Set GITHUB_TOKEN to authenticate GitHub API requests
# Set OPENAI_API_KEY or ANTHROPIC_API_KEY for log summarisation
# Set CODEX_COOKIE to access private Codex tasks
```

Generate a Markdown snippet for a Codex task:

```bash
f2clipboard codex-task https://chatgpt.com/codex/tasks/task_123
```

The resulting Markdown is printed to your terminal and copied to the clipboard.
For a list of available options, run ``f2clipboard codex-task --help``.
To skip copying to the clipboard, pass ``--no-clipboard``:

```bash
f2clipboard codex-task https://chatgpt.com/codex/tasks/task_123 --no-clipboard
```

Adjust the log size threshold for summarisation with ``--log-size-threshold``:

```bash
f2clipboard codex-task https://chatgpt.com/codex/tasks/task_123 --log-size-threshold 200000
```

The default threshold can also be set via the ``LOG_SIZE_THRESHOLD`` environment variable in
your ``.env`` file.

Generate a prompt that reads a shared chat transcript and implements any code or configuration
changes it mentions:

```bash
f2clipboard chat2prompt https://chatgpt.com/share/abcdefg
```

HTML tags are stripped and block-level elements become newlines to preserve chat formatting.

Specify a different platform with ``--platform``:

```bash
f2clipboard chat2prompt https://chatgpt.com/share/abcdefg --platform anthropic
```

Copy selected files from a local repository:

```bash
f2clipboard files --dir path/to/project
```

Exclude glob patterns by repeating `--exclude`:

```bash
f2clipboard files --dir path/to/project --exclude 'node_modules/*' --exclude '*.log'
```

Check the installed version:

```bash
f2clipboard --version
```

## GitHub Action

Run `f2clipboard` inside GitHub Actions using the bundled composite action:

```yaml
- uses: futuroptimist/f2clipboard@v1
  with:
    args: codex-task https://chatgpt.com/codex/tasks/task_123 --no-clipboard
```

Pass any CLI arguments via `args`; the default is `--help`.

## Plugins

f2clipboard loads plugins registered under the `f2clipboard.plugins` entry-point group. A plugin
exposes a callable that receives the Typer app and can register additional commands.

```toml
[project.entry-points."f2clipboard.plugins"]
hello = "my_package.plugin:register"
```

List installed plugins:

```bash
f2clipboard plugins
```

The first bundled plugin summarises Jira issues:

```bash
f2clipboard jira path/to/issue.json
```

Provide either a Jira issue URL or a path to a JSON export. The ticket's description is summarised
and copied to your clipboard.

## Contributing

See [AGENTS.md](AGENTS.md) for LLM-specific guidelines and [CONTRIBUTING.md](CONTRIBUTING.md) for the standard contribution workflow. Prompt templates live in [docs/prompts-codex.md](docs/prompts-codex.md).
