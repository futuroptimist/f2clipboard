# Contributing

1. Fork and clone the repository.
2. Review [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and [AGENTS.md](AGENTS.md).
3. Run `pre-commit run --files <modified_files>` and `pytest -q` before opening a pull request.
4. Mark tests that record HTTP interactions with `@pytest.mark.vcr`.
5. Describe your changes clearly.
