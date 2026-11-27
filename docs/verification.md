# Verify MDKV

Install uv and the Python selected by the repository's `.python-version`.
Use these commands from the project root to prepare the locked development
environment and run checks from the tracked CI workflow.

```sh
uv sync --locked --extra dev
uv run --no-sync ruff check mdkv
uv run --no-sync mypy mdkv
uv run --no-sync pytest -q --cov=mdkv --cov-report=term-missing --cov-fail-under=90
uv run --no-sync sphinx-build -W --keep-going -b html docs docs/_build/html
uv build --out-dir docs/_build/dist
```

The package supports Python 3.11 and newer. The tracked workflow configures a
separate pytest job on Python 3.11.
Open `docs/_build/html/index.html` for the built reference. Use the
[publication build](publication.md) to generate the paper and MDKV bundle.

Pandoc is an optional dependency for the CLI's PDF, EPUB, and DOCX conversions.
Container, Markdown, and HTML checks use local files.
