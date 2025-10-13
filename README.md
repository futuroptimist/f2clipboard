# f2clipboard v2 – "flows to clipboard"

[![Lint & Format][lint-badge]][lint-workflow]
[![Tests][tests-badge]][tests-workflow]
[![Coverage][coverage-badge]][codecov]
[![Docs][docs-badge]][docs-workflow]
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[lint-badge]: https://img.shields.io/github/actions/workflow/status/futuroptimist/f2clipboard/01-lint-format.yml?label=lint%20%26%20format
[lint-workflow]: https://github.com/futuroptimist/f2clipboard/actions/workflows/01-lint-format.yml
[tests-badge]: https://img.shields.io/github/actions/workflow/status/futuroptimist/f2clipboard/02-tests.yml?label=tests
[tests-workflow]: https://github.com/futuroptimist/f2clipboard/actions/workflows/02-tests.yml
[coverage-badge]: https://codecov.io/gh/futuroptimist/f2clipboard/branch/main/graph/badge.svg
[codecov]: https://codecov.io/gh/futuroptimist/f2clipboard
[docs-badge]: https://img.shields.io/github/actions/workflow/status/futuroptimist/f2clipboard/03-docs.yml?label=docs
[docs-workflow]: https://github.com/futuroptimist/f2clipboard/actions/workflows/03-docs.yml

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

Normalise the PR link—tolerating attribute whitespace and casing—by dropping
any query parameters, fragments or trailing slashes before calling the GitHub
API.

Query the GitHub API for the check-suite:

For checks concluding with `failure`, `timed_out`, `cancelled` or `action_required`
→ download full raw logs.

For checks concluding with `success`, `neutral`, `skipped` or any other
non-failure state → ignore.

If a log exceeds 150 kB → invoke an LLM (configurable, OpenAI or Anthropic) to summarise the failure.

Secrets such as API tokens are redacted from logs before summarisation or output,
including quoted environment values.

Emit a Markdown snippet ready for pasting back into Codex:

Each failing check becomes a level-three Markdown heading linking to the job plus a fenced
code-block of its log or summary.

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
- [x] Parse check-suites with GitHub REST v3 (API version 2022-11-28). 💯
- [x] Download raw logs; gzip-decode when necessary. 💯
- [x] Size-gate logs → summarise via LLM. 💯
- [x] Write Markdown artefact to `stdout` **and** clipboard. 💯

### M2 (hardening)
- [x] Playwright headless login for private Codex tasks. 💯
- [x] Unit tests (pytest + `pytest-recording` vcr). 💯
- [x] Secret scanning & redaction (via custom regex; GitHub `ghp_`/`gho_`/`ghu_`/`ghs_`/`ghr_`/`github_pat_`, OpenAI `sk-`, Slack `xoxb-` and `xapp-`, `Bearer` tokens, and base64-like secrets containing `+`, `/` or `=`) while preserving whitespace around `=` and `:` and supporting quoted values. 💯
- [x] AWS access key redaction. 💯

### M3 (extensibility)
- [x] Plugin interface (`entry_points = "f2clipboard.plugins"`). 💯
- [x] First plugin: Jira ticket summariser. 💯
- [x] VS Code task provider / GitHub Action marketplace listing. 💯
- [x] CLI command to list registered plugins. 💯

### M4 (quality of life)
- [x] Support excluding file patterns in `files` command via `--exclude`. 💯
- [x] Dry-run option for `files` command to print Markdown instead of copying. 💯
- [x] Save `files` command output to a file via `--output`. 💯
- [x] JSON output option for `plugins` command. 💯
- [x] YAML output option for `plugins` command. 💯
- [x] Non-interactive mode for `files` command to select all matches via `--all`. 💯
- [x] Plugin count via `plugins --count`. 💯
- [x] Show plugin versions via `plugins --versions`. 💯
- [x] Show plugin file paths via `plugins --paths`. 💯
- [x] Include additional file patterns in `files` command via `--include`. 💯
- [x] Sort plugin names via `plugins --sort`. 💯
- [x] Reverse plugin names via `plugins --reverse`. 💯
- [x] Filter plugin names via `plugins --filter`. 💯
- [x] Skip files larger than a threshold via `--max-size`. 💯

