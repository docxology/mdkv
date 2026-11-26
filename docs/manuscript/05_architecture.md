# Software Architecture: Thin Orchestration over a Typed Core

MDKV follows a thin‑orchestrator, modular architecture:

- `mdkv.core`: data model and validation
- `mdkv.storage`: persistence (read/write `.mdkv`)
- `mdkv.services`: search and export utilities
- `mdkv.cli`: CLI entry points and subcommands

This separation enables stable public APIs, testable modules, and straightforward extension.

## Core Model (`mdkv.core`)

The core defines two primary classes:

- `Track`: a single Markdown track with `track_id`, `track_type`, `language`, `path`, `content`, and invariant checks (valid type, non‑empty id, `path` under `tracks/`).
- `MDKVDocument`: an in‑memory aggregate with metadata (`title`, `authors`, `created`, `version`, and `metadata` map) and a mapping `track_id → Track`. It provides helpers for adding/removing tracks, renaming, content updates, language listing, and metadata set/get/remove.
- Track constructors and mutation helpers enforce structural checks; mutable dataclasses are revalidated at save/explicit validation boundaries. Storage safety and editorial validity are separate contracts.

The core also surfaces `allowed_track_types()` and validation types (`ValidationError`, `ValidationIssue`).

## Storage (`mdkv.storage`)

ZIP + YAML persistence:

- `save_mdkv(doc, output_path)`: write tracks under `tracks/` and emit `manifest.yaml` from the document.
- `load_mdkv(input_path)`: parse the manifest and reconstruct the document, loading each track’s content.

The manifest lists metadata and track descriptors; bodies remain discrete files for transparency and editability.

## Services (`mdkv.services`)

Services operate over `MDKVDocument` instances without owning container I/O:

- Search: stdlib `re` matching with optional `track_type`/`language` filters, supervised deadline enforcement and bounded pages; sync and async APIs share results.
- Export: composition of multi‑track Markdown via `to_markdown()`, primary‑track HTML via `to_html()` using [markdown‑it‑py](https://github.com/executablebooks/markdown-it-py), and per‑track files via `export_to_files()`.
- Native conversion: optional Pandoc PDF/EPUB/DOCX export of the body plus allowlisted frontmatter; informational MDKV comments are not emitted into native output.
- Comparison and statistics: structured `diff_documents()` results and textual `compute_stats()` counts; neither is an empirical benchmark.
- Export determinism: order is manifest‑driven; fixed inputs and renderer versions give identical text, while ZIP bytes and generation timestamps may differ.

## CLI (`mdkv.cli`)

Thin orchestrators for: init, info, validate, track ops, search, export, metadata, and GUI. Commands call module APIs directly for testability and minimal command‑layer logic.

## GUI (`mdkv.gui`)

The local GUI has a canonical single-track editor and independent preview checkboxes. `POST /api/render/tracks_html` renders subsets; `GET /api/track?track_id=...` reads a literal track identifier and `PUT /api/track` updates an existing track without parsing display comments. `GET /api/render/markdown` remains a combined presentation export. Browser operations serialize pending edits before switches/saves. State is shared across clients; persistence uses the same atomic `save_mdkv` writer as the CLI.

## Architecture Map and Source Pointers

- Layers and responsibilities: see [architecture guide](https://github.com/docxology/mdkv/blob/main/docs/architecture.md) (built locally with Sphinx; there is no hosted docs site).
- Core model: [core model](https://github.com/docxology/mdkv/blob/main/mdkv/core/model.py) defines `Track`, `MDKVDocument`, and invariants; re‑exported via [package entry point](https://github.com/docxology/mdkv/blob/main/mdkv/__init__.py).
- Storage: [container storage implementation](https://github.com/docxology/mdkv/blob/main/mdkv/storage/io.py) implements `save_mdkv` and `load_mdkv` (ZIP + YAML manifest and `tracks/`).
- Services: export in [export service](https://github.com/docxology/mdkv/blob/main/mdkv/services/export.py) (`to_markdown`, `to_html`, `export_to_files`); search in [search service](https://github.com/docxology/mdkv/blob/main/mdkv/services/search.py). Both are re‑exported at the top‑level package for a stable public API.
- CLI: [CLI implementation](https://github.com/docxology/mdkv/blob/main/mdkv/cli/main.py) surfaces subcommands (init, info, validate, track ops, search, export, gui).
- GUI backend: [GUI server](https://github.com/docxology/mdkv/blob/main/mdkv/gui/server.py) provides `POST /api/render/tracks_html` for subset rendering; static assets under [GUI assets](https://github.com/docxology/mdkv/tree/main/mdkv/gui/static).

Data flow summary (see also the repository `README.md` and docs pages):

- Authoring: create or load an `MDKVDocument`, add tracks; validate.
- Persistence: `save_mdkv` writes `tracks/` and `manifest.yaml` into a `.mdkv` ZIP; `load_mdkv` reconstructs.
- Services: `search_document` filters/matches; `to_markdown` and `to_html` export views; `export_to_files` writes per‑track files. For end‑to‑end CLI usage, see [CLI guide](https://github.com/docxology/mdkv/blob/main/docs/cli.md).
