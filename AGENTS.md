# Agents Guide

This project uses lightweight command line utilities to copy files into Markdown for LLM conversations. It may evolve into a workflow-based CLI, so clear instructions are important for contributors and future LLM agents.

## Overview
- `f2clipboard.py` collects files from a chosen directory and copies their contents to the clipboard in a formatted block.
- See the [README](README.md) for installation and the project roadmap.

## Setup
1. Ensure Python 3.x is installed.
2. Install dependencies with `pip install clipboard`.
3. Optionally create a virtual environment for isolation.
4. Check `llms.txt` for the list of approved LLMs.

## Testing
Run all tests before committing:

```bash
pytest -q
```

## Guidelines
- Format code with `black`.
- Keep commit messages concise (`component: summary`).
- Document any new CLI flags or prompt templates.
- Update this file if agent usage changes.

## Acceptable LLMs
See [llms.txt](llms.txt) for the list of allowed models.

## Disclaimers
Network access may be restricted in some environments, so some commands could fail. Provide offline instructions when possible.
