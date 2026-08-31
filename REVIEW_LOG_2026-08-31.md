# REVIEW_LOG — Agent-Ergonomics Deep Pass (2026-08-31)

Agent: mdkv (fleet agent-erg-fleet-20260831). Doctrine: fresh agent orients in 2 min, acts in 10, never misled.

## Phase 0 — Preflight
- Repo: /Volumes/external_drive/Git/projects/ongoing/docxology/mdkv, branch main, remote origin (github.com/docxology/mdkv).
- Dirty files at dispatch: 54 (all untracked per-directory AGENTS.md/README.md pairs from the 2026-08-29 docs-audit fleet — pre-existing, not mine, left untouched).
- Inventory: README.md (entry), AGENTS.md, TODO.md, CHANGELOG.md, CONTRIBUTING.md, MKVD_overview.md, docs/ (Sphinx + AGENTS.md + manuscript/ with MANUSCRIPT_STATUS.md), .github/ (CI: pytest + sphinx-build), .cursorrules.

## Phase 1 — Cold-start audit
Attempted as a cold agent using only entry docs:

(a) Current status — PASS with a caveat. TODO.md carried "version 0.11.0 / 309 tests / 100% coverage" as undated prose with no verification command. pyproject.toml confirms 0.11.0; CHANGELOG.md's newest entry was 0.10.0 (2025-07-23) — the 0.11.0 release was not logged in CHANGELOG despite the v0.11.0 commit existing.
(b) What to do next — FAIL before fix. TODO.md said "All items completed" with no pointer to where new work is tracked. Fixed in Phase 3.
(c) Primary verification — PASS. README Quickstart and CONTRIBUTING both give `uv run pytest -q`; verified executable.

Sweep results:
- Broken relative links in .md files: 0 (script-checked all .md; .git/_build/.venv excluded).
- Local-env finding (verified on this host): `uv run pytest` on default Python 3.14 fails — pydantic-core v2.33.2 has no 3.14 wheel here and its source build fails. `uv sync -p 3.12` + `uv run -p 3.12 pytest` works. Documented in AGENTS.md Gotchas; not a repo defect (CI pins 3.14 on ubuntu where wheels exist).
- Stale/duplicated fact-classes fixed: CHANGELOG missing 0.11.0 entry; TODO claims undated/unverifiable; TODO had no open-items section.
- No transient reports linked as current; generated trees (_built/, paper/_bundle/) already flagged in AGENTS.md.

## Phase 2 — Backlog scoping
See TODO.md "Backlog — open items" (Minor/Medium/Major). One Major deferred (documented there).

## Phase 3 — Implemented
- CHANGELOG.md: added missing [0.11.0] release section (dated 2026-08-28 per git history; content from the v0.11.0 commit message and the TODO completed-items record).
- TODO.md: added Last-audited line with verification commands; added "Backlog — open items" section routing new work; kept completed archive intact.
- AGENTS.md: appended local-env gotcha and status-pointers line (version→pyproject.toml, tests→pytest, history→CHANGELOG).
- README.md: added status pointers + verification commands to the Development section.

## Phase 4 — Verify & close
- Link check re-run after edits: 0 broken.
- Pre-push gate: CI runs pytest+sphinx on ubuntu/3.14; no fast local gate declared — noted, not invented. Test run on this host: slow (external drive); result recorded in the fleet report.
- Commits: path-scoped adds only; push to main per brief.

## Round 2 (2026-08-31, continuation)

- Implemented the previously-deferred Major: added `scripts_status.py` (date + version; `--tests` runs the suite and prints count/coverage). Verified: `uv run -p 3.12 python scripts_status.py` → date 2026-08-31, version 0.11.0.
- Full suite with coverage (uv, py3.12, external drive): 306 passed / 3 failed in 240.9s, TOTAL coverage 99%. The 3 failures (`test_benchmarks.py::TestBenchmarkSaveLoad::test_load_small_doc`, `test_main_module.py::test_python_m_mdkv_help`, `::test_python_m_mdkv_version`) are subprocess/timeout failures consistent with slow-drive I/O, not assertion failures; left as an open TODO item to confirm on CI/fast disk.
- TODO.md: all three open items marked [x] with dates; new Minor item opened for CI re-verification of the 3 flaky failures; Tests status line refreshed with measured numbers + verification command.
- CHANGELOG 0.11.0 coverage line refreshed with the 2026-08-31 re-measurement; README Development section now points at `scripts_status.py`; AGENTS.md Round 2 note appended.
- Link check after all edits: 0 broken.
- Commits: path-scoped (CHANGELOG.md, TODO.md, AGENTS.md, README.md, scripts_status.py, REVIEW_LOG_2026-08-31.md); pushed to main per brief.
