# MDKV — Upcoming Improvements TODO

Last updated: 2025-07-23
Current version: 0.6.0
Tests: 180 passing, 91% coverage
Coverage gaps: `gui/server.py` at 71% (render endpoints, library build, favicon)

## Minor — fixable in <1 hour each

### Documentation gaps from v0.6.0 features

- [ ] **docs/architecture.md**: Add `validate_track()`, `Track.__eq__`/`__hash__`, `move_track()`, `track_ids` property, `search limit` parameter, and reserved track_id validation to the model/search/validation sections. These features were shipped in v0.6.0 but architecture.md was not updated.

- [ ] **docs/usage.md**: Add Python API examples for `validate_track()`, `move_track()`, and `track_ids` property. These are new public API but have no usage examples.

- [ ] **docs/cli.md**: Add documentation for `info --format table` and `export --format json`. Also add `--limit` to the search section once implemented (see below).

- [ ] **docs/format.md**: Add reserved track_id validation rules to the validation section. Add `validate_track()` to the validation rules section.

- [ ] **docs/api.rst**: Add `validate_track` to the Validation automodule section (it's exported from `mdkv.core.validate` but not mentioned in the RST).

- [ ] **.cursorrules**: Add `Track.__eq__`/`__hash__`, `track_ids` property, `move_track()`, `validate_track()`, `search limit`, and reserved ID validation to the Model API, Search, Validation, and CLI sections.

- [ ] **README.md**: Add `validate_track`, `move_track`, `track_ids` to the Python API examples section.

### CLI gaps

- [ ] **CLI `search --limit N`**: The `search_document()` function already supports `limit=N` but the CLI `search` command doesn't expose it. Add `@click.option("--limit", type=int, default=None)` and pass it through. Files: `mdkv/cli/main.py` lines ~191-220.

- [ ] **CLI `move-track` command**: The model has `move_track()` but there's no CLI command. Add `@main.command("move-track")` with `--id` and `--after-id` options. Files: `mdkv/cli/main.py`.

### GUI gaps

- [ ] **GUI `POST /api/move-track`**: Model has `move_track()` but GUI has no endpoint. Add endpoint accepting `{"track_id": "...", "after_id": "..."}`. Files: `mdkv/gui/server.py`.

- [ ] **GUI `GET /api/validate-track`**: `validate_track()` exists but GUI has no per-track validation endpoint. Add `GET /api/validate-track?track_id=...`. Files: `mdkv/gui/server.py`.

- [ ] **GUI `/api/search` `limit` parameter**: `search_document()` supports `limit` but GUI search endpoint doesn't accept it. Add `limit: int = 0` query param. Files: `mdkv/gui/server.py` lines ~277-306.

### Community files

- [ ] **CODE_OF_CONDUCT.md**: Create standard Contributor Covenant file. Reference in CONTRIBUTING.md.

- [ ] **GitHub issue templates**: Create `.github/ISSUE_TEMPLATE/bug_report.md` and `feature_request.md`.

- [ ] **GitHub PR template**: Create `.github/PULL_REQUEST_TEMPLATE.md` with the checklist from CONTRIBUTING.md.

## Medium — new features, 1-4 hours each

- [ ] **Configurable ZIP compression**: Add `save_mdkv_compressed(doc, path, compression_level=6)` or add `compression` and `compresslevel` kwargs to `save_mdkv`. Default: `ZIP_DEFLATED` level 6. Allow `ZIP_STORED` (no compression) and `ZIP_DEFLATED` with level 0-9. Files: `mdkv/storage/io.py`. Test: roundtrip with each compression level. This matters for large documents with already-compressed media content.

- [ ] **CLI `export --format json` with `--types` filter**: Currently `export --format json` exports the entire document. Add support for filtering tracks by type in JSON mode (return only matching tracks in the `tracks` list). Files: `mdkv/cli/main.py`.

- [ ] **GUI dark/light theme toggle**: Add CSS `prefers-color-scheme` support and a manual toggle button in the toolbar. Store preference in `localStorage`. Files: `mdkv/gui/static/style.css`, `mdkv/gui/static/main.js`, `mdkv/gui/static/index.html`.

- [ ] **Performance benchmarks**: Add `tests/test_benchmarks.py` that profiles save/load/search/export on synthetic large documents (1000 tracks, 1MB content each). Use `pytest-benchmark` as optional dev dependency. Assert operations complete within time bounds.

- [ ] **Type stubs audit**: Run `mypy --strict mdkv/` and `pyright --strict mdkv/`, fix all type errors. The `py.typed` marker is present but the codebase hasn't been audited under strict mode. Focus on `gui/server.py` (FastAPI dict payloads need `TypedDict`), `cli/main.py` (Click type hints), and `core/model.py` (dataclass field types).

## Major — new subsystems, days of work each

- [ ] **PDF export service**: Add `mdkv/services/pdf.py` with `to_pdf(doc, output_path, include_track_types=None)`. Use `weasyprint` to render `to_markdown()` output to PDF. Add `weasyprint` as optional dependency in `[project.optional-dependencies]` under a `pdf` extra. Add CLI `export --format pdf`. Add GUI `GET /api/render/pdf`. Test: generate PDF, verify file exists and is non-empty. Consider `pandoc` as fallback if `weasyprint` is unavailable.

- [ ] **EPUB export service**: Add `mdkv/services/epub.py` with `to_epub(doc, output_path, include_track_types=None)`. Use `ebooklib` to build an EPUB from `to_markdown()` output. Add `ebooklib` as optional dependency under an `epub` extra. Add CLI `export --format epub`. Test: generate EPUB, verify it's a valid ZIP with `mimetype` entry.

- [ ] **Track versioning subsystem**: Add `mdkv/core/history.py` with `TrackHistory` dataclass storing a list of `(timestamp, content)` tuples per track_id. Integrate with `revision` track type: when a track is updated, optionally store the previous content as a revision entry. Add `MDKVDocument.get_track_history(track_id)` and `MDKVDocument.restore_track_version(track_id, timestamp)`. Add CLI `history` and `restore` commands. This is the most architecturally complex remaining item.

- [ ] **Batch operations CLI**: Add `@main.group("batch")` with subcommands: `batch validate`, `batch stats`, `batch search`, `batch export`. Each accepts multiple paths via `@click.argument("paths", nargs=-1)`. Output aggregates results per-file. Example: `mdkv batch validate *.mdkv --json | jq '.[] | select(.ok == false)'. Files: `mdkv/cli/main.py`.

- [ ] **Plugin system for track types**: Add `mdkv/core/registry.py` with `TrackTypeRegistry` class. Allow registering custom track types with display names, validation rules, and content heuristics via `register_track_type(name, validator_fn, heuristics_fn)`. Use Python entry points (`[project.entry-points."mdkv.track_types"]`) for third-party plugins. Modify `allowed_track_types()` to consult the registry. Update `Track.__post_init__` to validate against the registry.

- [ ] **Incremental save**: Add `save_mdkv_incremental(doc, path)` that opens the existing ZIP in append mode, removes only changed track files, and writes new ones. Requires tracking dirty tracks: add `MDKVDocument._dirty: set[str]` and mark on `add_track`/`update_track_content`/`remove_track`/`rename_track`/`move_track`. Clear on successful save. Use `zipfile.ZipFile(path, mode='a')` to append. Fallback to full `save_mdkv` if the file doesn't exist or is corrupt.

- [ ] **CLI shell completions**: Add `@main.command("generate-completions")` that outputs completion scripts for bash, zsh, and fish. Use `click.shell_completion` which is built into Click 8+. Document in `docs/cli.md`. Test: verify generated scripts are syntactically valid.

- [ ] **GUI drag-and-drop track reordering**: Add SortableJS (or vanilla HTML5 Drag and Drop) to the track filter checkboxes in the GUI. On reorder, call `POST /api/move-track` with the new position. Files: `mdkv/gui/static/main.js`, `mdkv/gui/static/index.html`, `mdkv/gui/static/style.css`. Requires the `/api/move-track` endpoint (see Minor).

- [ ] **GUI split-pane diff viewer**: Add a diff view mode to the GUI that shows two documents side-by-side with highlighted differences. Uses `diff_documents()` service. New endpoint `GET /api/diff/view?path=other.mdkv` returning HTML with diff highlights. Files: `mdkv/gui/server.py`, `mdkv/gui/static/main.js`, `mdkv/gui/static/index.html`. Consider using `difflib.HtmlDiff` for rendering.

- [ ] **Async search with pagination**: For documents with many large tracks, make `search_document` an async generator that yields matches. Add `search_document_async(doc, pattern, ...)` returning `AsyncIterator[SearchMatch]`. Add GUI `GET /api/search/stream` using Server-Sent Events. Add `limit` and `offset` for pagination. Files: `mdkv/services/search.py`, `mdkv/gui/server.py`.

- [ ] **Schema-based manifest validation**: Replace the manual dict key checks in `_doc_from_manifest` with a Pydantic model (`ManifestSchema`) or JSON Schema. Add `pydantic` as optional dependency. Validate manifest structure, track entries, and field types in one pass. Catch `ValidationError` and wrap in `MDKVFormatError`. Files: `mdkv/storage/io.py`. Benefit: catches type errors (e.g., `authors` as string instead of list) that current checks miss.

- [ ] **Internationalization (i18n)**: Wrap all CLI user-facing strings in `gettext()`. Create `mdkv/locales/` with `.po`/`.mo` files for at least Spanish and French. Add `--lang` CLI option. Use `babel` for extraction. Files: `mdkv/cli/main.py`, new `mdkv/i18n.py` module. Low priority — current user base is English-only.