## Getting Started

```bash
git clone https://github.com/futuroptimist/f2clipboard
cd f2clipboard
pip install -e ".[dev]"
cp .env.example .env  # fill in your tokens
# Set GITHUB_TOKEN to authenticate GitHub API requests
# Whitespace-only values are ignored
# Set OPENAI_API_KEY or ANTHROPIC_API_KEY for log summarisation
# Set OPENAI_MODEL or ANTHROPIC_MODEL to choose the summarisation model
# Set CODEX_COOKIE to access private Codex tasks
```

Generate a Markdown snippet for a Codex task:

```bash
f2clipboard codex-task https://chatgpt.com/codex/tasks/task_123
```

The resulting Markdown is printed to your terminal and copied to the clipboard.
View the copied Markdown:

```bash
pbpaste                          # macOS
xclip -o -selection clipboard    # Linux
```
For a list of available options, run ``f2clipboard codex-task --help``.
To skip copying to the clipboard, pass ``--no-clipboard``:

```bash
f2clipboard codex-task https://chatgpt.com/codex/tasks/task_123 --no-clipboard
```

Override the default model with ``--openai-model`` or ``--anthropic-model``:

```bash
f2clipboard codex-task https://chatgpt.com/codex/tasks/task_123 --openai-model gpt-4o-mini
```

Adjust the log size threshold for summarisation with ``--log-size-threshold``:

```bash
f2clipboard codex-task https://chatgpt.com/codex/tasks/task_123 --log-size-threshold 200000
```

The default threshold can also be set via the ``LOG_SIZE_THRESHOLD`` environment variable in
your ``.env`` file. Set the threshold to ``0`` to disable summarisation entirely.

Generate a prompt that reads a shared chat transcript and implements any code or configuration
changes it mentions:

```bash
f2clipboard chat2prompt https://chatgpt.com/share/abcdefg
```

The prompt is copied to your clipboard by default. To skip copying, use ``--no-clipboard``:

```bash
f2clipboard chat2prompt https://chatgpt.com/share/abcdefg --no-clipboard
```

HTML tags are stripped and block-level elements (including sectioning tags such as
`<section>`, `<article>`, `<aside>`, and preformatted blocks like `<pre>` or `<blockquote>`)
become newlines to preserve chat formatting. Unordered lists are converted to `-` bullets and
ordered lists become numbered items, honouring any HTML `start` attributes.

Specify a different platform with ``--platform``:

```bash
f2clipboard chat2prompt https://chatgpt.com/share/abcdefg --platform anthropic
```

Adjust the HTTP timeout (must be > 0, default 10 seconds):

```bash
f2clipboard chat2prompt https://chatgpt.com/share/abcdefg --timeout 5
```

Copy selected files from a local repository:

```bash
f2clipboard files --dir path/to/project
```

The command skips common binary and image files (for example, `.jpg`, `.png`, `.heic`) so the
output contains only text-friendly content. It also honours patterns from `.gitignore`,
stripping any inline `#` comments. The `.gitignore` file is resolved relative to `--dir`, so you
can run the command from outside the project directory.

Exclude glob patterns by repeating `--exclude`:

```bash
f2clipboard files --dir path/to/project --exclude 'node_modules/*' --exclude '*.log'
```

Include extra glob patterns by repeating `--include`:

```bash
f2clipboard files --pattern '*.py' --include '*.md' --include '*.txt'
```

Preview output without copying to the clipboard:

```bash
f2clipboard files --dir path/to/project --dry-run
```

Skip files larger than a given number of bytes:

```bash
f2clipboard files --dir path/to/project --max-size 1000
```

