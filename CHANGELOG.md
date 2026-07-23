# Changelog

All notable changes to MDKV are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2025-07-22

### Added
- `mdkv.services.diff` module with `diff_documents()` and `DiffResult` dataclass
- `mdkv.services.stats` module with `compute_stats()` and `DocumentStats` dataclass
- CLI `add-track --file` option to read content from a file
- CLI `update-track --file` option to read content from a file
- CLI `validate --json` flag for machine-readable JSON output
- CLI `export --metadata-header` flag for YAML frontmatter in output
- GUI `/api/document` POST now supports `version` and `metadata` updates
- `DiffResult.to_dict()` and `DiffResult.has_changes` property
- `DocumentStats.to_dict()` method
- New public API exports: `diff_documents`, `DiffResult`, `compute_stats`, `DocumentStats`
- `mdkv/services/diff.py` and `mdkv/services/stats.py` in API docs

### Changed
- CLI `diff` and `stats` commands now use shared service functions (DRY)
- GUI `/api/diff` and `/api/stats` now use shared service functions (DRY)
- GUI `/api/document` POST validates field presence before updating (no more silent no-ops)
- Version bumped to 0.5.0

### Fixed
- CLI `export --metadata-header` was `is_flag=False` (required a value); now correctly `is_flag=True`

## [0.4.0] - 2025-07-22

### Security
- Fixed path traversal in `export_to_files` — `_safe_filename()` sanitizes track IDs
- Fixed YAML injection in `metadata_header` — uses `yaml.safe_dump` for frontmatter
- Fixed HTML comment injection in `to_markdown` and `render_tracks_html` — strips `-->`
- `save_mdkv` now detects and rejects duplicate track paths (prevents silent data loss)
- `_doc_from_manifest` wraps `ValueError` from `Track` constructor in `MDKVFormatError`
- GUI `/api/track` upsert validates `track_type` on both create and mutation
- GUI `/api/search` catches `re.error` for invalid regex patterns
- CLI catches `re.error` for invalid search patterns

### Changed
- All CLI commands now catch `FileNotFoundError` and `MDKVFormatError` with clean error messages
- Removed dead imports (`json` in `gui/server.py`, `__license__` in `cli/main.py`)
- Fixed misleading `--types` help text in CLI `export` command

### Added
- 19 red-team tests covering all security and bug fixes
- Security section in `docs/concept.md`

## [0.3.0] - 2025-07-22

### Added
- `__main__.py` for `python -m mdkv` execution
- `Track.to_dict()` / `Track.from_dict()` for JSON serialization
- `MDKVDocument.to_dict()` / `MDKVDocument.from_dict()` for JSON serialization
- `MDKVDocument.count_tracks_by_type()` method
- `__repr__` on `Track` and `MDKVDocument`
- `case_insensitive` flag on `search_document()`
- CLI `search -i` flag for case-insensitive search
- `metadata_header` option on `to_markdown()` and `to_html()`
- `export_to_files()` returns `List[Path]` of written files
- GUI `/api/search`, `/api/stats`, `/api/diff` endpoints
- GUI `/api/validate` returns warnings alongside errors
- GUI `/api/document` includes `version` and `created` fields
- New examples: `import_example.py`, `diff_example.py`, `stats_example.py`
- 31 new tests

### Fixed
- Eliminated all remaining `datetime.utcnow()` calls in examples, docs, and paper bundles

## [0.2.0] - 2025-07-22

### Added
- Enhanced validation: path uniqueness (ERROR), empty content (WARN), code without fences (WARN),
  translation without language (WARN), bad version format (WARN), multiple primaries (WARN)
- `ValidationIssue.track_id` field for track-level issues
- `SearchMatch` now includes `track_type` and `language`
- `to_html()` accepts `include_track_types` parameter
- `export_to_files()` returns list of written paths
- `MDKVFormatError` for corrupt containers, missing manifests, missing track files
- CLI `remove-track`, `import`, `diff`, `stats` commands
- CLI `export --types` and `--out-dir` options
- CLI `validate` displays warnings
- `py.typed` marker (PEP 561)
- `.gitignore` fail-closed pattern for `*.mdkv`
- `httpx` in dev dependencies
- 33 new tests

### Fixed
- `datetime.utcnow()` deprecation in `cli/main.py`, `demo.py`, `library.py`
- `__import__("datetime")` antipattern in `library.py`

## [0.1.0] - 2025-01-01

### Initial release
- Zip-based `.mdkv` container with `manifest.yaml` and `tracks/`
- Track types: primary, translation, commentary, code, reference, media_ref, revision
- Validation, search, export (Markdown/HTML), CLI
- FastAPI web GUI
- Library builder from YAML definitions
- Demo document builder
- Sphinx documentation
