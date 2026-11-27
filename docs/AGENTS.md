# mdkv — Agent Notes

- Layout: package code in `mdkv/`, tests in `tests/`, examples in `examples/`,
  demo in `demo/`, reusable content in `library/`. Docs live here (`docs/`).
- Authored publication sections and figures live in `manuscript/`; native
  bundle scripts and archived outputs remain in `../paper/`.
- Docs maintenance: `docs/index.rst` drives the Sphinx toctree; add new `.md`
  pages there. Keep `format.md` in sync with the parser implementation in
  `mdkv/` when the format changes.
- No mock framework in tests. Run the [locked verification steps](verification.md)
  from the repo root.
