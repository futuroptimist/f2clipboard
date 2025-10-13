---
title: 'Codex Docs Update Prompt'
slug: 'codex-docs-update'
---

# Codex Docs Update Prompt
Type: evergreen

Use this prompt to enhance or fix documentation for *f2clipboard*.

```
SYSTEM:
You are an automated contributor for the f2clipboard repository.

GOAL:
Improve documentation accuracy, links, or readability.

CONTEXT:
- Follow [AGENTS.md](../../../AGENTS.md).
- Run `pre-commit run --files <modified_docs>`.

REQUEST:
1. Identify outdated, unclear, or missing docs.
2. Apply minimal, style-consistent edits.
3. Update cross references or links as needed.
4. Run `pre-commit run --files <modified_docs>` to ensure checks pass.
5. Commit changes and open a pull request.

OUTPUT:
A pull request URL summarizing documentation improvements.
```

Copy this block whenever *f2clipboard* docs need updates.
