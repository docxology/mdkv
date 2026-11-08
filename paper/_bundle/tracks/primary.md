
# MDKV: A Multitrack Markdown Container for Structured, Portable Documents

**Daniel Ari Friedman**  
[ORCID: 0000-0001-6232-9096](https://orcid.org/0000-0001-6232-9096)  
<daniel@activeinference.institute>  
August 10, 2025  
[DOI: 10.5281/zenodo.16790555](https://doi.org/10.5281/zenodo.16790555)

## Abstract

Digital knowledge work increasingly demands documents that are simultaneously multilingual, multi‑audience, and multi‑channel. Traditional single‑file Markdown struggles when the same canonical content must coexist with translations, commentary, references, code exemplars, and revision notes – each with distinct lifecycles and audiences. This paper introduces MDKV, a simple but rigorous multitrack Markdown container that packages a document’s canonical content and auxiliary tracks into a single, portable `.mdkv` file. An `.mdkv` is a ZIP archive with a YAML `manifest.yaml` and a `tracks/` directory of UTF‑8 Markdown files. MDKV provides a principled data model, validation, search, and export services, a CLI, and a small GUI for selective preview and live editing. We formalize the MDKV model, present its software architecture, explain round‑trip export semantics, and evaluate design trade‑offs against adjacent technologies. The MDKV initial specification is open source under the [Apache‑2.0](https://www.apache.org/licenses/LICENSE-2.0) license and maintained at the project repository (`https://github.com/docxology/mdkv`). We also situate MDKV with respect to Matroska (MKV) as background on containerization: although the two are orthogonal in domain (text vs. multimedia), they share conceptual lineage in extensible container design. We conclude with use cases, implications for governance and reproducibility, and future work such as richer validation rules and alternative exporters. This paper is itself a Markdown file that renders into a valid MDKV. The built artifact is available at [paper/paper.mdkv](https://github.com/docxology/mdkv/blob/main/paper/paper.mdkv); combined exports are under [paper/_bundle](https://github.com/docxology/mdkv/tree/main/paper/_bundle).

## Graphical Abstract: One Canonical Source, Accountable Views

![One Markdown source is packaged into a ZIP/YAML MDKV container with parallel primary, translation, commentary, code, reference, media_ref and revision tracks; deterministic exports compose reader, reviewer and archive views, while bounds cover the reader, search, writes, GUI and optional converters.](figures/mdkv-graphical-abstract.png)

*Figure 1. The MDKV workflow: author once, package the layers explicitly, and compose a view for each accountable audience. The graphic is descriptive, not a measured performance result.*

## 1. Introduction

Authoring, collaboration, and publishing workflows routinely require: (i) a single canonical text; (ii) multiple translations; (iii) audience‑specific commentary and references; (iv) code listings synchronized with the text; and (v) review and revision notes. Maintaining such layers in separate files and folders creates cognitive load and increases the risk of divergence. The central question is how to preserve a document’s conceptual unity while keeping its layers decoupled for editing, governance, and rendering.

MDKV addresses this need with a multitrack container for Markdown. Rather than overloading a single source with embedded annotations and language variants, MDKV separates concerns into tracks—`primary` (canonical), `translation`, `commentary`, `code`, `reference`, `media_ref`, and `revision`—and composes views at export time. The container format is intentionally modest: plain Markdown and YAML wrapped in ZIP, optimized for transparency, diff‑friendliness, and longevity.

Design motivations and lineage. MDKV applies general container principles (clear manifest, independent tracks, robust round‑trip) from adjacent domains to plaintext authoring. It favors human‑inspectable, durable primitives over custom binary formats, enabling simple tooling and long‑term readability. The initial public release standardizes a minimal spec and a reference implementation with CLI and GUI.

Contributions. (i) A precise model and container format with minimal but sufficient validation; (ii) a modular architecture separating model, storage, and services, surfaced via CLI and GUI; (iii) detailed use cases spanning multilingual publishing, layered collaboration, reproducible distribution, and governance; and (iv) guidance for cryptographic provenance and conformance.

## 2. Background: Why Containerize Documents?

### 2.1 Matroska (MKV): History and Technical Context

The [Matroska specification, RFC 9559](https://www.rfc-editor.org/rfc/rfc9559),
published in October 2024 by Steve Lhomme, Moritz Bunkus and Dave Rice, defines
an audiovisual container based on EBML. Its independently described tracks
provide a design analogy here, not evidence that a ZIP/YAML text format inherits
Matroska's streaming, recovery or interoperability properties.

MDKV does not implement Matroska or EBML. Historical adoption timelines are not
needed to establish the text-container design and are not evaluated in this work.

### 2.2 MDKV and MKV: Orthogonal Domains, Shared Intuition

MDKV is not an MKV editor, wrapper, or derivative; it targets plaintext documents rather than multimedia. The similarity in names is intentional only insofar as both are “container‑centric” designs. MDKV borrows the intuition that many artifacts are multi‑track by nature, but it embraces a radically simpler substrate—[Markdown (CommonMark)](https://commonmark.org), [YAML](https://yaml.org/spec/), and [ZIP](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT)—to maximize openness, inspectability, and compatibility with standard tooling. Where MKV multiplexes time‑based streams, MDKV co‑packages logically distinct textual layers.

### 2.3 Why a textual container (vs. multimedia/EPUB/PDF)

- **Keep primitives simple**: plain Markdown + YAML + ZIP are ubiquitous, inspectable, and durable; no custom binary framing.
- **Multi‑track authorship, not playback**: MDKV is for co‑authoring and distributing textual layers in parallel; it is not a media streaming format.
- **Deterministic composition**: exports are reproducible from a manifest and track set, supporting provenance and verification.
- **Toolchain leverage**: downstream pipelines (e.g., [pandoc](https://pandoc.org)) can consume `to_markdown()` outputs directly.
- **Manage external assets**: media stays outside via `media_ref` tracks, keeping bundles lean while links remain explicit and reviewable.
- **Human‑first diffs**: separate files per track minimize merge conflicts and make reviews targeted.
- **Sovereign metadata**: `manifest.yaml` is explicit and auditable; no hidden state.

## 3. MDKV Concept and Format

### 3.1 Container Layout: Manifest, Tracks and ZIP Envelope

An `.mdkv` file is a ZIP archive that contains:

- `manifest.yaml`: top‑level document metadata and an index of tracks
- `tracks/`: UTF‑8 Markdown files, one per track

Track text is CommonMark-compatible. The reference HTML renderer also enables pipe tables; arbitrary raw HTML is escaped. This is a renderer profile, not a new binary or media format.

### 3.2 Manifest Schema: Required Fields and Track Index

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

#### 3.2.1 Specification at a glance

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

### 3.3 Multi‑track example (manifest + track bodies)

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

### 3.4 The Paper as a Reproducible MDKV Bundle

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

CLI (linked): see [`docs/cli.md`](https://github.com/docxology/mdkv/blob/main/docs/cli.md). Minimal sequence:

```bash
uv run mdkv init --title "MDKV Paper" --author "Daniel Ari Friedman" --out paper.mdkv
uv run mdkv update-track paper.mdkv --id primary --file paper/mdkv_paper.md
uv run mdkv set-meta paper.mdkv doi 10.5281/zenodo.16790555
uv run mdkv validate paper.mdkv
uv run mdkv info paper.mdkv
```

### 3.5 Validation Rules: Structural and Editorial

MDKV’s base validator enforces:

- Presence of `title`, `authors`, and at least one `primary` track
- Track `path` begins with `tracks/`
- `track_type` is one of the supported values
- `track_id` is non‑empty and unique
- `language` is a string or null; BCP-47 is recommended, not syntactically enforced

The intentionally small rule set preserves extensibility while ensuring minimal integrity guarantees for downstream services.

Implementation note: the reference validator checks for the presence of a track whose `track_type` is `primary` (`mdkv/core/validate.py`), matching the rule above rather than requiring the specific id `primary`.

### 3.6 Informational Export Headers: Attribution Without a Parser

Combined Markdown includes a comment encoding track metadata. These are attribution hints, not a lossless reconstruction grammar; ZIP/JSON are the structured interchange paths. Native PDF/EPUB/DOCX conversion composes the selected body plus allowlisted frontmatter directly, so these comments do not become visible publication text:

```markdown
<!-- track:primary type:primary lang:en -->
Title

<!-- track:notes type:commentary lang:None -->
Editorial notes here
```

### 3.7 Normative Container Requirements (Conformance)

The MDKV container is defined by the following MUST/SHOULD requirements:

- A conforming `.mdkv` MUST be a ZIP archive with one unambiguous root `manifest.yaml` and indexed UTF-8 track members under `tracks/` (directory entries may be implicit).
- Editorial conformance requires a nonempty title, nonempty author list and at least one primary-type track. Structural loading is deliberately separate and can load incomplete documents for editing.
- Each descriptor MUST contain a unique nonempty `track_id`, registered `track_type` and safe relative `path`. `language` is optional and defaults to null. The metadata map contains string values, with documented safe scalar normalization.
- At least one track with `track_type: primary` MUST be present.
- Combined Markdown exports use informational comment headers. They do not define a conforming lossless import protocol.
- Implementations SHOULD preserve field ordering in `manifest.yaml` for human readability, though ordering is not semantically significant.
- Implementations SHOULD emit UTF‑8 for all track files and SHOULD NOT assume line ending conventions beyond standard text processing.

### 3.8 Conformance Levels

- Core Conformance: satisfies all MUST requirements above and passes validation.
- Extended presentation: selective export by track type and GUI preview by track ID. Language filtering is implemented for search, not as a direct export parameter.

### 3.9 Design Principles: Durable Primitives and Explicit Layers

- Simplicity first: rely on ubiquitous primitives (ZIP, YAML, Markdown) to maximize longevity and inspectability.
- Separation of concerns: keep tracks orthogonal; orchestrate at export time rather than embedding format‑specific directives into bodies.
- Round-trip fidelity: ZIP and JSON serialization preserve modeled document fields and exact track text. Combined Markdown headers are informational, not an unambiguous lossless interchange grammar.
- Deterministic composition: identical manifests and track sets produce identical exports to support reproducible publishing.
- Extensibility: add tracks and exporters without changing the core model or on‑disk layout.

### 3.10 Limitations of the format

- **No encryption or signing baked in**: use external tools for security (see Security and provenance guidance).
- **Not an execution environment**: `code` tracks are listings, not runnable notebooks; execution belongs to downstream systems.
- **No enforced cross‑track alignment**: paragraph‑level alignment between tracks is a convention, not a rule.
- **Binary assets live outside**: large media is referenced via `media_ref` instead of embedded to keep bundles lean and editable.
- **No cross‑doc linking semantics**: references across containers are conventional; not part of the base spec.
- **Time semantics are shallow**: `created` is recorded; versioning/history are external concerns.

## 4. Software Architecture: Thin Orchestration over a Typed Core

MDKV follows a thin‑orchestrator, modular architecture:

- `mdkv.core`: data model and validation
- `mdkv.storage`: persistence (read/write `.mdkv`)
- `mdkv.services`: search and export utilities
- `mdkv.cli`: CLI entry points and subcommands

This separation enables stable public APIs, testable modules, and straightforward extension.

### 4.1 Core Model (`mdkv.core`)

The core defines two primary classes:

- `Track`: a single Markdown track with `track_id`, `track_type`, `language`, `path`, `content`, and invariant checks (valid type, non‑empty id, `path` under `tracks/`).
- `MDKVDocument`: an in‑memory aggregate with metadata (`title`, `authors`, `created`, `version`, and `metadata` map) and a mapping `track_id → Track`. It provides helpers for adding/removing tracks, renaming, content updates, language listing, and metadata set/get/remove.
- Track constructors and mutation helpers enforce structural checks; mutable dataclasses are revalidated at save/explicit validation boundaries. Storage safety and editorial validity are separate contracts.

The core also surfaces `allowed_track_types()` and validation types (`ValidationError`, `ValidationIssue`).

### 4.2 Storage (`mdkv.storage`)

ZIP + YAML persistence:

- `save_mdkv(doc, output_path)`: write tracks under `tracks/` and emit `manifest.yaml` from the document.
- `load_mdkv(input_path)`: parse the manifest and reconstruct the document, loading each track’s content.

The manifest lists metadata and track descriptors; bodies remain discrete files for transparency and editability.

### 4.3 Services (`mdkv.services`)

Services operate over `MDKVDocument` instances without owning container I/O:

- Search: stdlib `re` matching with optional `track_type`/`language` filters, supervised deadline enforcement and bounded pages; sync and async APIs share results.
- Export: composition of multi‑track Markdown via `to_markdown()`, primary‑track HTML via `to_html()` using [markdown‑it‑py](https://github.com/executablebooks/markdown-it-py), and per‑track files via `export_to_files()`.
- Native conversion: optional Pandoc PDF/EPUB/DOCX export of the body plus allowlisted frontmatter; informational MDKV comments are not emitted into native output.
- Comparison and statistics: structured `diff_documents()` results and textual `compute_stats()` counts; neither is an empirical benchmark.
- Export determinism: order is manifest‑driven; fixed inputs and renderer versions give identical text, while ZIP bytes and generation timestamps may differ.

### 4.4 CLI (`mdkv.cli`)

Thin orchestrators for: init, info, validate, track ops, search, export, metadata, and GUI. Commands call module APIs directly for testability and minimal command‑layer logic.

### 4.5 GUI (`mdkv.gui`)

The local GUI has a canonical single-track editor and independent preview checkboxes. `POST /api/render/tracks_html` renders subsets; `GET /api/track?track_id=...` reads a literal track identifier and `PUT /api/track` updates an existing track without parsing display comments. `GET /api/render/markdown` remains a combined presentation export. Browser operations serialize pending edits before switches/saves. State is shared across clients; persistence uses the same atomic `save_mdkv` writer as the CLI.

### 4.6 Architecture Map and Source Pointers

- Layers and responsibilities: see [`docs/architecture.md`](https://github.com/docxology/mdkv/blob/main/docs/architecture.md) (built locally with Sphinx; there is no hosted docs site).
- Core model: [`mdkv/core/model.py`](https://github.com/docxology/mdkv/blob/main/mdkv/core/model.py) defines `Track`, `MDKVDocument`, and invariants; re‑exported via [`mdkv/__init__.py`](https://github.com/docxology/mdkv/blob/main/mdkv/__init__.py).
- Storage: [`mdkv/storage/io.py`](https://github.com/docxology/mdkv/blob/main/mdkv/storage/io.py) implements `save_mdkv` and `load_mdkv` (ZIP + YAML manifest and `tracks/`).
- Services: export in [`mdkv/services/export.py`](https://github.com/docxology/mdkv/blob/main/mdkv/services/export.py) (`to_markdown`, `to_html`, `export_to_files`); search in [`mdkv/services/search.py`](https://github.com/docxology/mdkv/blob/main/mdkv/services/search.py). Both are re‑exported at the top‑level package for a stable public API.
- CLI: [`mdkv/cli/main.py`](https://github.com/docxology/mdkv/blob/main/mdkv/cli/main.py) surfaces subcommands (init, info, validate, track ops, search, export, gui).
- GUI backend: [`mdkv/gui/server.py`](https://github.com/docxology/mdkv/blob/main/mdkv/gui/server.py) provides `POST /api/render/tracks_html` for subset rendering; static assets under [`mdkv/gui/static/`](https://github.com/docxology/mdkv/tree/main/mdkv/gui/static).

Data flow summary (see also the repository `README.md` and docs pages):

- Authoring: create or load an `MDKVDocument`, add tracks; validate.
- Persistence: `save_mdkv` writes `tracks/` and `manifest.yaml` into a `.mdkv` ZIP; `load_mdkv` reconstructs.
- Services: `search_document` filters/matches; `to_markdown` and `to_html` export views; `export_to_files` writes per‑track files. For end‑to‑end CLI usage, see [`docs/cli.md`](https://github.com/docxology/mdkv/blob/main/docs/cli.md).

## 5. Public API: Stable Imports and Compatibility Boundaries

The top‑level `mdkv` package re‑exports the public API to provide a stable surface:

- `MDKVDocument`, `Track`, `allowed_track_types`, `ValidationError`, `validate_document`, `validate_track`, `ValidationIssue`
- `search_document`, `search_document_async`, `SearchMatch`, `diff_documents`, `DiffResult`, `compute_stats`, `DocumentStats`
- `to_markdown`, `to_html`, `export_to_files`, `to_pdf`, `to_epub`, `to_docx`
- `save_mdkv`, `save_mdkv_incremental`, `load_mdkv`, `MDKVFormatError`, `TrackHistory`, `TrackVersion`
- `TrackTypeRegistry`, `register_track_type`, `get_registry`

This consolidation supports both script‑level usage and library integrations without deep import paths.

## 6. Usage: CLI, Python API and GUI Workflows

### 6.1 Quickstart

```bash
# use an existing uv installation; no installer is run by the builder
# from repo root
uv sync --locked --extra dev
uv run pytest -q
uv run mdkv --help
```

### 6.2 Create, Inspect, Validate

```bash
uv run mdkv init --title "Doc" --author "You" --out doc.mdkv
uv run mdkv info doc.mdkv
uv run mdkv validate doc.mdkv
```

### 6.3 Track Operations

```bash
uv run mdkv list-tracks doc.mdkv
uv run mdkv add-track doc.mdkv --id notes --type commentary --lang "" --content "Note"
uv run mdkv rename-track doc.mdkv --old-id notes --new-id commentary
uv run mdkv update-track doc.mdkv --id commentary --content "Updated note"
```

### 6.4 Export and GUI

```bash
# export selected track types to Markdown
uv run mdkv export-tracks doc.mdkv --types primary,commentary > exported.md

# export HTML of primary track
uv run mdkv export --html doc.mdkv > primary.html

# launch GUI
uv run mdkv gui --path doc.mdkv
```

### 6.5 Programmatic Export

```python
from pathlib import Path
from datetime import datetime, timezone
from mdkv import MDKVDocument, Track, export_to_files, to_markdown, save_mdkv, validate_document

# write selected tracks as individual .md files
doc = MDKVDocument(title="Doc", authors=["You"], created=datetime.now(timezone.utc), version="0.1")
doc.add_track(Track(track_id="primary", track_type="primary", language="en", path="tracks/primary.md", content="# Hello\n"))

# validate, save, export
validate_document(doc)
save_mdkv(doc, Path("doc.mdkv"))
export_to_files(doc, Path("out_tracks"), include_track_types=["primary", "commentary"])

# combined markdown (for pandoc or review)
combined_md = to_markdown(doc)
Path("combined.md").write_text(combined_md, encoding="utf-8")
```

### 6.6 End‑to‑end: create a multi‑track paper

```bash
# 1) Initialize
uv run mdkv init --title "Paper" --author "Author" --out paper.mdkv

# 2) Add tracks
uv run mdkv add-track paper.mdkv --id ru --type translation --lang ru --content "# Резюме\n..."
uv run mdkv add-track paper.mdkv --id zh --type translation --lang zh --content "# 摘要\n..."
uv run mdkv add-track paper.mdkv --id commentary --type commentary --content "Editors: tighten abstract."
uv run mdkv add-track paper.mdkv --id code --type code --content '```bash
uv run pytest -q
```'
uv run mdkv add-track paper.mdkv --id refs --type reference --content "- CommonMark: https://commonmark.org"
uv run mdkv add-track paper.mdkv --id media --type media_ref --content "docs/_static/gui_demo.webm"
uv run mdkv add-track paper.mdkv --id revisions --type revision --content "- 2025-08-10: camera‑ready edits"

# 3) Inspect and validate
uv run mdkv list-tracks paper.mdkv | jq .
uv run mdkv validate paper.mdkv

# 4) Search (only Russian translations for TODO/FIXME)
uv run mdkv search paper.mdkv --pattern "TODO|FIXME" --types translation --languages ru | jq .

# 5) Export views
uv run mdkv export-tracks paper.mdkv --types primary,translation > combined.md
uv run mdkv export --html paper.mdkv > primary.html
```

## 7. Data Model: Semantics of Tracks

MDKV’s track taxonomy encodes common document layers:

- `primary`: canonical content intended for publication and primary consumption.
- `translation`: language alternatives to `primary`, preserving structure but adapting language and, where necessary, locale.
- `commentary`: editorial guidance; excluded by default from HTML, but included by default in unfiltered combined Markdown. Public Markdown should explicitly select `--types primary`.
- `code`: code listings and examples that remain synchronized with the narrative; not intended as executed notebooks.
- `reference`: citations and reference lists, metadata‑heavy but typically orthogonal to `primary` structure.
- `media_ref`: references to external media (figures, videos) that are managed outside the container but linked textually.
- `revision`: review notes and change summaries; useful for governance, release notes, and compliance trails.

Semantically, MDKV treats tracks as parallel layers; it does not prescribe alignment at paragraph or section granularity. Alignment strategies (e.g., anchor conventions) can be layered atop the format by convention when needed.

## 8. Validation, Integrity and Resource Bounds

Minimal by design to maximize compatibility while catching common integrity issues. Optional profiles can enforce stricter policies (e.g., translation coverage, mandatory references) without compromising baseline portability. See Appendix C for an example of bundle metadata and checksums emitted by the paper builder.

### 8.1 Common validation errors and remedies

- **Missing `primary` track**: Add at least one `primary` track; ensure `track_type: primary`.
- **Invalid track `path`**: Ensure `path` starts with `tracks/` and corresponds to a file in the container.
- **Unknown `track_type`**: Use only the allowed set; see section 7.
- **Empty `authors`**: Provide at least one author string.
- **Malformed `created`**: Use ISO‑8601 (e.g., `2025-08-10T00:00:00Z`).
- **Duplicate `track_id`**: Ensure each `track_id` is unique; rename or remove conflicts.
- **Bad `track_type` change**: When changing a track’s type, ensure downstream exporters are aware of filtering.

## 9. Search and Export: Exact Matching, Bounded Output

Regex search across selected tracks and languages enables cross‑cutting queries (e.g., beta‑flagged commentary in Spanish). Export is deterministic given a manifest and track set:

- Multi‑track Markdown: concatenates track bodies with track headers for round‑trip attribution and optional filtering by track type.
- HTML (primary): renders the `primary` track to HTML for simple distribution channels, leveraging a standard Markdown engine.
- File export: writes track contents to discrete `.md` files for downstream pipelines.

These capabilities support reproducible publishing.

Programmatic search is available via `mdkv.services.search.search_document(doc, pattern, track_types=None, languages=None)`; the CLI mirrors this with `uv run mdkv search <path> --pattern PATTERN [--types ...] [--languages ...]`.
Combined export headers assist human attribution; they are not reversible identifiers for arbitrary bodies. Native conversion uses restricted Pandoc defaults; PDF requires trusted source and an existing engine.

## 10. Implementation Notes: Runtime, Packaging and Testing

- Python 3.11+; dataclasses and type hints; explicit naming.
- Packaging: public API re‑exports; CLI entry point `mdkv`.
- Dependencies: YAML, ZIP (std lib), Markdown renderer for HTML export.
- Tests: cover CLI, services, model invariants, and storage round‑trip.

## 11. Use Cases: From Localization to Audit Trails

### 11.1 Multilingual publishing and localization

- Goal: ship a single canonical text to multiple locales without forking.
- Tracks: `primary` (en), `translation` (ru, zh, …).
- Flow: author primary/translation tracks and search by language. To export a locale, select the corresponding tracks in a document view before type-filtered export; there is no direct language-export parameter.
- Intended benefit: organizing locale variants without requiring separate repositories. This has not been empirically compared with branching workflows.
- Notes: reserve `track_id` values for ISO language tags where possible (e.g., `ru`, `zh-Hans`).

### 11.2 Layered collaboration, review, and stakeholder tailoring

- Goal: separate canonical narrative from internal commentary and change rationale.
- Tracks: `commentary`, `revision` alongside `primary`.
- Flow: reviewers annotate in `commentary`; change summaries accrue in `revision`; public exports omit commentary; internal exports include it for audit and coaching.
- Benefit: clean public artifacts with rich internal discourse and governance trails.
- Notes: treat `revision` as append‑only; include date stamps for traceability.

### 11.3 Developer documentation with synchronized code listings

- Goal: keep examples synced with docs and ship channel‑specific bundles.
- Tracks: `code` for listings; optional `media_ref` for demos.
- Flow: update code listings in `code`; search across `code` and `primary` for API drift; export code‑only bundles for IDE extensions and full docs for websites.
- Benefit: reduces drift between narrative and examples; supports tailored distribution.
- Notes: pair `code` listings with tested snippets in CI; consider tangling to source when appropriate.

### 11.4 Scholarly and technical writing with curated references

- Goal: bundle narrative with references and domain annotations.
- Tracks: `reference` for citations/bibliography; optional `commentary` for reviewer notes.
- Flow: maintain references in `reference`; export tight submissions without commentary; archive complete `.mdkv` with all layers for reproducibility.
- Benefit: transparent, reproducible artifacts while enabling audience‑specific exports.
- Notes: adopt a citation style within `reference` tracks and keep DOIs/URLs explicit.

### 11.5 Governance, compliance, and audit trails

- Goal: capture intent and decision history without imposing a VCS workflow on recipients.
- Tracks: `revision` for change logs; document `metadata` fields for release info.
- Flow: record rationale per release in `revision`; embed DOI, version, or policy IDs in `metadata`; export for auditors or regulators with selected layers.
- Benefit: lightweight provenance and traceability without heavy infrastructure.
- Notes: use checksums/signatures described in Appendix C to support integrity attestations.

### 11.6 Product, policy, and dual‑audience documentation

- Goal: publish the same canonical content to internal and external audiences.
- Tracks: `commentary` (internal notes), `reference` (appendices), `media_ref` (assets).
- Flow: export public bundles from `primary` only; export internal bundles with commentary and references for onboarding/support teams.
- Benefit: single source of truth with audience‑appropriate views.
- Notes: mark internal commentary with a prefix (e.g., `INTERNAL:`) to aid filtering.

### 11.7 Digital archiving and long‑term preservation

- Goal: store durable, inspectable artifacts that migrate across tools.
- Tracks: all, with emphasis on `manifest.yaml` readability.
- Flow: write `.mdkv` for archives; include checksums and optional signatures; consumers can inspect and transform with standard tooling.
- Benefit: longevity and portability via ubiquitous primitives (ZIP, YAML, Markdown).
- Notes: include `BUNDLE_INFO.yaml` with source commit metadata when available.

## 12. Implications for Governance and Reproducibility

- Governance: `revision` + metadata expose intent and review structure.
- Reproducibility: deterministic export + manifest versioning.
- Interoperability: ubiquitous primitives (ZIP, YAML, Markdown).
- Diff‑friendliness: semantic separation reduces merge conflicts.
- Extensibility: add track types/exporters without core changes.
- Supply-chain clarity: explicit manifests, source hashes and runtime records make a specific bundle auditable; deterministic text composition is not a byte-reproducible build certification.

### Licensing and community

- **License**: Apache‑2.0. See [LICENSE](https://github.com/docxology/mdkv/blob/main/LICENSE) in the repository.
- **Source & issues**: development and issue tracking on the [GitHub repository](https://github.com/docxology/mdkv).
- **Contributions**: small, focused pull requests preferred; tests and docs alongside changes.

### Security and Privacy Considerations

- `.mdkv` bundles are not encrypted; sensitive content SHOULD be managed with appropriate transport and storage controls (e.g., encryption at rest, signed artifacts).
- `metadata` may contain personally identifiable information; producers SHOULD minimize PII and consumers SHOULD handle metadata under applicable policies.
- Track headers in exported Markdown are informational; avoid embedding secrets in headers or comments.
- Validation is minimal by design; distributors SHOULD layer additional checks where provenance and integrity are critical (e.g., checksums, signatures).

### Evidence and limitations of this methods description

The examples in this paper and `library/definitions/` are authored synthetic
demonstrations, not empirical datasets. This work reports no user study,
comparative benchmark, empirical validation of an active-inference model, or
measured improvement in governance, collaboration, cognition or merge-conflict rates. The use-case
benefits are design motivations and hypotheses, not experimental findings.

For implementation assurance, the repository's versioned release receipt records
the exact runtime, commands, source binding and observed checks. Statement
coverage measures executed statements, not conformance completeness or security.
The defensive review models a malicious document supplier and a website
attempting access to the loopback GUI; hostile same-user processes, collaborative
concurrency and external Pandoc/LaTeX resource policies remain outside that model.
History helpers are standalone in-memory objects; MDKV does not automatically
persist edits as revision history. Unknown ZIP members and unknown manifest keys
are not preserved by model-based save/load roundtrips.

### Cryptographic provenance and signing

- Manifest and track checksums: producers MAY compute SHA‑256 (or stronger) digests for each file and include them in `metadata` for integrity verification after transport.
- Container signing: producers MAY sign the `.mdkv` archive (e.g., using minisign or GPG) and distribute the signature alongside the artifact. Consumers SHOULD verify signatures prior to ingest in security‑sensitive contexts.
- Reproducibility scope: fixed document fields, track order and renderer versions give deterministic text exports. ZIP timestamps and bundle generation timestamps are not byte-reproducible build guarantees; published checksums verify the particular supplied artifacts, not independent rebuild identity.
- Threat model notes: code tracks are not executed by MDKV. Version 0.12.0 disables raw HTML in its HTML renderers, escapes diff descriptions, sandboxes GUI previews and rejects foreign browser origins/hosts. This is not authentication, an external-resource fetch sandbox, or isolation from another process running as the same user.

### Interoperability and Migration Guidance

- Content SHOULD be authored in CommonMark‑compatible Markdown to maximize renderer compatibility.
- For downstream channels (PDF/EPUB), use `to_markdown()` with pandoc‑compatible flags/templates; retain track headers to assist provenance.
- When migrating legacy multi‑file projects, prefer one‑track‑per‑file mapping under `tracks/` and encode provenance in `metadata`.

## 13. Related Work: Containers, Markdown and Publication Pipelines

- Matroska (MKV): multimedia container with EBML, multiplexing heterogeneous streams and metadata. Conceptually adjacent as a container design; orthogonal in domain (binary streams vs. plaintext tracks).
- CommonMark: Markdown specification underpinning content rendering; MDKV does not require new Markdown syntax. The reference HTML renderer's pipe-table support is an explicit rendering profile.
- EPUB/PDF pipelines: rich, distribution‑focused bundles; MDKV targets authoring/editing unity and channel‑agnostic composition, and can serve as an upstream source for such exporters.
- Jupyter notebooks: literate, executable documents combining code and text; MDKV focuses on non‑executable, layered textual artifacts with optional code listings.

## 14. Future Work: Validation Profiles and Richer Exporters

- Validation profiles: optional, stricter validators (coverage constraints, reference bibliography schemas).
- Exporter evolution: PDF/EPUB/DOCX are already implemented through optional Pandoc; further work includes track-aware templates and rendering profiles.
- Track alignment aids: soft anchors and cross‑track link conventions for advanced localization/review.
- Provenance and signing: cryptographic checksums and signatures for manifests and tracks.
- Remote storage: mapping tracks to object stores while preserving a virtual manifest.
- Richer GUI: current per-track editing, selective preview and diff views do not implement collaborative editing or translation alignment.

## 15. Conclusion: A Small Format with Explicit Boundaries

MDKV introduces a practical, minimal, and extensible approach to multitrack textual documents. By embracing simple, durable primitives (Markdown, YAML, ZIP) and separating core modeling from storage and services, MDKV enables multilingual and multi‑audience authoring without branching, improves governance through explicit layer semantics, and supports reproducible publishing. As the ecosystem evolves, MDKV can integrate stronger validation profiles and richer exporters while preserving its core promise: a small, inspectable container for structured documents that travels well and ages gracefully.

## References

- Lhomme, S.; Bunkus, M.; Rice, D. (2024). [Matroska Media Container Format Specification, RFC 9559](https://www.rfc-editor.org/rfc/rfc9559).
- MacFarlane, J. (2024). [CommonMark Specification 0.31.2](https://spec.commonmark.org/0.31.2/).
- YAML Language Development Team (2021). [YAML 1.2.2 specification](https://yaml.org/spec/1.2.2/).
- ZIP Appnote (PKWARE): [PKWARE Appnote](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT)
- markdown‑it‑py project: [executablebooks/markdown-it-py](https://github.com/executablebooks/markdown-it-py)
- Astral uv project: [astral-sh/uv](https://github.com/astral-sh/uv)

## Appendix A: Glossary

- MDKV: Multitrack Markdown container defined by this specification.
- Track: A named, typed Markdown layer within an MDKV document (e.g., `primary`, `translation`).
- Manifest: YAML file at the root of the container that indexes tracks and captures metadata.
- Round-trip: exact modeled field and track-text preservation through ZIP or JSON. Combined Markdown is a presentation export; embedded header-like text is not escaped into a reversible interchange format.
- Conformance: Degree to which an implementation satisfies normative requirements in this document.

## Appendix B: Informational Headers, Pandoc Recipes and Tooling Checks

The informational header emitted in combined exports has the following shape. It does not distinguish literal header-like text in a track body and must not be used as a lossless parser:

```text
<!--\s+track:{track_id}\s+type:{track_type}\s+lang:{language}\s+-->
```

When language is unspecified, the literal text `None` is emitted for `{language}`.

### B.1 Pandoc pipeline (PDF)

```bash
# export only the primary track, with explicit title/author frontmatter
uv run mdkv export paper.mdkv --types primary --metadata-header > primary.md
pandoc primary.md --resource-path=paper --pdf-engine=xelatex -o primary.pdf
```

### B.2 Inspect and verify

```bash
# show manifest summary and tracks
uv run mdkv info paper.mdkv | sed -n '1,60p'

# validate and list tracks
uv run mdkv validate paper.mdkv
uv run mdkv list-tracks paper.mdkv
```

### B.3 When to choose MDKV

- **You need layered authorship**: separate canonical text, translations, commentary, references, code listings, and revisions without branching the project.
- **You want reproducible bundles**: deterministic exports and manifest‑driven structure make builds auditable.
- **You prefer plain text pipelines**: leverage Markdown/YAML and existing tools (git, grep, pandoc) rather than custom ecosystems.
- **You need selective exports**: tailor by track types or build explicit track views; direct language filtering is a search feature.
- **You need to be able to edit the document via multiple tools**: MDKV is a container for text, not a text editor.
- **You want to use an open source format to ensure long-term compatibility**: MDKV is a small, simple, modular, and well-documented format that is licensed under the Apache 2.0 license.

- `track_id`: string, unique per document
- `track_type`: one of `primary, translation, commentary, code, reference, media_ref, revision`
- `language`: BCP‑47 code or `None`

## Appendix C: Bundle Artifacts, Checksums and Verification

This appendix sketches the files created by the builder (`paper/build_paper_bundle.py`) to support reproducible publication and verification.

- `paper/paper.mdkv`: ZIP archive with `manifest.yaml` and `tracks/` (e.g., `tracks/primary.md`, optional `tracks/references.md`).
- `paper/_bundle/paper.md`: primary-only Markdown with title/author frontmatter; the reference track is not duplicated in the publication stream.
- `paper/_bundle/paper.html`: HTML of the `primary` track from `to_html()`.
- `paper/_bundle/tracks/`: individual per‑track Markdown files exported for distribution pipelines.
- `paper/_bundle/figures/`: copied SVG/PNG figure assets referenced by the manuscript.
- `paper/_bundle/BUNDLE_INFO.yaml`: source/builder/lock hashes, runtime versions, timestamps, dirty state and optional exact clone identity.
- `paper/_bundle/CHECKSUMS.yaml`: exact artifact SHA-256 digests, with keys relative to the bundle directory's parent (including custom output names).

Example excerpt of `BUNDLE_INFO.yaml`:

```yaml
generated_at: 2025-08-10T12:34:56Z
source_markdown: mdkv_paper.md
output_mdkv: paper.mdkv
repo_url: https://github.com/docxology/mdkv
cloned_commit: 0123abcd...
builder_commit: 89ef4567...
```

Example excerpt of `CHECKSUMS.yaml`:

```yaml
_bundle/paper.html: 7f4c2b...
_bundle/paper.md: 8b91fe...
_bundle/tracks/primary.md: 0b12aa...
_bundle/figures/mdkv-graphical-abstract.png: 9d31c0...
paper.mdkv: 5c44d1...
```
