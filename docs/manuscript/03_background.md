# Background: Why Containerize Documents?

## Matroska (MKV): History and Technical Context

The [Matroska specification, RFC 9559](https://www.rfc-editor.org/rfc/rfc9559),
published in October 2024 by Steve Lhomme, Moritz Bunkus and Dave Rice, defines
an audiovisual container based on EBML. Its independently described tracks
provide a design analogy here, not evidence that a ZIP/YAML text format inherits
Matroska's streaming, recovery or interoperability properties.

MDKV does not implement Matroska or EBML. Historical adoption timelines are not
needed to establish the text-container design and are not evaluated in this work.

## MDKV and MKV: Orthogonal Domains, Shared Intuition

MDKV is not an MKV editor, wrapper, or derivative; it targets plaintext documents rather than multimedia. The similarity in names is intentional only insofar as both are “container‑centric” designs. MDKV borrows the intuition that many artifacts are multi‑track by nature, but it embraces a radically simpler substrate—[Markdown (CommonMark)](https://commonmark.org), [YAML](https://yaml.org/spec/), and [ZIP](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT)—to maximize openness, inspectability, and compatibility with standard tooling. Where MKV multiplexes time‑based streams, MDKV co‑packages logically distinct textual layers.

## Why a textual container (vs. multimedia/EPUB/PDF)

- **Keep primitives simple**: plain Markdown + YAML + ZIP are ubiquitous, inspectable, and durable; no custom binary framing.
- **Multi‑track authorship, not playback**: MDKV is for co‑authoring and distributing textual layers in parallel; it is not a media streaming format.
- **Deterministic composition**: exports are reproducible from a manifest and track set, supporting provenance and verification.
- **Toolchain leverage**: downstream pipelines (e.g., [pandoc](https://pandoc.org)) can consume `to_markdown()` outputs directly.
- **Manage external assets**: media stays outside via `media_ref` tracks, keeping bundles lean while links remain explicit and reviewable.
- **Human‑first diffs**: separate files per track minimize merge conflicts and make reviews targeted.
- **Sovereign metadata**: `manifest.yaml` is explicit and auditable; no hidden state.
