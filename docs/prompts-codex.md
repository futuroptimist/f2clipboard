---
title: 'Codex Prompts'
slug: 'prompts-codex'
---

# Codex prompts for the *f2clipboard* repo

Codex can automate improvements to this repository when given clear, scoped instructions.
Use the blocks below to craft prompts and track roadmap progress.

## Baseline automation prompt

```
SYSTEM:
You are an automated contributor for the f2clipboard repository. Follow the conventions in AGENTS.md and README.md. Make small, incremental improvements or complete a roadmap item. Always run `pre-commit run --files <modified_files>` and `pytest -q`.

USER:
<task-specific instructions>

OUTPUT:
A pull request summarising the change and test results.
```

## Reusable template

```
You are working in futuroptimist/f2clipboard.

GOAL: <one sentence>.

FILES OF INTEREST
- <path/to/File1>   ← brief hint
- <path/to/File2>

REQUIREMENTS
1. …
2. …
3. …

ACCEPTANCE CHECK
`pre-commit run --files <modified_files>` && `pytest -q` exit with status 0.

OUTPUT
Return **only** the patch (diff) needed.
```

## Roadmap implementation prompt

Tasks are tracked in [README.md](../README.md) under "Roadmap" using Markdown checkboxes.
Codex should pick a single line that is unchecked and implement it fully.
After all checks pass, mark the corresponding line with `💯`.

```
SYSTEM:
You are an automated contributor for the f2clipboard repository. Choose one item from README.md's "Roadmap" section that is `[ ]` or `[x]` without `💯`. Implement it completely with code, tests and documentation. Always run `pre-commit run --files <modified_files>` and `pytest -q` before committing.

USER:
1. Follow the steps above.
2. After verifying the implementation, mark the README line with `💯`.
3. Update documentation as needed.

OUTPUT:
A pull request implementing the chosen item with all checks green.
```

## Task-specific prompts

### 1 Size-gate logs and summarise via LLM

```
SYSTEM: You are an automated contributor for futuroptimist/f2clipboard.

GOAL
Replace the TODO placeholder in `f2clipboard/codex_task.py` with size-gated log summarisation using the configured LLM.

FILES OF INTEREST
- f2clipboard/codex_task.py   ← summarise oversize logs
- f2clipboard/config.py       ← expose `log_size_threshold`
- tests/test_codex_task.py    ← test summarisation behaviour

REQUIREMENTS
1. When a log exceeds `Settings.log_size_threshold`, call the default LLM to produce a concise summary.
2. Include the first 100 lines of the original log inside a `<details>` block after the summary.
3. Add a `--log-size-threshold` CLI option to override the default threshold.

ACCEPTANCE CHECK
`pre-commit run --files f2clipboard/codex_task.py f2clipboard/config.py tests/test_codex_task.py` && `pytest -q` succeed.

OUTPUT
Return the diff.
```

### 2 Emit Markdown to stdout and clipboard

```
SYSTEM: You are an automated contributor for futuroptimist/f2clipboard.

GOAL
Have the `codex-task` command write its Markdown result both to stdout and the user's clipboard.

FILES OF INTEREST
- f2clipboard/codex_task.py   ← clipboard integration
- tests/test_codex_task.py    ← cover clipboard behaviour
- README.md                   ← document clipboard output

REQUIREMENTS
1. Use `pyperclip` for clipboard interaction and handle missing system utilities with a warning instead of failing.
2. Ensure the original Markdown still prints to stdout.
3. Add an example to README's Getting Started section.

ACCEPTANCE CHECK
`pre-commit run --files f2clipboard/codex_task.py tests/test_codex_task.py README.md` && `pytest -q` succeed.

OUTPUT
Return only the patch.
```
