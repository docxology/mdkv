# MDKV — Upcoming Improvements TODO

Last updated: 2025-07-23  
Current version: 0.5.0  
Tests: 150 passing, 91% coverage  

## Minor (documentation polish + small fixes)

- [ ] **docs/usage.md**: Add documentation for `get-meta`, `set-meta`, `rename-track`, `update-track`, and `license` commands (currently missing)
- [ ] **docs/usage.md**: Add documentation for `--file`, `--json`, `--metadata-header`, `-i` flags
- [ ] **docs/usage.md**: Add Python API examples for `diff_documents()`, `compute_stats()`, `DiffResult`, `DocumentStats`
- [ ] **docs/cli.md**: Add `--file`, `--json`, `--metadata-header` flag documentation to the relevant commands
- [ ] **docs/cli.md**: Add `get-meta`, `set-meta`, `license` command sections (currently missing)
- [ ] **docs/format.md**: Add `MDKVFormatError` documentation to the error handling section
- [ ] **pyproject.toml**: Remove redundant `[dependency-groups]` section (conflicts with `[project.optional-dependencies]`)
- [ ] **pyproject.toml**: Add `[tool.pytest.ini_options]` section with `testpaths = ["tests"]` and `minversion = "7.0"`
- [ ] **pyproject.toml**: Add `[tool.coverage.run]` section with `source = ["mdkv"]` and `omit = ["tests/*"]`
- [ ] **CI**: Remove `uv run pip install httpx` from ci.yml (httpx is now in dev dependencies)
- [ ] **CONTRIBUTING.md**: Create contributing guide referencing test/build/lint workflow
- [ ] **.cursorrules**: Add `services.diff` and `services.stats` to the package structure and CLI/GUI sections
- [ ] **README.md**: Mention `python -m mdkv` as alternative to `mdkv` entry point in Quickstart

## Medium (feature improvements)

- [ ] **Track.__eq__**: Add equality comparison to `Track` (compare all fields) — enables proper `==` semantics for diff/testing
- [ ] **MDKVDocument.track_ids**: Add `track_ids` property as `list(self.tracks.keys())` for convenience
- [ ] **move_track(track_id, after_id)**: Reorder tracks within a document by reinserting at a new position
- [ ] **search_document**: Add `limit` parameter to cap the number of matches returned (prevent DoS via catastrophic backtracking)
- [ ] **CLI `export --format json`**: Export the full document as JSON (`doc.to_dict()`) for programmatic consumption
- [ ] **CLI `info --json`**: Already JSON; add `--format table` for human-readable table output
- [ ] **GUI**: Add `POST /api/import` endpoint to import a Markdown file into the loaded document as a new track
- [ ] **GUI**: Add `GET /api/document/json` endpoint returning `doc.to_dict()` for full JSON export
- [ ] **Validation**: Add `validate_track(track)` function for single-track validation (not just document-level)
- [ ] **Validation**: Add check for reserved track_id values (e.g., "all", "None") that could confuse the GUI
- [ ] **Storage**: Add `save_mdkv_compressed(doc, path, compression_level)` for configurable ZIP compression
- [ ] **Examples**: Add `diff_stats_example.py` demonstrating `diff_documents()` + `compute_stats()` together
- [ ] **Library**: Add a `media_ref` track type example to the definitions (currently no definition exercises it)
- [ ] **Docs**: Add `docs/security.md` page documenting all defense-in-depth measures (path traversal, YAML injection, HTML comment injection, etc.)

## Major (architectural / new subsystems)

- [ ] **PDF export**: Add `to_pdf(doc, output_path)` service using `weasyprint` or `pandoc` — render Markdown to PDF
- [ ] **EPUB export**: Add `to_epub(doc, output_path)` service — render to EPUB e-book format
- [ ] **Track versioning**: Add `TrackHistory` to track content revisions within a document — store diffs between versions
- [ ] **Batch operations CLI**: `mdkv batch` subcommand to run operations across multiple .mdkv files (e.g., `mdkv batch validate *.mdkv`)
- [ ] **Plugin system**: Extensible track type registry — allow users to register custom track types with validation rules
- [ ] **Incremental save**: `save_mdkv` currently rewrites the entire ZIP; add incremental update mode that only writes changed tracks
- [ ] **CLI shell completions**: Generate bash/zsh/fish completion scripts via `mdkv --generate-completions`
- [ ] **GUI**: Add track drag-and-drop reordering in the web UI
- [ ] **GUI**: Add split-pane diff viewer (side-by-side comparison of two documents)
- [ ] **GUI**: Add dark/light theme toggle
- [ ] **Async search**: For very large documents, add async search with pagination
- [ ] **Schema validation**: Use JSON Schema or Pydantic models for manifest validation (more rigorous than current dict checks)
- [ ] **Internationalization**: i18n for CLI messages (currently all English)
- [ ] **Performance benchmarks**: Add `tests/test_benchmarks.py` with large-document profiling
- [ ] **Type stubs**: Publish type stubs package or ensure `py.typed` covers all edge cases for mypy/pyright
