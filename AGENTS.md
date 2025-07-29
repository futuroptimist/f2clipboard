# Agents Guide for f2clipboard

> This file follows the [AGENTS.md specification](https://agentsmd.net/) and provides instructions for LLM contributors. Its scope is the entire repository. Nested `AGENTS.md` files override these rules. Always run the checks listed below after modifying any files.

## Project Structure
- `f2clipboard.py` – CLI entry point
- `tests/` – test suite
- `scripts/` – helper scripts
- `AGENTS.md` and `llms.txt` – agent and model guidance

## Coding Conventions
### General
- Use Python 3.x and keep style consistent.
- Format code with `black` and `isort`.
- Keep names descriptive and include comments for complex logic.
- Document new CLI flags and prompt templates.

### Styling
- Follow existing patterns in the code base.

## Testing Requirements
Run the full test suite before committing:

```bash
pytest -q
```

## Pull Request Guidelines
1. Provide a clear description of the change.
2. Reference related issues when applicable.
3. Ensure all tests and checks pass.
4. Keep PRs focused on a single concern.
5. Update documentation if behavior changes.

## Programmatic Checks
Run the following before opening a PR:

```bash
pre-commit run --files <modified_files>
pytest -q
```

All checks must pass before code is merged.

## Acceptable LLMs
See [llms.txt](llms.txt) for the list of approved models.

## Disclaimers
Network access may be restricted; provide offline instructions when possible.
