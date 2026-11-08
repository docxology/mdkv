# Architecture: Layers, Boundaries and Guarantees

MDKV separates an in-memory model from ZIP persistence and presentation services.

- `core.model`: mutable `Track` and `MDKVDocument`, identity/path invariants,
  ordered track mutations and JSON projection. Self-move is a no-op; rename
  validates the proposed identity/path before preserving the original position.
- `core.registry`: one process-local authority for built-in and explicitly
  registered custom types. Construction, validation, GUI and storage use it.
  Loading a type name never imports executable plugins.
- `core.validate`: structural revalidation plus editorial requirements (title,
  authors, primary track), content warnings and registered callbacks. A loadable
  incomplete document is not necessarily editorially valid.
- `core.history`: standalone chronological `TrackHistory`/`TrackVersion` utilities,
  not automatic persisted undo. A history uses consistent naive or aware dates;
  mixed conventions are refused before mutation.
- `storage.schema`: Pydantic manifest schema with safe legacy scalar adapters.
- `storage.io`: bounded unambiguous YAML/ZIP reads and one validated atomic writer.
  `save_mdkv_incremental` performs a full rewrite; its boolean reports whether the
  previous destination was valid, not how many bytes were reused.
- `services.search`: exact stdlib `re` in a short-lived supervised interpreter,
  with separate startup/matching deadlines, bounded result pages and child reaping.
  Async callers do not run matching on the event-loop thread.
- `services.export`: deterministic text composition for fixed fields/order/runtime,
  inert HTML with table support, and collision-checked per-file exports.
- `services.diff`: modeled field comparison, including creation time and track
  order (`created_changed`, `track_order_changed` in JSON); archive bytes and
  unknown fields are not compared.
- `services.stats`: textual counts, track types and languages; not scientific
  performance measurements.
- `services.pandoc_export`: optional installed Pandoc PDF/EPUB/DOCX conversion of
  Markdown body plus allowlisted frontmatter, with restricted defaults, subprocess
  deadlines and atomic output publication. Informational MDKV track comments are
  not composed into native output. Relative figure links need an explicit Pandoc
  `--resource-path` from the caller.
- `cli`: Click orchestration. Expected input/I/O failures produce clean nonzero
  exits. Batch commands finish reporting all peers, then exit nonzero on failure.
- `gui`: loopback FastAPI application and static single-track editor/preview.
  One process-global document is shared across clients. Browser operations are
  serialized, with exact canonical track IDs rather than parsed display comments.
- `library`: authored YAML definition loading and generation. Setuptools maps
  `mdkv.resources` to canonical `library/`, so installed examples need no checkout
  or site-packages writes. `_built/` is regenerated through `build_all_examples`.
- `common`, `i18n`: logging and packaged gettext catalogs.

The package root re-exports the public API documented in [API](api.rst).
[Format](format.md) defines storage versus editorial validity; [security](security.md)
defines limits and trust boundaries. The methods manuscript and its owning bundle
builder live in `paper/`, independently of Sphinx. Artifact checksums attest exact
outputs; ZIP/generation timestamps are not byte-reproducible build guarantees.
