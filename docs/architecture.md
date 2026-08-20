# Architecture

MDKV is split into clear layers:

- `mdkv.core`: domain model and validation
- `mdkv.storage`: read/write `.mdkv` containers
- `mdkv.services`: search and export utilities
- `mdkv.cli`: user-facing command line interface
- `mdkv.gui`: FastAPI web GUI with REST API
- `mdkv.common`: logging utilities
- `mdkv.library`: example definition builder
- `mdkv.demo`: demo document builder

## Package responsibilities

- `core.model`:
  - `Track`, `MDKVDocument`, helper methods, allowed track types
  - `Track.to_dict()` / `Track.from_dict()` for JSON serialization
  - `MDKVDocument.to_dict()` / `MDKVDocument.from_dict()` for JSON serialization
  - `MDKVDocument.count_tracks_by_type()` for statistics
  - `MDKVDocument.track_ids` property — ordered list of track IDs
  - `MDKVDocument.move_track()` — reorder tracks within document
  - `Track.__eq__()` / `Track.__hash__()` — equality and hashing (path-based)
  - `__repr__` on both classes for debugging
- `core.validate`:
  - `validate_track()` — validate a single Track in isolation
  - ERROR-level: required metadata, primary track, path uniqueness
  - WARN-level: empty content, code without fences, translation without language, bad version, multiple primaries, reserved track_id
  - Reserved track_ids: `all`, `none`, `null`, `true`, `false`, `""` (empty string)
  - `ValidationIssue` carries `track_id` for track-level issues
- `core.errors`:
  - `ValidationError` exception
- `storage.io`:
  - ZIP packaging, YAML manifest read/write
  - `MDKVFormatError` for corrupt containers, missing manifests, missing track files
  - `FileNotFoundError` for missing files
- `services.search`:
  - Regex search with track type/language filters
  - `case_insensitive` convenience flag
  - `limit` parameter to cap results
  - `SearchMatch` includes `track_type` and `language`
- `services.export`:
  - `to_markdown()` with optional `include_track_types` and `metadata_header`
  - `to_html()` with optional `include_track_types` and `metadata_header`
  - `export_to_files()` returns list of written paths
  - `_safe_filename()` prevents path traversal in file export
- `services.diff`:
  - `diff_documents()` compares two documents
  - `DiffResult` dataclass with `has_changes` and `to_dict()`
  - Detects content, type, language, and path changes
- `services.stats`:
  - `compute_stats()` aggregates document statistics
  - `DocumentStats` dataclass with `to_dict()`
- `services.pandoc_export`:
  - `to_pdf()`, `to_epub()`, `to_docx()` via pandoc subprocess
  - Mirrors docxology/template rendering approach (no new Python deps)
- `core.history`:
  - `TrackHistory` and `TrackVersion` for content revision history
  - `add_version()`, `get_current()`, `get_version_at()`, `restore_to()`
- `core.registry`:
  - `TrackTypeRegistry` for custom track type registration
  - `register_track_type()`, `get_registry()`
- `i18n`:
  - `set_language()`, `gettext()` for internationalization
  - Falls back to English; reads `MDKV_LANG`/`LANG` env vars
- `storage.io`:
  - `save_mdkv_incremental()` for atomic incremental saves
  - `save_mdkv()` with configurable compression and compresslevel
- `cli.main`:
  - `init`, `info`, `validate`, track ops (add/remove/rename/update), search, export
  - `import` — import a Markdown file as a new .mdkv
  - `diff` — compare two .mdkv documents
  - `stats` — document statistics
  - `gui` — launch web GUI
- `gui.server`:
  - FastAPI app with CRUD endpoints for documents and tracks
  - `/api/search`, `/api/stats`, `/api/diff` REST endpoints
  - `/api/render/*` for HTML/Markdown rendering
  - `/api/library` for example documents
  - `/api/validate` returns warnings alongside errors

## Data flow

1. CLI/API creates an `MDKVDocument`, adds tracks
2. `storage.save_mdkv()` writes a ZIP with manifest and `tracks/`
3. `storage.load_mdkv()` reconstructs the document
4. `services.search/export` operate on the in-memory document
5. `MDKVDocument.to_dict()` / `from_dict()` for JSON serialization

## Extension points

- Additional track types with domain-specific meaning
- Alternate exporters (PDF/EPUB) built on `to_markdown()`
- Richer validation rules in `core.validate`
- Additional CLI commands wrapping service-layer functions
- Additional GUI API endpoints for new operations

## Public API

Re-exported from `mdkv.__init__`:
- `MDKVDocument`, `Track`, `allowed_track_types`
- `ValidationError`, `validate_document`, `validate_track`, `ValidationIssue`
- `TrackHistory`, `TrackVersion`, `TrackTypeRegistry`, `register_track_type`, `get_registry`
- `search_document`, `search_document_async`, `SearchMatch`
- `to_markdown`, `to_html`, `export_to_files`
- `diff_documents`, `DiffResult`
- `compute_stats`, `DocumentStats`
- `to_pdf`, `to_epub`, `to_docx`
- `save_mdkv`, `save_mdkv_incremental`, `load_mdkv`, `MDKVFormatError`
- `MDKVManifestModel`, `TrackManifestModel`

Type safety: `py.typed` marker present (PEP 561).
