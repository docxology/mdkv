# MDKV — Upcoming Improvements TODO

Last updated: 2025-07-23  
Current version: 0.6.0  
Tests: 180 passing, 91% coverage  

## Completed (v0.2.0–v0.6.0)

All minor documentation polish and most medium feature improvements have been
shipped. See [CHANGELOG.md](CHANGELOG.md) for the full history.

### Minor — all done ✓

- [x] docs/usage.md: all CLI commands documented (get-meta, set-meta, rename-track, update-track, license)
- [x] docs/usage.md: all new flags documented (--file, --json, --metadata-header, -i)
- [x] docs/usage.md: Python API examples for diff_documents(), compute_stats(), DiffResult, DocumentStats
- [x] docs/cli.md: --file, --json, --metadata-header flag documentation
- [x] docs/cli.md: get-meta, set-meta, license command sections
- [x] docs/format.md: MDKVFormatError documentation in error handling section
- [x] pyproject.toml: removed redundant [dependency-groups] section
- [x] pyproject.toml: added [tool.pytest.ini_options] with testpaths and filterwarnings
- [x] pyproject.toml: added [tool.coverage.run] and [tool.coverage.report]
- [x] CI: removed separate httpx install (now in dev deps)
- [x] CONTRIBUTING.md: created with full development guide
- [x] .cursorrules: updated with services.diff/stats, security section, all CLI flags
- [x] README.md: mentions python -m mdkv in Quickstart

### Medium — 13 of 14 done ✓

- [x] Track.__eq__ and Track.__hash__ for proper equality comparison
- [x] MDKVDocument.track_ids property
- [x] MDKVDocument.move_track(track_id, after_id) for reordering
- [x] search_document limit parameter
- [x] CLI export --format json and --format html
- [x] CLI info --format table
- [x] GUI POST /api/import endpoint
- [x] GUI GET /api/document/json endpoint
- [x] validate_track() function for single-track validation
- [x] Reserved track_id validation (all, none, null, true, false)
- [x] examples/diff_stats_example.py
- [x] library/definitions/media_refs.yaml (exercises media_ref track type)
- [x] docs/security.md page with full defense-in-depth documentation

## Remaining — Medium

- [ ] **Storage**: Add `save_mdkv_compressed(doc, path, compression_level)` for configurable ZIP compression. Current `save_mdkv` uses `ZIP_DEFLATED` with default level; this would allow `ZIP_STORED` (no compression, faster for already-compressed content) or higher compression levels.

## Remaining — Major (architectural / new subsystems)

- [ ] **PDF export**: Add `to_pdf(doc, output_path)` service using `weasyprint` or `pandoc` — render Markdown to PDF. Would add `weasyprint` as optional dependency.
- [ ] **EPUB export**: Add `to_epub(doc, output_path)` service — render to EPUB e-book format. Would add `ebooklib` as optional dependency.
- [ ] **Track versioning**: Add `TrackHistory` to track content revisions within a document — store diffs between versions. Requires a new `revision` track management subsystem.
- [ ] **Batch operations CLI**: `mdkv batch` subcommand to run operations across multiple .mdkv files (e.g., `mdkv batch validate *.mdkv`, `mdkv batch stats *.mdkv --format table`).
- [ ] **Plugin system**: Extensible track type registry — allow users to register custom track types with validation rules via entry points or a registration API.
- [ ] **Incremental save**: `save_mdkv` currently rewrites the entire ZIP; add incremental update mode that only writes changed tracks. Requires tracking which tracks changed since last save.
- [ ] **CLI shell completions**: Generate bash/zsh/fish completion scripts via `mdkv --generate-completions`. Click has built-in support via `click.shell_completion`.
- [ ] **GUI drag-and-drop reordering**: Add track drag-and-drop reordering in the web UI using HTML5 Drag and Drop API or a library like SortableJS.
- [ ] **GUI split-pane diff viewer**: Side-by-side comparison of two documents in the web UI. Would use the existing `diff_documents()` service.
- [ ] **GUI dark/light theme toggle**: Add CSS theme toggle with `prefers-color-scheme` support.
- [ ] **Async search**: For very large documents, add async search with pagination. Would require `asyncio` and possibly streaming results.
- [ ] **Schema validation**: Use JSON Schema or Pydantic models for manifest validation (more rigorous than current dict checks). Would add `pydantic` as optional dependency.
- [ ] **Internationalization**: i18n for CLI messages (currently all English). Would use `gettext` or `babel`.
- [ ] **Performance benchmarks**: Add `tests/test_benchmarks.py` with large-document profiling. Would use `pytest-benchmark`.
- [ ] **Type stubs audit**: `py.typed` is present but ensure all edge cases pass `mypy --strict` and `pyright`.
