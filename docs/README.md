# MDKV Documentation Map: Guides, Contracts and Build

`mdkv` is a ZIP/YAML multitrack Markdown format and toolkit (Python package `mdkv`,
CLI entry point `mdkv`, local GUI via `run_gui.py`). See the repo root
[`README.md`](../README.md) for the product overview and
[`../AGENTS.md`](../AGENTS.md) for agent-facing conventions.

## Map

- `index.rst`, `conf.py`, `Makefile`, `_static/` — Sphinx docs build.
- `architecture.md` — layer boundaries, service responsibilities and guarantees.
- `concept.md` — the MDKV concept, graphical abstract and data model.
- `format.md` — the MDKV file-format specification (ZIP envelope, manifest and tracks).
- `cli.md` — CLI reference.
- `usage.md` — usage guide.
- `api.rst` — API reference (autodoc).
- `security.md` — supplier-input, browser-origin and native-conversion boundaries.
- `manuscript/MANUSCRIPT_STATUS.md` — manuscript source, bundle and release evidence.
- `license.md` — licensing.
- `../paper/` — publication track, manuscript source, bundle builder and canonical graphical abstract (`figures/mdkv-graphical-abstract.svg`, PNG rendering).

## Build the docs

```bash
make -C docs html   # Sphinx; output under docs/_build/
```

## Run / test the package (from repo root)

```bash
uv sync --extra dev   # first time: create .venv with runtime + dev deps
uv run mdkv --help
uv run pytest
```

(Commands taken from `pyproject.toml` `[project.scripts]` (`mdkv = "mdkv.cli:main"`)
and repo layout; no other run scripts are declared in the repo.)
