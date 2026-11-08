# MDKV — Upcoming Improvements TODO

Last updated: 2026-11-08 (release merged; dependency refresh in review)
Current source version: 0.12.0; source is merged on `main`, while tag/GitHub release publication remains a separate authorized step.
Fresh post-audit baseline: 571 passed, 95.07% coverage on Python 3.15.2, and 571 passed on Python 3.11.18; PR #2 merged as `1dbad9a`, CI run 42513537263 green. Historical 2026-08-31 report: 306 passed / 3 failed; the old I/O-timeout explanation was reported, not independently established.

## Backlog — open items

New work goes here, one line per entry with file path(s). Move completed items
into the archive below with a `[x]` and a date. Entry doc: `README.md`;
release history: `CHANGELOG.md` (its single canonical home).

### Minor
- [x] CHANGELOG `[0.11.0]` entry added (2026-08-31); coverage claim re-measured 2026-08-31: 306 passed / 3 timeout-flaky failed (slow external drive), 99% TOTAL coverage — CHANGELOG + this file updated together.
- [x] Fresh baseline on 2026-11-07: all 309 pre-audit tests passed under pinned Python 3.15.2. This resolves current reproduction status, not the historical failures' cause.

### Medium
- [x] Dated status surface now exists: `scripts_status.py` prints date/version (+ tests/coverage with `--tests`); `README.md` Development section points to it and to this file.

### Major
- [x] `scripts_status.py` added (2026-08-31): executable status truth (date, version from pyproject.toml; test count + coverage with `--tests`). README Development section references it.

## Historical completed work

The following dated reports describe earlier work, not current acceptance or
proof that the new candidate has been merged/tagged/published:

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
- [x] **Coverage expansion**: Increased test suite to 309 tests; 100% statement coverage as measured 2026-08-19, re-measured 2026-08-31 at 99% TOTAL (see header).

