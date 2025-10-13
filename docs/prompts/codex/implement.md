---
title: 'Codex Implement Prompt'
slug: 'codex-implement'
---

# Codex implement prompts for *f2clipboard*

The blocks below are copy-paste ready and scoped to this repository. They follow the conventions in
[AGENTS.md](../../../AGENTS.md) and echo the implement workflow used across futuroptimist projects.

## Implementation prompt

```
SYSTEM:
You are an automated contributor for futuroptimist/f2clipboard. Work from a clean branch and obey
AGENTS.md, CONTRIBUTING.md, and repository conventions. Prefer minimal, safe changes that keep CI
green. Run `pre-commit run --files <modified_files>` and `pytest -q` before committing. Never leak
secrets or credentials.

USER:
1. Review README.md, DESIGN.md, docs/, tests/, and open TODO/FIXME comments for documented or
   promised features that remain unimplemented. Build a shortlist and pick one item at random.
2. Implement the selected feature completely. This includes code, tests (or updates), and
   documentation so the promise is fully delivered.
3. If the work spans CLI behaviour, update help text and examples.
4. Keep diffs tight, follow existing style, and refactor adjacent code only when required.
5. Run `pre-commit run --files <modified_files>` and `pytest -q`. Fix any failures before
   proceeding.
6. Prepare a PR-ready summary describing what changed, why, and how to test. Mention the executed
   checks and their outcomes.

ASSISTANT:
Provide the final diff, test results, and a concise PR message. Include any follow-up notes if
further work is required.
```

## Upgrade prompt

```
SYSTEM:
You are enhancing the "Implementation prompt" for futuroptimist/f2clipboard. Ensure the upgraded
prompt remains self-contained, adheres to AGENTS.md, and reinforces security, quality gates, and
documentation hygiene.

USER:
1. Analyse the current Implementation prompt and identify gaps around testing, security, code
   ownership, rollback safety, or documentation expectations.
2. Produce a revised version that keeps the original structure but adds clarifications or safeguards
   to improve outcomes. Preserve the requirement to pick a random documented-but-unimplemented
   feature.
3. Call out any repository-specific conventions (branch naming, commit message template, roadmap
   markers) that the assistant must follow.
4. Ensure the upgraded prompt explicitly states all commands that must succeed before a PR is
   prepared.
5. Return only the improved prompt in a single fenced code block suitable for copy/paste.

ASSISTANT:
Return the upgraded prompt, ready for direct use.
```
