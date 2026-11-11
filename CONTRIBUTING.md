# Contributing

1. Fork and clone the repository.
2. Review [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and [AGENTS.md](AGENTS.md).
3. Run `pre-commit run --files <modified_files>` and `pytest -q` before opening a pull request.
4. Mark tests that record HTTP interactions with `@pytest.mark.vcr`.
5. Describe your changes clearly.

## Dependency update pilot

Dependabot checks the root Python project and GitHub Actions weekly, with at most
two open version-update PRs per ecosystem. GitHub manages security-update PRs
separately; this limit does not cap them or change their repository settings.

Review each update's diff, dependency source and release notes manually, including
runtime requirements and breaking changes. Check CI and review feedback against
the final commit before merging. This pilot does not enable auto-merge or change
repository settings.
