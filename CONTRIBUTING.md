# Contributing

1. Fork and clone the repository.
2. Run `pre-commit run --files <modified_files>` and `pytest -q` before opening a pull request.
3. Mark tests that record HTTP interactions with `@pytest.mark.vcr`.
4. Describe your changes clearly.
