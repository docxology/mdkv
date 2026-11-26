# Build the manuscript and MDKV bundle

The [canonical manuscript](https://github.com/docxology/mdkv/tree/main/docs/manuscript)
holds the numbered sections, configured publication metadata, bibliography,
and graphical abstract. Output formats are specified in its `config.yaml`.

## Native bundle

After [installing the project](usage.md), run from the
repository root. Use explicit destination paths to preserve the archived
publication in `paper/`.

```sh
build=$(mktemp -d)
bash paper/build_paper_bundle.sh --no-clone --out "$build/paper.mdkv" --bundle-dir "$build/bundle"
uv run --no-sync mdkv validate "$build/paper.mdkv"
uv run --no-sync mdkv list-tracks "$build/paper.mdkv"
```

The builder emits the container, Markdown and HTML exports, separate tracks,
figure assets, and provenance and checksum files. `BUNDLE_INFO.yaml` records
the digest of the composed Markdown for the canonical tree. A custom single
Markdown file may still be supplied via `--markdown` with title, author, and
timezone-aware creation metadata. `CHECKSUMS.yaml` verifies the corresponding
output bytes. The native bundle builder does not produce a PDF.

## Pinned Template PDF and HTML

Install Python 3.14, uv, Pandoc 3.14, pandoc-crossref v0.3.26b, XeLaTeX with the
[Template TeX packages](https://github.com/docxology/template/blob/87704feae0a4490ef7dad9c931d268e8c30273c2/README.md#L565-L574),
and Noto Sans Mono CJK SC for multilingual examples. Set `MDKV_CHECKOUT` to the
absolute path of your MDKV checkout, then register a detached copy.

```sh
git clone https://github.com/docxology/template.git mdkv-template-runner
cd mdkv-template-runner
git checkout --detach 87704feae0a4490ef7dad9c931d268e8c30273c2
uv sync --locked --python 3.14
project=projects/working/mdkv
mkdir -p projects/working
git -C "$MDKV_CHECKOUT" worktree add --detach "$PWD/$project" HEAD
uv run python "$project/scripts/01_prepare_manuscript.py"
uv run python scripts/pipeline/stage_03_render.py --project working/mdkv
uv run python scripts/pipeline/stage_04_validate.py --project working/mdkv
```

Inspect `$project/output/pdf/mdkv_combined.pdf` and
`$project/output/web/index.html`. The validation report and rendered
provenance are under `$project/output/reports/`.
