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

# remove a track
uv run mdkv remove-track doc.mdkv --id notes

# export selected track types as Markdown
uv run mdkv export-tracks doc.mdkv --types primary,commentary

# diff two documents
uv run mdkv diff doc_v1.mdkv doc_v2.mdkv

# show statistics
uv run mdkv stats doc.mdkv

# case-insensitive search
uv run mdkv search doc.mdkv --pattern "hello" -i
```

## Python API (public surface)

```python
from datetime import datetime, timezone
from mdkv import (
  MDKVDocument, Track,
  save_mdkv, load_mdkv,
  validate_document,
  export_to_files,
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

To record a short demo (optional): see `examples/record_gui_demo.py`. If you have `ffmpeg` and ImageMagick, you can convert the recorded `.webm` to `.gif` for embedding.
