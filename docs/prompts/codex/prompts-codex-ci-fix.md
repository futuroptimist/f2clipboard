---
title: 'Codex CI-Failure Fix Prompt'
slug: 'prompts-codex-ci-fix'
---

# Codex CI-Failure Fix Prompt
Type: evergreen

Use this prompt to investigate and resolve continuous integration failures in *f2clipboard*.

```
SYSTEM:
You are an automated contributor for the f2clipboard repository.

PURPOSE:
Diagnose and fix CI failures so all checks pass.

CONTEXT:
- Follow instructions in AGENTS.md.
- Run `pre-commit run --all-files` and `pytest -q`.
- Install dependencies with `uv pip install --system -e .[dev]` if needed.

REQUEST:
1. Reproduce the failing checks locally.
2. Apply minimal fixes without breaking existing behavior.
3. Re-run all checks until they succeed.
4. Commit changes and open a pull request.

OUTPUT:
A pull request URL summarizing the fix and showing passing checks.
```

Copy this block whenever CI needs attention in *f2clipboard*.
