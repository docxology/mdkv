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

- Validation: ensure required fields and a `primary` track exist
- Search: regex-based search across selected track types/languages
- Export: render to Markdown (all or filtered tracks) or HTML (primary)

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
uv run mdkv export-tracks doc.mdkv --types primary,commentary > out.md
uv run mdkv export --html doc.mdkv > out.html
```

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
- Tooling: CLI and Python API (`mdkv.core`, `mdkv.storage`, `mdkv.services`)


