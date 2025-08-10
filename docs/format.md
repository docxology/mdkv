# MDKV format

A `.mdkv` file is a ZIP archive with two key elements:

- `manifest.yaml`: document metadata and an index of tracks
- `tracks/`: UTF-8 Markdown files (one file per track)

## Manifest schema

Top-level fields:

- `title`: string (required)
- `authors`: list[string] (required, at least one)
- `created`: ISO-8601 datetime string (required)
- `version`: string (optional, default "0.1")
- `metadata`: object<string,string> (optional)
- `tracks`: list[Track] (optional, but a `primary` track is required for validity)

Track object fields:

- `track_id`: string (required, unique)
- `track_type`: one of `primary`, `translation`, `commentary`, `code`, `reference`, `media_ref`, `revision`
- `language`: string or null (optional). BCP-47/ISO-639 suggested for linguistic tracks
- `path`: string (required). Must start with `tracks/` and typically end with `.md`

### Example manifest

```yaml
# manifest.yaml
title: Example
authors: ["Author"]
created: 2025-01-01T00:00:00
version: "0.1"
metadata: {}
tracks:
  - track_id: primary
    track_type: primary
    language: en
    path: tracks/primary.md
  - track_id: notes
    track_type: commentary
    language: null
    path: tracks/notes.md
```

### Track files

Track contents are stored as Markdown files inside the archive, relative to `path` in the manifest:

- `tracks/primary.md`
- `tracks/notes.md`

Each file contains the UTF-8 Markdown for that track.

## Validation rules

- `title` and `authors` must be present
- At least one track of `track_type: primary` must exist
- Track `path` must begin with `tracks/`
- `track_type` must be one of the supported values

## Round-trip export headers

When exporting to a single Markdown stream, tracks are prefixed with lightweight HTML comments carrying track metadata. These hints enable reconstructing which text came from which track during round-trip workflows:

```markdown
<!-- track:primary type:primary lang:en -->
# Title

<!-- track:notes type:commentary lang:None -->
Editorial notes here
```

These headers are informational; they are not required in individual track files within a `.mdkv` container.
