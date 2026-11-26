# Public API: Stable Imports and Compatibility Boundaries

The top‑level `mdkv` package re‑exports the public API to provide a stable surface:

- `MDKVDocument`, `Track`, `allowed_track_types`, `ValidationError`, `validate_document`, `validate_track`, `ValidationIssue`
- `search_document`, `search_document_async`, `SearchMatch`, `diff_documents`, `DiffResult`, `compute_stats`, `DocumentStats`
- `to_markdown`, `to_html`, `export_to_files`, `to_pdf`, `to_epub`, `to_docx`
- `save_mdkv`, `save_mdkv_incremental`, `load_mdkv`, `MDKVFormatError`, `TrackHistory`, `TrackVersion`
- `TrackTypeRegistry`, `register_track_type`, `get_registry`

This consolidation supports both script‑level usage and library integrations without deep import paths.
