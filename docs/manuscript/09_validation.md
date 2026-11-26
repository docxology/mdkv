# Validation, Integrity and Resource Bounds

Minimal by design to maximize compatibility while catching common integrity issues. Optional profiles can enforce stricter policies (e.g., translation coverage, mandatory references) without compromising baseline portability. See Appendix C for an example of bundle metadata and checksums emitted by the paper builder.

## Common validation errors and remedies

- **Missing `primary` track**: Add at least one `primary` track; ensure `track_type: primary`.
- **Invalid track `path`**: Ensure `path` starts with `tracks/` and corresponds to a file in the container.
- **Unknown `track_type`**: Use only the allowed set; see section 7.
- **Empty `authors`**: Provide at least one author string.
- **Malformed `created`**: Use ISO‑8601 (e.g., `2025-08-10T00:00:00Z`).
- **Duplicate `track_id`**: Ensure each `track_id` is unique; rename or remove conflicts.
- **Bad `track_type` change**: When changing a track’s type, ensure downstream exporters are aware of filtering.
