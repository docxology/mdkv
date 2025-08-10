# Architecture

MDKV is split into clear layers:

- `mdkv.core`: domain model and validation
- `mdkv.storage`: read/write `.mdkv` containers
- `mdkv.services`: search and export utilities
- `mdkv.cli`: user-facing command line interface

## Package responsibilities

- `core.model`:
  - `Track`, `MDKVDocument`, helper methods, allowed track types
- `core.validate`:
  - minimal validation (required metadata + primary track)
- `storage.io`:
  - ZIP packaging, YAML manifest read/write
- `services.search`:
  - regex search with track type/language filters
- `services.export`:
  - multi-track Markdown export and primary-HTML rendering
- `cli.main`:
  - `init`, `info`, `validate`, track ops, search, export

## Data flow

1. CLI/API creates an `MDKVDocument`, adds tracks
2. `storage.save_mdkv()` writes a ZIP with manifest and `tracks/`
3. `storage.load_mdkv()` reconstructs the document
4. `services.search/export` operate on the in-memory document

## Extension points

- Additional track types with domain-specific meaning
- Alternate exporters (PDF/EPUB) built on `to_markdown()`
- Richer validation rules in `core.validate`
