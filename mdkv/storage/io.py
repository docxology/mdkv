from __future__ import annotations

"""Persistence layer for MDKV containers.

A `.mdkv` file is a ZIP archive containing a `manifest.yaml` and a `tracks/`
directory with UTF-8 Markdown files. This module serializes/deserializes
`MDKVDocument` instances to/from that container format.
"""

import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import yaml

from mdkv.core.model import MDKVDocument, Track


MANIFEST_NAME = "manifest.yaml"


def _manifest_from_doc(doc: MDKVDocument) -> Dict[str, Any]:
    """Create a manifest dictionary suitable for YAML emission.

    The manifest lists metadata and an index of tracks with paths. Track content
    is stored separately as files within the ZIP.
    """
    return {
        "title": doc.title,
        "authors": list(doc.authors),
        "created": doc.created.isoformat(),
        "version": doc.version,
        "metadata": dict(doc.metadata),
        "tracks": [
            {
                "track_id": t.track_id,
                "track_type": t.track_type,
                "language": t.language,
                "path": t.path,
            }
            for t in doc.tracks.values()
        ],
    }


def _doc_from_manifest(manifest: Dict[str, Any], file_reader: zipfile.ZipFile) -> MDKVDocument:
    """Reconstruct a document from a parsed manifest and the ZIP handle."""
    doc = MDKVDocument(
        title=manifest["title"],
        authors=list(manifest.get("authors", [])),
        created=datetime.fromisoformat(manifest["created"]),
        version=manifest.get("version", "0.1"),
    )
    doc.metadata.update(manifest.get("metadata", {}))
    for t in manifest.get("tracks", []):
        path = t["path"]
        with file_reader.open(path) as f:
            content = f.read().decode("utf-8")
        track = Track(
            track_id=t["track_id"],
            track_type=t["track_type"],
            language=t.get("language"),
            path=path,
            content=content,
        )
        doc.add_track(track)
    return doc


def save_mdkv(doc: MDKVDocument, output_path: Path) -> None:
    """Write `doc` to `output_path` as a `.mdkv` ZIP container.

    Overwrites existing files. Creates parent directories as needed.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = _manifest_from_doc(doc)
    with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for track in doc.tracks.values():
            zf.writestr(track.path, track.content)
        zf.writestr(MANIFEST_NAME, yaml.safe_dump(manifest, sort_keys=False))


def load_mdkv(input_path: Path) -> MDKVDocument:
    """Load a `.mdkv` document from `input_path`.

    Raises `KeyError`/`yaml.YAMLError` if the manifest is missing/invalid.
    """
    with zipfile.ZipFile(Path(input_path), mode="r") as zf:
        with zf.open(MANIFEST_NAME) as f:
            manifest = yaml.safe_load(f.read().decode("utf-8"))
        return _doc_from_manifest(manifest, zf)


