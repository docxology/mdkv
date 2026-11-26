# Search and Export: Exact Matching, Bounded Output

Regex search across selected tracks and languages enables cross‑cutting queries (e.g., beta‑flagged commentary in Spanish). Export is deterministic given a manifest and track set:

- Multi‑track Markdown: concatenates track bodies with track headers for round‑trip attribution and optional filtering by track type.
- HTML (primary): renders the `primary` track to HTML for simple distribution channels, leveraging a standard Markdown engine.
- File export: writes track contents to discrete `.md` files for downstream pipelines.

These capabilities support reproducible publishing.

Programmatic search is available via `mdkv.services.search.search_document(doc, pattern, track_types=None, languages=None)`; the CLI mirrors this with `uv run mdkv search <path> --pattern PATTERN [--types ...] [--languages ...]`.
Combined export headers assist human attribution; they are not reversible identifiers for arbitrary bodies. Native conversion uses restricted Pandoc defaults; PDF requires trusted source and an existing engine.
