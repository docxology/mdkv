# MDKV Concept and Format

## Container Layout: Manifest, Tracks and ZIP Envelope

An `.mdkv` file is a ZIP archive that contains:

- `manifest.yaml`: top‑level document metadata and an index of tracks
- `tracks/`: UTF‑8 Markdown files, one per track

Track text is CommonMark-compatible. The reference HTML renderer also enables pipe tables; arbitrary raw HTML is escaped. This is a renderer profile, not a new binary or media format.

## Manifest Schema: Required Fields and Track Index

Top‑level fields (required unless noted):

- `title`: string
- `authors`: list[string] (at least one)
- `created`: ISO‑8601 datetime string
- `version`: string (optional; default "0.1")
- `metadata`: object<string,string> (optional)
- `tracks`: list[Track] (optional at the schema level, but at least one `primary` track is required by validation)

Track object fields:

- `track_id`: string (unique within the document)
- `track_type`: one of `primary`, `translation`, `commentary`, `code`, `reference`, `media_ref`, `revision`
- `language`: string or null (BCP‑47/ISO‑639 recommended for linguistic content)
- `path`: a relative POSIX path below `tracks/`, without empty, dot, parent, backslash or NUL components; paths SHOULD end with `.md`.

Example manifest:

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
  - track_id: notes
    track_type: commentary
    language: null
    path: tracks/notes.md
```

### Specification at a glance

Field overview:

| Field | Type | Required | Notes |
|---|---|---|---|
| `title` | string | yes | Document title |
| `authors` | list[string] | yes | At least one author |
| `created` | ISO‑8601 string | yes | UTC recommended |
| `version` | string | no | Default "0.1" |
| `metadata` | map[string,string] | no | Freeform key/value pairs |
| `tracks` | list[Track] | schema‑optional | Validation requires at least one `primary` |

Track descriptor overview:

| Field | Type | Required | Notes |
|---|---|---|---|
| `track_id` | string | yes | Unique within the document |
| `track_type` | enum | yes | One of `primary, translation, commentary, code, reference, media_ref, revision` |
| `language` | string or null | no | BCP‑47 recommended for linguistic tracks |
| `path` | string | yes | Must start with `tracks/` |

## Multi‑track example (manifest + track bodies)

Below is a compact, realistic multi‑track container using several track types side‑by‑side. This illustrates how translations, commentary, code listings, references, media references, and revisions live next to the canonical `primary` track.

Manifest:

```yaml
title: Product Onboarding Guide
authors: ["Tech Docs Team"]
created: 2025-06-01T12:00:00Z
version: "0.1"
metadata:
  audience: "customer, internal"
tracks:
  - track_id: primary
    track_type: primary
    language: en
    path: tracks/primary.md
  - track_id: ru
    track_type: translation
    language: ru
    path: tracks/ru.md
  - track_id: zh
    track_type: translation
    language: zh
    path: tracks/zh.md
  - track_id: commentary
    track_type: commentary
    language: null
    path: tracks/commentary.md
  - track_id: snippets
    track_type: code
    language: null
    path: tracks/snippets.md
  - track_id: refs
    track_type: reference
    language: null
    path: tracks/refs.md
  - track_id: media
    track_type: media_ref
    language: null
    path: tracks/media.md
  - track_id: release_notes
    track_type: revision
    language: null
    path: tracks/release_notes.md
```

Track bodies (excerpts):

````markdown
<!-- track:primary type:primary lang:en -->
# Welcome
Follow these steps to get started.

<!-- track:ru type:translation lang:ru -->
# Добро пожаловать
Выполните следующие шаги, чтобы начать.

<!-- track:zh type:translation lang:zh -->
# 欢迎
请按照以下步骤开始。

<!-- track:commentary type:commentary lang:None -->
Editors: confirm screenshots match v1.3 UI before release.

<!-- track:snippets type:code lang:None -->
```bash
uv run mdkv init --title "Guide" --author "Docs" --out guide.mdkv
```

<!-- track:refs type:reference lang:None -->
- Quickstart video: media:gui_demo.webm
- Markdown spec: https://commonmark.org

<!-- track:media type:media_ref lang:None -->
assets/gui_demo.webm  # external file shipped alongside exported package

<!-- track:release_notes type:revision lang:None -->
- 2025-06-15: Updated step 2 for new sign‑in flow.
````

Combined exports concatenate track bodies in manifest order with informational attribution headers. Literal header-like content is not escaped into a reversible framing protocol.

## The Paper as a Reproducible MDKV Bundle

Use `paper/build_paper_bundle.sh --no-clone` to package the explicitly attributed authored source. The following manifest illustrates the same model:

1) Create `manifest.yaml` with at least one primary track and metadata:

```yaml
title: "MDKV: A Multitrack Markdown Container for Structured, Portable Documents"
authors: ["Daniel Ari Friedman"]
created: 2025-08-10T00:00:00Z
version: "0.1"
metadata:
  doi: "10.5281/zenodo.16790555"
  orcid: "0000-0001-6232-9096"
  contact: "daniel@activeinference.institute"
