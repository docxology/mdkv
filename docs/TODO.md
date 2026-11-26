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

## Workflowz review — 2026-11-10

- [ ] **MR-1 — P2: Make strict mypy usable with the repository's pinned Python 3.15 development toolchain.** Outcome: the normal project-environment mypy check runs without interpreter/stub resolution failures while retaining meaningful strict checking. Evidence: `.python-version:1` selects 3.15; `pyproject.toml:66` pins mypy analysis to 3.11; `pyproject.toml:73-75` lists only selected third-party import overrides. Probe: from the repository root, run `uv run mypy mdkv tests`; require exit 0 with no missing-import or module-attribute errors, and no change to `.python-version` or blanket removal of strict checking. Dependencies/constraints: reconcile the existing 3.11 analysis target with the declared 3.15 workflow; add only evidence-backed, compatible typing configuration/dependencies and do not prescribe runtime dependency upgrades.
- [ ] **MR-2 — P2: Align Sphinx exclusions with the documentation source directory.** Outcome: intended docs guidance is excluded without Sphinx interpreting it as a documentation page or emitting warnings under the declared strict build. Evidence: `docs/conf.py:26` excludes the root-style `README.md` path although `SOURCEDIR` is `docs` in `docs/Makefile:5`; `docs/AGENTS.md:7` requires the `-W` docs build. Probe: from the repository root, run `uv run sphinx-build -b html docs docs/_build/html -W`; require exit 0 and completed HTML output with intended exclusions preserved. Dependencies/constraints: follow `docs/AGENTS.md`; do not suppress warnings globally or remove intended exclusions for `AGENTS.md` and `_build`.
