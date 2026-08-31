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
- No mock framework in tests; run `uv run pytest -q` from the repo root.
  GUI: `uv run python run_gui.py`.
- LOCAL-ONLY tree under `projects/ongoing/` — never commit. Parent standard:
  `/Volumes/external_drive/Git/template/projects/ongoing/AGENTS.md`.

## Layout map

- `mdkv/core/` — model, errors, history, registry, validate.
- `mdkv/services/` — diff, export, pandoc_export, search, stats.
- `mdkv/storage/` — io, schema (zip container persistence).
- `mdkv/cli/` — argparse CLI entrypoint (`mdkv.cli`).
- `mdkv/gui/` — local GUI server (`run_gui.py`) + static assets.
- `tests/` — pytest suite (cli, gui, export, search, storage, redteam, ...).

## Gotchas

- This directory is reached through a symlink from
  `projects/ongoing/File_Types/mdkv`; edit here (canonical), not through
  lane copies.
- `_built/` and `paper/_bundle/` are generated artifacts; regenerate via the
  build scripts rather than hand-editing.

## Undocumented subfolders (fleet note, 2026-08-29)

`mdkv/mdkv/*` subpackages, `mdkv/locales/*`, `demo/`, `tests/`,
`library/_built/` carry no per-folder AGENTS/README pairs beyond this file;
`examples/` and `docs/` have READMEs. Verify with the coverage script.

## Status pointers (2026-08-31)

- Current version: single source is `version` in `pyproject.toml`; release history lives only in `CHANGELOG.md` (TODO.md may reference it, never restate it).
- Test/coverage status: verify with `uv run pytest -q --cov=mdkv --cov-report=term-missing` from repo root; dated claims live in `TODO.md`.
- Next actions: `TODO.md` ("Backlog — open items" section).

## Gotchas (local env, 2026-08-31)

- On this host (macOS, external drive), `uv run pytest` on the default Python 3.14 fails: `pydantic-core` 2.33.2 has no 3.14 wheel here and its source build fails. Workaround: `uv sync -p 3.12 && uv run -p 3.12 pytest -q`. CI pins 3.14 on ubuntu where the wheel exists, so this is a local-env note, not a repo defect.

## Round 2 additions (2026-08-31)

- `scripts_status.py` (repo root): executable status truth — `uv run python scripts_status.py` prints date + version; `--tests` also runs the suite and prints test count + coverage. README and TODO.md reference it instead of undated prose claims.
