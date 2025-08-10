from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import yaml

from mdkv.model import MDKVDocument, Track
from mdkv.storage import save_mdkv


def build_doc_from_definition(defn: Dict[str, Any]) -> MDKVDocument:
    doc = MDKVDocument(
        title=defn["title"],
        authors=list(defn.get("authors", [])),
        created=datetime.utcnow(),
    )
    for t in defn.get("tracks", []):
        track_id = t["id"]
        track_type = t["type"]
        language = t.get("language")
        content = t.get("content", "")
        path = f"tracks/{track_id}.md"
        doc.add_track(Track(track_id, track_type, language, path, content))
    return doc


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Build .mdkv from YAML definition")
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()

    data = yaml.safe_load(Path(args.input).read_text(encoding="utf-8"))
    doc = build_doc_from_definition(data)
    save_mdkv(doc, args.output)
    print(f"Wrote {args.output}")


