# MDKV concept

MDKV is a multitrack Markdown container. A single `.mdkv` file (a ZIP) holds a manifest plus one or more Markdown tracks:

```text
doc.mdkv
├─ manifest.yaml
└─ tracks/
   ├─ primary.md
   ├─ commentary.md
   ├─ translation-es.md
   └─ code.md
```

## File structure

- `manifest.yaml`: document metadata and track index
- `tracks/`: UTF-8 Markdown files, one per track

Minimal manifest:

```yaml
title: Example
authors: ["Author"]
created: 2025-01-01T00:00:00Z
version: "0.1"
metadata: {}
tracks:
  - track_id: primary
    track_type: primary
    language: en
    path: tracks/primary.md
```

Supported track types:

- primary: canonical content
- translation: language-alternate content
- commentary: notes/annotations
- code: embedded code examples
- reference: citations/refs
- media_ref: references to external media
- revision: revision notes

## Core functions

- Validation: ensure required fields, primary track, path uniqueness, and content heuristics
- Search: regex-based search across selected track types/languages with case-insensitive support
- Export: render to Markdown (all or filtered tracks, optional YAML frontmatter) or HTML (with type filtering)
- Import: bring existing Markdown files into a new .mdkv container
- Diff: compare two .mdkv documents (tracks, metadata, content changes)
- Stats: document statistics (track counts, characters, lines, languages)

Examples:

```bash
# init, inspect, validate
uv run mdkv init --title T --author A --out doc.mdkv
uv run mdkv info doc.mdkv
uv run mdkv validate doc.mdkv

# add and list
uv run mdkv add-track doc.mdkv --id notes --type commentary --lang "" --content "Note"
uv run mdkv list-tracks doc.mdkv

# search and export
uv run mdkv search doc.mdkv --pattern beta --types primary,commentary
uv run mdkv search doc.mdkv --pattern hello -i  # case-insensitive
uv run mdkv export-tracks doc.mdkv --types primary,commentary > out.md
uv run mdkv export --html doc.mdkv > out.html
uv run mdkv export --html --types primary,commentary doc.mdkv > combined.html

# import, diff, stats
uv run mdkv import README.md --out imported.mdkv --title "Imported" --author "You"
uv run mdkv diff doc_v1.mdkv doc_v2.mdkv
uv run mdkv stats doc.mdkv
```

## Security

MDKV is designed with defense-in-depth:

- **Path traversal prevention**: `export_to_files` sanitizes track IDs before using them as filenames, preventing directory escape via malicious track IDs like `../../etc/passwd`.
- **HTML comment injection**: track metadata in export headers is sanitized to prevent `-->` injection that could break out of HTML comments.
- **YAML-safe metadata**: the `metadata_header` export option uses `yaml.safe_dump` for frontmatter, preventing YAML injection via special characters in titles or metadata values.
- **Container integrity**: `save_mdkv` detects and rejects duplicate track paths before writing, preventing silent data loss in the ZIP. `load_mdkv` wraps `ValueError` from `Track` construction in `MDKVFormatError` so corrupt manifests produce clean errors.
- **Input validation**: the GUI API validates `track_type` on both creation and mutation of tracks. Invalid regex patterns in search return clean 400 errors instead of crashing.
- **CLI error handling**: all CLI commands catch `FileNotFoundError` and `MDKVFormatError` and report clean error messages with exit code 1, instead of Python tracebacks.

## Implications

- Portability: plain-text Markdown in a single ZIP; easy to email, archive, diff
- Multilingual: first-class `translation` tracks without forking the document
- Layering: `commentary`/`reference` add context without touching primary
- Composability: selective export builds views for audiences and channels
- Governance: explicit `revision`/metadata support validation and audits
- Examples: see `library/definitions/` for small, bilingual, large multilingual, code, and revisions samples

## Why this matters

Traditional single-file Markdown breaks down when the same document needs alternate languages, audience notes, or channel-specific extracts. MDKV keeps everything together but decoupled:

- Authoring: teams can work in parallel on `primary`, `translation`, and `commentary` tracks.
- Publishing: choose which tracks to include at render time without editing content.
- Review: `revision` tracks and manifest metadata encode change intent explicitly.

This design balances portability (plain Markdown) with structure (manifest + tracks), enabling predictable automation and human-friendly workflows.

## Interop

- Container: standard ZIP; no custom filesystem requirements
- Content: CommonMark-compatible Markdown; rendered via `markdown-it`
- Tooling: CLI (`python -m mdkv` or `mdkv` entry point) and Python API (`mdkv.core`, `mdkv.storage`, `mdkv.services`)
- Type safety: `py.typed` marker for PEP 561 compatibility
