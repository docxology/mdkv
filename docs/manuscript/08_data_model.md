# Data Model: Semantics of Tracks

MDKV’s track taxonomy encodes common document layers:

- `primary`: canonical content intended for publication and primary consumption.
- `translation`: language alternatives to `primary`, preserving structure but adapting language and, where necessary, locale.
- `commentary`: editorial guidance; excluded by default from HTML, but included by default in unfiltered combined Markdown. Public Markdown should explicitly select `--types primary`.
- `code`: code listings and examples that remain synchronized with the narrative; not intended as executed notebooks.
- `reference`: citations and reference lists, metadata‑heavy but typically orthogonal to `primary` structure.
- `media_ref`: references to external media (figures, videos) that are managed outside the container but linked textually.
- `revision`: review notes and change summaries; useful for governance, release notes, and compliance trails.

Semantically, MDKV treats tracks as parallel layers; it does not prescribe alignment at paragraph or section granularity. Alignment strategies (e.g., anchor conventions) can be layered atop the format by convention when needed.
