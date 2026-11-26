# Usage: CLI, Python API and GUI Workflows

## Quickstart

```bash
# use an existing uv installation; no installer is run by the builder
# from repo root
uv sync --locked --extra dev
uv run pytest -q
uv run mdkv --help
```

## Create, Inspect, Validate

```bash
uv run mdkv init --title "Doc" --author "You" --out doc.mdkv
uv run mdkv info doc.mdkv
uv run mdkv validate doc.mdkv
```

## Track Operations

```bash
uv run mdkv list-tracks doc.mdkv
uv run mdkv add-track doc.mdkv --id notes --type commentary --lang "" --content "Note"
uv run mdkv rename-track doc.mdkv --old-id notes --new-id commentary
uv run mdkv update-track doc.mdkv --id commentary --content "Updated note"
```

## Export and GUI

```bash
# export selected track types to Markdown
uv run mdkv export-tracks doc.mdkv --types primary,commentary > exported.md

# export HTML of primary track
uv run mdkv export --html doc.mdkv > primary.html

# launch GUI
uv run mdkv gui --path doc.mdkv
```

## Programmatic Export

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

## End‑to‑end: create a multi‑track paper

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
