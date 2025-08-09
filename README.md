# MDKV: Multitrack Markdown Container (Python)

A modular Python implementation of the MDKV concept in `MKVD_overview.md`.

- Zip-based `.mdkv` container with `manifest.yaml` and `tracks/`.
- Tracks: primary, translation, commentary, code, reference, media_ref, revision.
- Services: validation, search, export (Markdown/HTML), CLI.

## Quickstart (uv)

```bash
# install uv once per machine (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh

# from repo root
uv venv
uv run pytest -q
uv run mdkv --help
```

## Create a document

```bash
uv run mdkv init --title "Doc" --author "You" --out doc.mdkv
uv run mdkv info doc.mdkv
uv run mdkv validate doc.mdkv
uv run mdkv export doc.mdkv > out.md
uv run mdkv export --html doc.mdkv > out.html
```

## Docs

```bash
# build Sphinx docs to docs/_build/html
uv run sphinx-build -b html docs docs/_build/html
```

See `docs/concept.md` for the format concept, `docs/cli.md` for CLI details, and `examples/logged_workflow.py` for a logged, end-to-end workflow that writes outputs to `workflow_out/`.

## Development

- Tests: `uv run pytest -q`
- Examples: see `examples/` for minimal scripts that call APIs.
- Design: tests and examples act as thin orchestrators of module methods.

## Package structure

- `mdkv.core`: types, errors, validation
- `mdkv.storage`: save/load container
- `mdkv.services`: search and export
- `mdkv.cli`: CLI entry point (`mdkv`)

License: MIT

## Concept overview

- Container: `.mdkv` is a ZIP with a `manifest.yaml` and `tracks/` Markdown files
- Tracks: `primary`, `translation`, `commentary`, `code`, `reference`, `media_ref`, `revision`
- Validation: requires `title`, `authors`, and a `primary` track
- Export: Markdown (all or filtered tracks) and HTML (primary)

Example layout:

```text
doc.mdkv
├─ manifest.yaml
└─ tracks/
   ├─ primary.md
   ├─ commentary.md
   └─ translation-es.md
```

Implications:

- Multilingual and multi-audience documents without branching
- Clean layering of notes/references separate from the primary
- Simple, portable, git-friendly plaintext inside a single file
