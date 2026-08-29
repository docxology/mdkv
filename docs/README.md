# mdkv — Documentation Index

`mdkv` is a plaintext knowledge/video format and toolkit (Python package `mdkv`,
CLI entry point `mdkv`, optional GUI via `run_gui.py`). See the repo root
[`README.md`](../README.md) for the product overview and
[`../AGENTS.md`](../AGENTS.md) for agent-facing conventions.

## Map

- `index.rst`, `conf.py`, `Makefile`, `_static/` — Sphinx docs build.
- `architecture.md` — system architecture.
- `concept.md` — the MKVD/mdkv concept and data model.
- `format.md` — the mdkv file format specification.
- `cli.md` — CLI reference.
- `usage.md` — usage guide.
- `api.rst` — API reference (autodoc).
- `security.md` — security notes.
- `license.md` — licensing.

## Build the docs

```bash
make -C docs html   # Sphinx; output under docs/_build/
```

## Run / test the package (from repo root)

```bash
uv run mdkv --help
uv run pytest
```

(Commands taken from `pyproject.toml` `[project.scripts]` (`mdkv = "mdkv.cli:main"`)
and repo layout; no other run scripts are declared in the repo.)