`--max-size` must be a positive integer.

Save output to a Markdown file:

```bash
f2clipboard files --dir path/to/project --output snippet.md
```

Select all matched files without prompts:

```bash
f2clipboard files --dir path/to/project --pattern '*.py' --all
```

Combine with `--dry-run` to preview the output before copying.

Use brace expansion in patterns to match multiple extensions:

```bash
f2clipboard files --pattern '*.{py,js}'
```

Check the installed version:

```bash
f2clipboard --version
```

### Merge conflict helpers

Fetch a GitHub pull request and try automatic merge strategies:

```bash
f2clipboard merge-resolve --pr 123 --strategy both
```

The command fetches the PR's head (`pull/<number>/head`), checks it out into a
local `pr-<number>` branch, looks up the base branch from the GitHub API, and
then attempts the requested merge strategy (or both). It also ensures the
working tree is clean and by default runs `f2clipboard merge-checks` after a
successful merge. When `--pr` is provided and `GITHUB_TOKEN` is configured the
tool also posts a summary comment to the pull request describing the outcome.
Pass `--no-run-checks` to skip automated validation, use
`--strategy ours`/`--strategy theirs` to attempt a single strategy, or override
the merge base with `--base`.

If all merge strategies fail, the command gathers the conflicting hunks and,
when either `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is configured, invokes the
Codex merge-conflicts prompt to propose a unified diff. `merge-resolve` then
retries the merge, applies the suggested patch automatically and stages the
changes before running `f2clipboard merge-checks` (unless `--no-run-checks` is
provided). If the patch cannot be applied it is printed so you can review or
apply it manually. Without credentials the command reminds you to configure an
API key for automatic patch generation.

Run the standard checks after resolving conflicts:

```bash
f2clipboard merge-checks
```

The command looks for modified files in the current repository, runs
`pre-commit run --files` for those paths, and then executes `pytest -q`. Use
`--file` to pass an explicit list of files or `--repo` to point at a different
working tree.

## GitHub Action

Run `f2clipboard` inside GitHub Actions using the bundled composite action:

```yaml
- uses: futuroptimist/f2clipboard@v1
  with:
    args: codex-task https://chatgpt.com/codex/tasks/task_123 --no-clipboard
```

Pass any CLI arguments via `args`; the default is `--help`.
See [docs/github-action.md](docs/github-action.md) for authentication options, environment variables, and more details.

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

Sort them alphabetically:

```bash
f2clipboard plugins --sort
```

Reverse the order of plugins:

```bash
f2clipboard plugins --reverse
```

Sort descending:

```bash
f2clipboard plugins --sort --reverse
```

Filter by substring (case-insensitive with `--ignore-case`):

```bash
f2clipboard plugins --filter jira --ignore-case
```

Output as JSON:

```bash
f2clipboard plugins --json
```

Output as YAML:

```bash
f2clipboard plugins --yaml
```

Show the number of installed plugins:

```bash
f2clipboard plugins --count
```

Output the plugin count as JSON (including plugin names):

```bash
f2clipboard plugins --count --json
```

```json
{"count": 1, "plugins": ["jira"]}
```

Show plugin versions:

```bash
f2clipboard plugins --versions
```

Output versions as JSON:

```bash
f2clipboard plugins --versions --json
```

Show plugin source paths:

```bash
f2clipboard plugins --paths
```

Output paths as JSON:

```bash
f2clipboard plugins --paths --json
```

The first bundled plugin summarises Jira issues:

```bash
f2clipboard jira path/to/issue.json
```

Provide either a Jira issue URL or a path to a JSON export. The ticket's description is summarised
and copied to your clipboard.

## Contributing

See [AGENTS.md](AGENTS.md) for LLM-specific guidelines and [CONTRIBUTING.md](CONTRIBUTING.md) for the standard contribution workflow. Prompt templates live in [docs/prompts/codex/overview.md](docs/prompts/codex/overview.md).
