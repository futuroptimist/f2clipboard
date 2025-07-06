flake8 .
black --check .
isort --check .
pytest -q
