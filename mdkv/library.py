from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .core.model import MDKVDocument, Track
from .storage import save_mdkv


def build_document_from_definition(defn: dict[str, Any]) -> MDKVDocument:
    created = defn.get("created")
    if isinstance(created, str):
        created_dt = datetime.fromisoformat(created)
    elif isinstance(created, datetime):
        created_dt = created
    else:
        created_dt = datetime.now(UTC)
    doc = MDKVDocument(
        title=defn["title"],
        authors=list(defn.get("authors", [])),
        created=created_dt,
    )
    for t in defn.get("tracks", []):
        track = Track(
            track_id=t["id"],
            track_type=t["type"],
            language=t.get("language"),
            path=f"tracks/{t['id']}.md",
            content=t.get("content", ""),
        )
        doc.add_track(track)
    return doc


def load_example_definition(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return {}
    return {str(k): v for k, v in loaded.items()}


def build_all_examples(definitions_dir: Path, out_dir: Path) -> list[Path]:
    definitions_dir = Path(definitions_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for yml in sorted(definitions_dir.glob("*.yaml")):
        defn = load_example_definition(yml)
        doc = build_document_from_definition(defn)
        out_path = out_dir / (yml.stem + ".mdkv")
        save_mdkv(doc, out_path)
        outputs.append(out_path)
    return outputs
