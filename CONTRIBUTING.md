# Contributing to MDKV

Contributions are welcome! Please follow these guidelines.

## Development setup

```bash
# Clone and install
uv venv
uv run pip install -e ".[dev]"

# Run tests
uv run pytest -q

# Run tests with coverage
uv run pytest -q --cov=mdkv --cov-report=term-missing

# Build docs
uv run sphinx-build -b html docs docs/_build/html
```

## Code style

- Python 3.9+ (CI uses 3.14)
- Explicit, readable names (no 1-2 character variables)
- Guard clauses over deep nesting
- Use `datetime.now(timezone.utc)` — never `datetime.utcnow()` (deprecated)
- Keep comments minimal; document "why", not "what"
- Public API documented via docstrings
- `py.typed` marker present (PEP 561) — all public functions should have type hints

## Architecture

- `mdkv.core`: data model + validation (no external deps)
- `mdkv.storage`: ZIP container persistence (`MDKVFormatError`)
- `mdkv.services`: search, export, diff, stats (no I/O, operate on in-memory docs)
- `mdkv.cli`: Click-based CLI entry point (`mdkv` or `python -m mdkv`)
- `mdkv.gui`: FastAPI web GUI with REST API
- `mdkv.common`: logging utilities
- `mdkv.library`: example definition builder
- `mdkv.demo`: demo document builder

Legacy shim files (`mdkv/model.py`, `mdkv/io.py`, etc.) re-export from the
package modules for backward compatibility.

## Adding a new CLI command

1. Add the command function in `mdkv/cli/main.py` with `@main.command("name")`
2. Apply the `@_handle_load_errors` decorator if the command loads .mdkv files
3. Use `click.echo()` for output, `click.echo(..., err=True)` for errors
4. Use `json.dumps(..., indent=2)` for structured output
5. Add tests in `tests/test_cli_*.py`
6. Document in `docs/cli.md`

## Adding a new service

1. Create the module in `mdkv/services/`
2. Export from `mdkv/services/__init__.py`
3. Export from `mdkv/__init__.py` and update `__all__`
4. Add to `docs/api.rst`
5. Update `docs/architecture.md`
6. Write tests in `tests/test_services_*.py`

## Adding a new GUI endpoint

1. Add the endpoint in `mdkv/gui/server.py` inside `create_app()`
2. Use `_require_doc()` for endpoints that need a loaded document
3. Return `dict` for JSON responses, `HTMLResponse` for HTML
4. Write tests in `tests/test_gui_*.py` using `TestClient`

## Testing

- Tests are thin orchestrators of module methods
- No mocks for documented flows
- Use `pytest` fixtures (`tmp_path`) for file I/O
- Run `uv run pytest -q` before submitting PRs
- Coverage target: 90%+ overall, 100% for core modules

## Pull request checklist

- [ ] Tests pass: `uv run pytest -q`
- [ ] Coverage maintained: `uv run pytest -q --cov=mdkv`
- [ ] Docs build: `uv run sphinx-build -b html docs docs/_build/html`
- [ ] No deprecation warnings from our code
- [ ] CHANGELOG.md updated (if user-facing changes)
- [ ] `.cursorrules` updated (if API surface changed)
