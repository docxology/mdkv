# mdkv — Agent Notes

- Layout: package code in `mdkv/`, tests in `tests/`, examples in `examples/`,
  demo in `demo/`, reusable content in `library/`. Docs live here (`docs/`).
- The publication track is `paper/` (`mdkv_paper.md`, `paper.mdkv`,
  `build_paper_bundle.py|.sh`, bundled PDF) — separate from these Sphinx docs.
- Docs maintenance: `docs/index.rst` drives the Sphinx toctree; add new `.md`
  pages there. Keep `format.md` in sync with the parser implementation in
  `mdkv/` when the format changes.
- No mock framework in tests; run `uv run pytest` from the repo root.
