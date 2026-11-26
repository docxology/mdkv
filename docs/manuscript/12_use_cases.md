# Use Cases: From Localization to Audit Trails

## Multilingual publishing and localization

- Goal: ship a single canonical text to multiple locales without forking.
- Tracks: `primary` (en), `translation` (ru, zh, …).
- Flow: author primary/translation tracks and search by language. To export a locale, select the corresponding tracks in a document view before type-filtered export; there is no direct language-export parameter.
- Intended benefit: organizing locale variants without requiring separate repositories. This has not been empirically compared with branching workflows.
- Notes: reserve `track_id` values for ISO language tags where possible (e.g., `ru`, `zh-Hans`).

## Layered collaboration, review, and stakeholder tailoring

- Goal: separate canonical narrative from internal commentary and change rationale.
- Tracks: `commentary`, `revision` alongside `primary`.
- Flow: reviewers annotate in `commentary`; change summaries accrue in `revision`; public exports omit commentary; internal exports include it for audit and coaching.
- Benefit: clean public artifacts with rich internal discourse and governance trails.
- Notes: treat `revision` as append‑only; include date stamps for traceability.

## Developer documentation with synchronized code listings

- Goal: keep examples synced with docs and ship channel‑specific bundles.
- Tracks: `code` for listings; optional `media_ref` for demos.
- Flow: update code listings in `code`; search across `code` and `primary` for API drift; export code‑only bundles for IDE extensions and full docs for websites.
- Benefit: reduces drift between narrative and examples; supports tailored distribution.
- Notes: pair `code` listings with tested snippets in CI; consider tangling to source when appropriate.

## Scholarly and technical writing with curated references

- Goal: bundle narrative with references and domain annotations.
- Tracks: `reference` for citations/bibliography; optional `commentary` for reviewer notes.
- Flow: maintain references in `reference`; export tight submissions without commentary; archive complete `.mdkv` with all layers for reproducibility.
- Benefit: transparent, reproducible artifacts while enabling audience‑specific exports.
- Notes: adopt a citation style within `reference` tracks and keep DOIs/URLs explicit.

## Governance, compliance, and audit trails

- Goal: capture intent and decision history without imposing a VCS workflow on recipients.
- Tracks: `revision` for change logs; document `metadata` fields for release info.
- Flow: record rationale per release in `revision`; embed DOI, version, or policy IDs in `metadata`; export for auditors or regulators with selected layers.
- Benefit: lightweight provenance and traceability without heavy infrastructure.
- Notes: use checksums/signatures described in Appendix C to support integrity attestations.

## Product, policy, and dual‑audience documentation

- Goal: publish the same canonical content to internal and external audiences.
- Tracks: `commentary` (internal notes), `reference` (appendices), `media_ref` (assets).
- Flow: export public bundles from `primary` only; export internal bundles with commentary and references for onboarding/support teams.
- Benefit: single source of truth with audience‑appropriate views.
- Notes: mark internal commentary with a prefix (e.g., `INTERNAL:`) to aid filtering.

## Digital archiving and long‑term preservation

- Goal: store durable, inspectable artifacts that migrate across tools.
- Tracks: all, with emphasis on `manifest.yaml` readability.
- Flow: write `.mdkv` for archives; include checksums and optional signatures; consumers can inspect and transform with standard tooling.
- Benefit: longevity and portability via ubiquitous primitives (ZIP, YAML, Markdown).
- Notes: include `BUNDLE_INFO.yaml` with source commit metadata when available.
