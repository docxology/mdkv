## Pull Request Checklist

- [ ] Tests pass: `uv run pytest -q`
- [ ] Coverage maintained: `uv run pytest -q --cov=mdkv`
- [ ] Docs build: `uv run sphinx-build -b html docs docs/_build/html`
- [ ] No deprecation warnings from our code
- [ ] CHANGELOG.md updated (if user-facing changes)
- [ ] .cursorrules updated (if API surface changed)

## Description

Brief description of the changes.

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Other
