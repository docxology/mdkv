# mdkv — Agent Notes

- Layout: package code in `mdkv/` (`cli/`, `core/`, `services/`, `storage/`,
  `gui/`, `common/`, `locales/`), tests in `tests/` (~50 real-data pytest
  modules), examples in `examples/`, demo containers in `demo/`, reusable
  content in `library/` (`definitions/` YAML + `_built/` prebuilt .mdkv).
  Docs live in `docs/` (Sphinx; see its AGENTS.md).
- The publication track is `paper/` (`mdkv_paper.md`, `paper.mdkv`,
  `build_paper_bundle.py|.sh`, `_bundle/` with CHECKSUMS + BUNDLE_INFO,
  bundled PDF) — separate from the Sphinx docs.
- MDKV format: zip-based `.mdkv` container with `manifest.yaml` and `tracks/`;
  track types primary/translation/commentary/code/reference/media_ref/revision.
  Concept overview: `MKVD_overview.md`.
- Prefer real behavioral fixtures; older orchestration tests include mocks. Run `uv run pytest -q` from the repo root.
  GUI: `uv run python run_gui.py --path <owned-fixture.mdkv>`.
- Repository-wide policy for template projects is maintained in the template repository, not restated here.

## Layout map

- `mdkv/core/` — model, errors, history, registry, validate.
- `mdkv/services/` — diff, export, pandoc_export, search, stats.
- `mdkv/storage/` — io, schema (zip container persistence).
- `mdkv/cli/` — Click-based CLI entrypoint (`mdkv.cli`; also `python -m mdkv`).
- `mdkv/gui/` — local GUI server (`run_gui.py`) + static assets.
- `tests/` — pytest suite (cli, gui, export, search, storage, redteam, ...).

## Gotchas

- This directory is reached through a symlink from
  `projects/ongoing/File_Types/mdkv`; edit here (canonical), not through
  lane copies.
- `_built/` and `paper/_bundle/` are generated artifacts; regenerate via the
  build scripts rather than hand-editing.

## Undocumented subfolders (fleet note, 2026-08-29)

`mdkv/*` subpackages (`cli`, `core`, `services`, `storage`, `gui`, `common`),
`mdkv/locales/*`, `demo/`, `tests/`, `library/_built/` carry no per-folder
AGENTS/README pairs beyond this file; `examples/` and `docs/` have READMEs.
Verify with `scripts_status.py`.

## Status pointers (2026-08-31)

- Current version: canonical source is `version` in `pyproject.toml`; `mdkv/__init__.py` mirrors it in `__version__` (used by `mdkv --version`) — bump both together. Release history lives only in `CHANGELOG.md` (TODO.md may reference it, never restate it).
- Test/coverage status: verify with `uv run pytest -q --cov=mdkv --cov-report=term-missing` from repo root; dated claims live in `TODO.md`.
- Next actions: `TODO.md` ("Backlog — open items" section).

## Gotchas (local env, 2026-08-31)

- Historical report (2026-08-31): Python 3.14/pydantic-core 2.33.2 failed locally; a Python 3.12 workaround was used then. This is not current advice: `.python-version` now selects 3.15 and the refreshed lock was installed successfully on 3.15.2 during the 2026-11-07 audit. Do not change the pin to revive an old workaround.

## Round 2 additions (2026-08-31)

- `scripts_status.py` prints source date/version; `--tests` streams the actual pytest result and propagates its exit status. Explicit trailing pytest arguments allow bounded owned-fixture checks.
