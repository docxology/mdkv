# Manuscript Status: Source, Bundle and Release Evidence

- Repo type: Modular Python implementation of the MDKV multitrack-markdown container
- Publication source is `paper/mdkv_paper.md`; the owning builder emits `paper.mdkv`, primary Markdown/HTML, copied `figures/` assets and provenance/checksums. `build_paper_bundle.sh --no-clone` does not build a PDF.
- Trigger for creating a manuscript/ tree: only if a new manuscript distinct from `paper/` is started.

Audited 2026-08-29 (docs_audit_2026-08-29 fleet); publication-track line corrected 2026-10-25.

The 0.12.0 audit corrects attribution and implementation claims in that source.
`mdkv_v1_DAF_08-10-2025.pdf` is the preserved historical DOI deposit, not a render
of the current revised manuscript. New candidate render/proof artifacts are
identified separately in the repository release receipt. Do not replace the
historical PDF or claim that its DOI has been updated by a software release.

Bundle source custody is observed before generating outputs. `builder_dirty`
is null when Git status is unavailable, never an inferred clean result. SHA-256
fields bind the actual manuscript, builder and lockfile; generation timestamps
and ZIP bytes may vary.
