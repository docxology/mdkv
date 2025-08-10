# MDKV: Multitrack Markdown Container (Python)

A modular Python implementation of the MDKV concept in `MKVD_overview.md`.

- Zip-based `.mdkv` container with `manifest.yaml` and `tracks/`.
- Tracks: primary, translation, commentary, code, reference, media_ref, revision.
- Services: validation, search, export (Markdown/HTML), CLI.

## Why MDKV?

MDKV packages related Markdown "tracks" into a single, portable file while preserving structure and intent. This enables:

- Multilingual documents without branching: author a single canonical `primary` track alongside any number of `translation` tracks.
- Layered collaboration: keep `commentary` and `reference` separate from canonical content; include or exclude them per audience.
- Reproducible publishing: export just the tracks needed for a channel (e.g., primary-only HTML, or primary+refs Markdown) deterministically.
- Governance-friendly history: `revision` tracks make review notes and change summaries first-class.
- Plaintext portability: Markdown in a ZIP with a YAML manifest—easy to diff, archive, and pass around.

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

See `docs/concept.md` for the format concept, `docs/format.md` for the container/manifest schema, `docs/architecture.md` for package layout, `docs/cli.md` for CLI details, and `examples/logged_workflow.py` for a logged, end-to-end workflow that writes outputs to `workflow_out/`.

## GUI

```bash
uv run mdkv gui --path doc.mdkv
# or
python3 run_gui.py --path doc.mdkv
```

- Preview uses checkboxes to toggle tracks: keep "All" checked for everything, or uncheck it and select a custom subset.
- The editor pane always contains the full combined Markdown; live updates persist per-track.
- Programmatic subset preview is available via `POST /api/render/tracks_html` with `{ "track_ids": ["primary", ...] }`.

Preview video:

```text
docs/_static/gui_demo.gif (optional)
```

Inline preview (if present):

![GUI demo](docs/_static/gui_demo.gif)

To regenerate the demo recording:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
python3 examples/record_gui_demo.py
# optional GIF conversion if ffmpeg + imagemagick are available
ffmpeg -i docs/_static/gui_demo.webm -vf fps=12,scale=960:-1:flags=lanczos -y docs/_static/gui_demo.mp4
magick -loop 0 -delay 8 -density 144 docs/_static/gui_demo.mp4 docs/_static/gui_demo.gif
```

## Features

- Structured container: `.mdkv` is a ZIP with `manifest.yaml` and `tracks/` directory
- Track types: `primary`, `translation`, `commentary`, `code`, `reference`, `media_ref`, `revision`
- Validation: ensures required fields and at least one `primary` track
- Search: regex across tracks with type/language filters
- Export: render to Markdown (optionally filtered by track type) and to HTML (primary by default)
- CLI + Python API: create, inspect, modify, search, validate, and export

## Installation

We recommend `uv` for fast, reproducible environments:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
uv run mdkv --help
```

Alternatively, standard `pip` works:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
mdkv --help
```

## Development

- Tests: `uv run pytest -q`
- Examples: see `examples/` for minimal scripts that call APIs.
- Design: tests and examples act as thin orchestrators of module methods.

### Contributing

Contributions are welcome. Please:

- Follow the test-driven, modular design used throughout the repo.
- Keep public APIs documented via docstrings and Sphinx; update `docs/api.rst` when surfacing new modules.
- Run `uv run pytest -q` and `uv run sphinx-build -b html docs docs/_build/html` before submitting PRs.

### FAQ

- Why not keep everything in one Markdown file? Because different audiences need different views; tracks make export and collaboration explicit without forking content.
- Is `.mdkv` proprietary? No—it's a simple ZIP container with YAML + Markdown; no custom filesystem.
- How do I share a subset? Use CLI export filters, or the GUI checkboxes to preview subsets. Programmatically, build Markdown with `to_markdown(doc, include_track_types=[...])`.

### Related reading

- CommonMark specification (`https://commonmark.org`)
- Best practices for README structure and clarity (e.g., "Best Practices for Writing README Files")
- Guidance on project documentation organization (e.g., "How to Write the Best README Files")

## Package structure

- `mdkv.core`: types, errors, validation
- `mdkv.storage`: save/load container
- `mdkv.services`: search and export
- `mdkv.cli`: CLI entry point (`mdkv`)

License: Apache-2.0. See the `LICENSE` file.

## Concept overview

- Container: `.mdkv` is a ZIP with a `manifest.yaml` and `tracks/` Markdown files
- Tracks: `primary`, `translation`, `commentary`, `code`, `reference`, `media_ref`, `revision`
- Validation: requires `title`, `authors`, and a `primary` track
- Export: Markdown (all or filtered tracks) and HTML (primary)

Export files example:

```python
from pathlib import Path
from mdkv.export import export_to_files

# write selected tracks as individual .md files
export_to_files(loaded, Path("out_tracks"), include_track_types=["primary", "commentary"])
```

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
