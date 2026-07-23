# MDKV: Multitrack Markdown Container (Python)

A modular Python implementation of the MDKV concept in `MKVD_overview.md`.

- Zip-based `.mdkv` container with `manifest.yaml` and `tracks/`.
- Tracks: primary, translation, commentary, code, reference, media_ref, revision.
- Services: validation, search, export (Markdown/HTML), diff, stats, CLI.

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

## Import from Markdown

```bash
# Import an existing Markdown file as a new .mdkv document
uv run mdkv import README.md --out imported.mdkv --title "Imported" --author "You"
```

## CLI Commands

| Command | Description |
|---|---|
| `init` | Create a new .mdkv document |
| `info` | Show document metadata |
| `list-tracks` | List all tracks |
| `add-track` | Add a new track (`--content` or `--file`) |
| `remove-track` | Remove a track by id |
| `rename-track` | Rename a track |
| `update-track` | Update track content (`--content` or `--file`) |
| `export` | Export to Markdown, HTML, or individual files |
| `export-tracks` | Export filtered tracks as Markdown |
| `search` | Regex search across tracks (`-i` for case-insensitive) |
| `validate` | Validate document (`--json` for JSON output) |
| `set-meta` / `get-meta` | Manage metadata |
| `import` | Import a Markdown file into a new .mdkv |
| `diff` | Compare two .mdkv documents |
| `stats` | Show document statistics |
| `gui` | Launch web GUI |
| `license` | Show license info |

### Export options

```bash
# Markdown (all tracks)
uv run mdkv export doc.mdkv

# HTML with specific track types
uv run mdkv export doc.mdkv --html --types primary,commentary

# Export tracks as individual files
uv run mdkv export doc.mdkv --out-dir tracks_out/

# Markdown with YAML frontmatter
uv run mdkv export doc.mdkv --metadata-header
```

### Add/update tracks from files

```bash
# Add a track with content read from a file
uv run mdkv add-track doc.mdkv --id notes --type commentary --file notes.md

# Update a track's content from a file
uv run mdkv update-track doc.mdkv --id primary --file updated.md
```

### Validate with JSON output

```bash
# Human-readable
uv run mdkv validate doc.mdkv

# JSON output for CI/automation
uv run mdkv validate doc.mdkv --json
```

### Diff two documents

```bash
uv run mdkv diff doc_v1.mdkv doc_v2.mdkv
```

Reports changes in title, authors, version, tracks (added/removed/modified), and metadata.

### Statistics

```bash
uv run mdkv stats doc.mdkv
```

Shows track count, types, languages, character/line counts.

## Python API

```python
from datetime import datetime, timezone
from mdkv import (
    MDKVDocument, Track,
    save_mdkv, load_mdkv,
    validate_document,
    export_to_files,
    diff_documents,
    compute_stats,
)

doc = MDKVDocument(title="T", authors=["A"], created=datetime.now(timezone.utc))
doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Hello"))

# Save and reload
save_mdkv(doc, "doc.mdkv")
loaded = load_mdkv("doc.mdkv")

# Validate (returns issues, raises on ERROR)
issues = validate_document(loaded)

# Diff two documents
result = diff_documents(doc, loaded)
if not result.has_changes:
    print("Identical")

# Compute statistics
stats = compute_stats(loaded)
print(f"{stats.track_count} tracks, {stats.total_characters} chars")

# JSON serialization
data = doc.to_dict()
restored = MDKVDocument.from_dict(data)
```

## Docs

```bash
uv run sphinx-build -b html docs docs/_build/html
```

See `docs/` for concept, format, architecture, usage, CLI, and API reference.

## GUI

```bash
uv run mdkv gui --path doc.mdkv
```

The GUI exposes a REST API with endpoints for search, stats, diff, validate,
and CRUD operations on documents and tracks.

## Features

- Structured container: `.mdkv` is a ZIP with `manifest.yaml` and `tracks/` directory
- Track types: `primary`, `translation`, `commentary`, `code`, `reference`, `media_ref`, `revision`
- Validation: required fields, primary track, path uniqueness, content heuristics, version format
- Search: regex across tracks with type/language filters, case-insensitive support
- Export: Markdown (filtered, with frontmatter), HTML (with type filtering), individual files
- Diff: compare two documents with structured `DiffResult`
- Stats: `DocumentStats` with track counts, characters, lines, languages
- CLI + Python API: create, inspect, modify, search, validate, export, import, diff, stats
- Type safety: `py.typed` marker for PEP 561
- Security: path traversal prevention, YAML-safe headers, HTML comment injection prevention

## Development

```bash
uv run pytest -q --cov=mdkv --cov-report=term-missing
uv run sphinx-build -b html docs docs/_build/html
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development guide.

## Roadmap

See [TODO.md](TODO.md) for planned minor, medium, and major improvements.

## Package structure

- `mdkv.core`: types, errors, validation
- `mdkv.storage`: save/load container (`MDKVFormatError`)
- `mdkv.services`: search, export, diff, stats
- `mdkv.cli`: CLI entry point (`mdkv` or `python -m mdkv`)
- `mdkv.gui`: FastAPI web GUI
- `mdkv.common`: logging utilities
- `mdkv.library`: example definition builder
- `mdkv.demo`: demo document builder

License: Apache-2.0. See the `LICENSE` file.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
