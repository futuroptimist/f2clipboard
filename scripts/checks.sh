#!/usr/bin/env bash
set -euo pipefail

ruff check .
flake8 .
black --check .
isort --check .
