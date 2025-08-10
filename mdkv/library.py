from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from .core.model import MDKVDocument, Track
from .storage import save_mdkv


def build_document_from_definition(defn: Dict[str, Any]) -> MDKVDocument:
    doc = MDKVDocument(title=defn["title"], authors=list(defn.get("authors", [])), created=defn.get("created") or __import__("datetime").datetime.utcnow())
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


def load_example_definition(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def build_all_examples(definitions_dir: Path, out_dir: Path) -> List[Path]:
    definitions_dir = Path(definitions_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []
    for yml in sorted(definitions_dir.glob("*.yaml")):
        defn = load_example_definition(yml)
        doc = build_document_from_definition(defn)
        out_path = out_dir / (yml.stem + ".mdkv")
        save_mdkv(doc, out_path)
        outputs.append(out_path)
    return outputs


