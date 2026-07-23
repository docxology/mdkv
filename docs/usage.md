# Usage

## Install and run with uv

```bash
uv venv
uv run mdkv --help

# or use python -m
python -m mdkv --help
```

## Create a document

```bash
uv run mdkv init --title "Doc" --author "You" --out doc.mdkv
uv run mdkv info doc.mdkv
uv run mdkv validate doc.mdkv
uv run mdkv export doc.mdkv > out.md
uv run mdkv export --html doc.mdkv > out.html
```

## Import from Markdown

```bash
uv run mdkv import README.md --out imported.mdkv --title "Imported" --author "You"
```

## CLI utilities

```bash
# list tracks as JSON
uv run mdkv list-tracks doc.mdkv

# add a commentary track
uv run mdkv add-track doc.mdkv --id notes --type commentary --lang "" --content "Note"

# add a track from a file
uv run mdkv add-track doc.mdkv --id notes --type commentary --file notes.md

# remove a track
uv run mdkv remove-track doc.mdkv --id notes

# rename a track
uv run mdkv rename-track doc.mdkv --old-id notes --new-id annotations

# update track content
uv run mdkv update-track doc.mdkv --id primary --content "# Updated"
uv run mdkv update-track doc.mdkv --id primary --file updated.md

# export selected track types as Markdown
uv run mdkv export-tracks doc.mdkv --types primary,commentary

# export with YAML frontmatter
uv run mdkv export doc.mdkv --metadata-header > out.md

# diff two documents
uv run mdkv diff doc_v1.mdkv doc_v2.mdkv

# show statistics
uv run mdkv stats doc.mdkv

# case-insensitive search
uv run mdkv search doc.mdkv --pattern "hello" -i

# validate with JSON output (for CI/automation)
uv run mdkv validate doc.mdkv --json

# metadata operations
uv run mdkv set-meta doc.mdkv author "Another"
uv run mdkv get-meta doc.mdkv author

# show license information
uv run mdkv license
```

## Python API (public surface)

```python
from datetime import datetime, timezone
from mdkv import (
  MDKVDocument, Track,
  save_mdkv, load_mdkv,
  validate_document,
  export_to_files,
  diff_documents, DiffResult,
  compute_stats, DocumentStats,
)

doc = MDKVDocument(title="T", authors=["A"], created=datetime.now(timezone.utc))
doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Title\n\nText"))
doc.list_languages()  # ["en"]

save_mdkv(doc, "doc.mdkv")
loaded = load_mdkv("doc.mdkv")
validate_document(loaded)

# access and remove
track = loaded.get_track("primary")
removed = loaded.remove_track("primary")

# write each track to its own .md file
from pathlib import Path
written = export_to_files(loaded, Path("out_tracks"), include_track_types=["primary", "commentary"])
```

### JSON serialization

```python
from mdkv import MDKVDocument, Track
from datetime import datetime, timezone

doc = MDKVDocument(title="T", authors=["A"], created=datetime.now(timezone.utc))
doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Hello"))

# serialize to dict (JSON-compatible)
data = doc.to_dict()
import json
print(json.dumps(data, indent=2))

# reconstruct from dict
restored = MDKVDocument.from_dict(data)
assert restored.title == doc.title
```

### Diff and stats

```python
from mdkv import diff_documents, compute_stats, load_mdkv

doc_a = load_mdkv("doc_v1.mdkv")
doc_b = load_mdkv("doc_v2.mdkv")

# Compare two documents
result = diff_documents(doc_a, doc_b)
if result.has_changes:
    print(result.to_dict())
else:
    print("Documents are identical")

# Compute statistics
stats = compute_stats(doc_a)
print(f"{stats.track_count} tracks, {stats.total_characters} chars, {stats.total_lines} lines")
print(f"Languages: {stats.languages}")
print(f"Track types: {stats.tracks_by_type}")

# Access track IDs as a list
print(f"Track IDs: {doc_a.track_ids}")

# Validate a single track
from mdkv import validate_track
test_track = Track("notes", "commentary", None, "tracks/notes.md", "Some notes")
issues = validate_track(test_track)
for issue in issues:
    print(f"{issue.level}: {issue.message}")

# Move a track to a new position
doc_a.move_track("notes", "primary")  # Move 'notes' after 'primary'
doc_a.move_track("notes", None)  # Move 'notes' to first position
```

### From YAML definitions

The `library/definitions/` directory contains YAML examples you can convert to `.mdkv` using the included helper:

```python
from pathlib import Path
from mdkv.library import build_all_examples

build_all_examples(Path('library/definitions'), Path('library/_built'))
```

## Logging & workflows

- Configure logging with `mdkv.common.configure_logging()`.
- See `examples/logged_workflow.py` for an end-to-end script that logs steps and writes outputs to `workflow_out/`.

## GUI

Launch the local web GUI (two-pane editor/preview):

```bash
uv run mdkv gui --path doc.mdkv
# or with the convenience launcher
python3 run_gui.py --path doc.mdkv
```

In the GUI preview toolbar, use checkboxes to toggle which tracks are shown:
- All: renders all tracks.
- Custom: uncheck All and select any combination of tracks; the preview updates live. Selecting none shows an empty preview.

The editor pane always holds the full combined Markdown (round-trippable).

### GUI REST API

The GUI server exposes additional endpoints beyond the CRUD operations:

- `GET /api/search?pattern=...&types=...&languages=...&case_insensitive=true` — search tracks
- `GET /api/stats` — document statistics
- `POST /api/diff` with `{"path": "other.mdkv"}` — diff against another document
- `POST /api/validate` — returns warnings alongside errors
- `POST /api/document` — update title, authors, version, and metadata
- `POST /api/track` — create or update a track (validates track_type)
- `DELETE /api/track/{track_id}` — remove a track (returns 404 if not found)

To record a short demo (optional): see `examples/record_gui_demo.py`. If you have `ffmpeg` and ImageMagick, you can convert the recorded `.webm` to `.gif` for embedding.
