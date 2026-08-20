# MDKV — Upcoming Improvements TODO

Last updated: 2026-08-19
Current version: 0.11.0
Tests: 309 passing, 100% coverage

## All items completed

All minor, medium, and major improvements scoped for this phase have been
implemented and verified:

### Completed Minor Improvements
- [x] **GUI /api/library coverage & edge cases**: Full test coverage of `/api/library` (pre-built vs fresh build) and GUI error paths in `gui/server.py` (100% GUI coverage).
- [x] **Typing audits & TypedDicts in GUI**: Added complete typing annotations and dict types across FastAPI handlers in `gui/server.py`.
- [x] **Documentation polish & consistency**: Sphinx HTML build verified with zero warnings (`-W`), docstrings updated, and public API tables refreshed.

### Completed Medium Improvements
- [x] **Schema-based manifest validation**: Introduced `MDKVManifestModel` and `TrackManifestModel` via Pydantic (`mdkv/storage/schema.py`) integrated into `storage.io`.
- [x] **Strict mypy compliance across all modules**: Configured strict mode in `pyproject.toml`, achieving 100% clean check across 32 source files.
- [x] **Ruff linting & formatting cleanup**: Resolved all lint/format warnings with zero errors remaining.

### Completed Major Improvements
- [x] **i18n translation files & runtime infrastructure**: Created and compiled `.po`/`.mo` translation files for Spanish (`es`) and French (`fr`) with UTF-8 headers and CLI integration.
- [x] **Core engine & storage optimizations**: Streamlined track movement ordering logic, safe filename sanitization, and fallback resilience.
- [x] **Comprehensive roundtrip & corruption validation suites**: Added exhaustive roundtrip tests, corrupt ZIP / scalar YAML checks, and edge-case validations.
- [x] **Coverage expansion to 100%**: Increased test suite to 309 tests with 100% statement coverage across every module in `mdkv`.

