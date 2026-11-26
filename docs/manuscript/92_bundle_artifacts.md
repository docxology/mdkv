# Appendix C: Bundle Artifacts, Checksums and Verification

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
source_markdown: docs/manuscript/
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