tracks:
  - track_id: primary
    track_type: primary
    language: en
    path: tracks/primary.md
```

Place the authored body in `tracks/primary.md`; a ZIP may use implicit `tracks/`
prefixes rather than an explicit directory entry. The owning bundle builder
validates metadata and content, emits current exports and records their provenance.

CLI (linked): see [CLI guide](https://github.com/docxology/mdkv/blob/main/docs/cli.md). Minimal sequence:

```bash
uv run mdkv init --title "MDKV Paper" --author "Daniel Ari Friedman" --out paper.mdkv
uv run mdkv update-track paper.mdkv --id primary --file docs/manuscript/02_introduction.md
uv run mdkv set-meta paper.mdkv doi 10.5281/zenodo.16790555
uv run mdkv validate paper.mdkv
uv run mdkv info paper.mdkv
```

## Validation Rules: Structural and Editorial

MDKV’s base validator enforces:

- Presence of `title`, `authors`, and at least one `primary` track
- Track `path` begins with `tracks/`
- `track_type` is one of the supported values
- `track_id` is non‑empty and unique
- `language` is a string or null; BCP-47 is recommended, not syntactically enforced

The intentionally small rule set preserves extensibility while ensuring minimal integrity guarantees for downstream services.

Implementation note: the reference validator checks for the presence of a track whose `track_type` is `primary` (`mdkv/core/validate.py`), matching the rule above rather than requiring the specific id `primary`.

## Informational Export Headers: Attribution Without a Parser

Combined Markdown includes a comment encoding track metadata. These are attribution hints, not a lossless reconstruction grammar; ZIP/JSON are the structured interchange paths. Native PDF/EPUB/DOCX conversion composes the selected body plus allowlisted frontmatter directly, so these comments do not become visible publication text:

```markdown
<!-- track:primary type:primary lang:en -->
Title

<!-- track:notes type:commentary lang:None -->
Editorial notes here
```

## Normative Container Requirements (Conformance)

The MDKV container is defined by the following MUST/SHOULD requirements:

- A conforming `.mdkv` MUST be a ZIP archive with one unambiguous root `manifest.yaml` and indexed UTF-8 track members under `tracks/` (directory entries may be implicit).
- Editorial conformance requires a nonempty title, nonempty author list and at least one primary-type track. Structural loading is deliberately separate and can load incomplete documents for editing.
- Each descriptor MUST contain a unique nonempty `track_id`, registered `track_type` and safe relative `path`. `language` is optional and defaults to null. The metadata map contains string values, with documented safe scalar normalization.
- At least one track with `track_type: primary` MUST be present.
- Combined Markdown exports use informational comment headers. They do not define a conforming lossless import protocol.
- Implementations SHOULD preserve field ordering in `manifest.yaml` for human readability, though ordering is not semantically significant.
- Implementations SHOULD emit UTF‑8 for all track files and SHOULD NOT assume line ending conventions beyond standard text processing.

## Conformance Levels

- Core Conformance: satisfies all MUST requirements above and passes validation.
- Extended presentation: selective export by track type and GUI preview by track ID. Language filtering is implemented for search, not as a direct export parameter.

## Design Principles: Durable Primitives and Explicit Layers

- Simplicity first: rely on ubiquitous primitives (ZIP, YAML, Markdown) to maximize longevity and inspectability.
- Separation of concerns: keep tracks orthogonal; orchestrate at export time rather than embedding format‑specific directives into bodies.
- Round-trip fidelity: ZIP and JSON serialization preserve modeled document fields and exact track text. Combined Markdown headers are informational, not an unambiguous lossless interchange grammar.
- Deterministic composition: identical manifests and track sets produce identical exports to support reproducible publishing.
- Extensibility: add tracks and exporters without changing the core model or on‑disk layout.

## Limitations of the format

- **No encryption or signing baked in**: use external tools for security (see Security and provenance guidance).
- **Not an execution environment**: `code` tracks are listings, not runnable notebooks; execution belongs to downstream systems.
- **No enforced cross‑track alignment**: paragraph‑level alignment between tracks is a convention, not a rule.
- **Binary assets live outside**: large media is referenced via `media_ref` instead of embedded to keep bundles lean and editable.
- **No cross‑doc linking semantics**: references across containers are conventional; not part of the base spec.
- **Time semantics are shallow**: `created` is recorded; versioning/history are external concerns.
