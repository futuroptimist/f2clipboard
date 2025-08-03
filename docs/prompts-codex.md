---
title: 'Codex Prompts'
slug: 'prompts-codex'
---

# Codex prompts for the *f2clipboard* repo

Codex can automate improvements to this repository when given clear, scoped instructions.
Use the templates below to craft prompts and track roadmap progress.

## Reusable template

```text
You are working in futuroptimist/f2clipboard.

GOAL: <one sentence>.

FILES OF INTEREST
- <path/to/File1>   ← brief hint
- <path/to/File2>

REQUIREMENTS
1. …
2. …
3. …

OUTPUT
Return **only** the patch (diff) needed.
```

## Implementation Prompt

Tasks are tracked in [README.md](../README.md) under "Roadmap" using Markdown checkboxes.
Codex should pick a single line that is unchecked and implement it fully. After
all checks pass, mark the corresponding line with `💯`.

```text
SYSTEM:
You are an automated contributor for the f2clipboard repository. Choose one
item from README.md's "Roadmap" section that is `[ ]` or `[x]` without `💯`.
Implement it completely with code, tests and documentation. Always run
`pre-commit run --files <modified_files>` and `pytest -q` before committing.

USER:
1. Follow the steps above.
2. After verifying the implementation, mark the README line with `💯`.
3. Document new functionality as needed.

OUTPUT:
A pull request implementing the chosen item with all checks green.
```
