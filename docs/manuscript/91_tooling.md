# Appendix B: Informational Headers, Pandoc Recipes and Tooling Checks

The informational header emitted in combined exports has the following shape. It does not distinguish literal header-like text in a track body and must not be used as a lossless parser:

```text
<!--\s+track:{track_id}\s+type:{track_type}\s+lang:{language}\s+-->
```

When language is unspecified, the literal text `None` is emitted for `{language}`.

## B.1 Pandoc pipeline (PDF)

```bash
# export only the primary track, with explicit title/author frontmatter
uv run mdkv export paper.mdkv --types primary --metadata-header > primary.md
pandoc primary.md --resource-path=paper --pdf-engine=xelatex -o primary.pdf
```

## B.2 Inspect and verify

```bash
# show manifest summary and tracks
uv run mdkv info paper.mdkv | sed -n '1,60p'

# validate and list tracks
uv run mdkv validate paper.mdkv
uv run mdkv list-tracks paper.mdkv
```

## B.3 When to choose MDKV

- **You need layered authorship**: separate canonical text, translations, commentary, references, code listings, and revisions without branching the project.
- **You want reproducible bundles**: deterministic exports and manifest‑driven structure make builds auditable.
- **You prefer plain text pipelines**: leverage Markdown/YAML and existing tools (git, grep, pandoc) rather than custom ecosystems.
- **You need selective exports**: tailor by track types or build explicit track views; direct language filtering is a search feature.
- **You need to be able to edit the document via multiple tools**: MDKV is a container for text, not a text editor.
- **You want to use an open source format to ensure long-term compatibility**: MDKV is a small, simple, modular, and well-documented format that is licensed under the Apache 2.0 license.

- `track_id`: string, unique per document
- `track_type`: one of `primary, translation, commentary, code, reference, media_ref, revision`
- `language`: BCP‑47 code or `None`
