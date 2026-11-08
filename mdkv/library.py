from __future__ import annotations

from datetime import UTC, datetime
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any

import yaml

from .core.model import MDKVDocument, Track
from .storage import save_mdkv


def build_document_from_definition(defn: dict[str, Any]) -> MDKVDocument:
    """Build an independent document, preserving canonical definition metadata."""
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
        version=defn.get("version", "0.1"),
        metadata=dict(defn.get("metadata", {})),
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


def example_definitions_dir() -> Traversable:
    """Return read-only canonical YAML resources in editable or installed builds.

    The resource package maps to the authored ``library/`` directory at build
    time. Callers must use the Traversable read API, not assume a filesystem path
    or create generated containers beside these resources.
    """
    return files("mdkv.resources").joinpath("definitions")


def load_example_definition(path: Traversable) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return {}
    return {str(k): v for k, v in loaded.items()}


def load_example_document(name: str) -> MDKVDocument:
    """Load a fresh in-memory example by canonical YAML filename; never write it."""
    if not name.endswith(".yaml") or "/" in name or "\\" in name or "\x00" in name:
        raise ValueError("example name must be a single canonical .yaml filename")
    definition = example_definitions_dir().joinpath(name)
    if not definition.is_file():
        raise FileNotFoundError(name)
    return build_document_from_definition(load_example_definition(definition))


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
