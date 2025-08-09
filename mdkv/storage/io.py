from __future__ import annotations

"""MDKV storage layer: read/write `.mdkv` containers.

The `.mdkv` format is a ZIP archive containing a `manifest.yaml` plus Markdown
files under the `tracks/` directory. This module serializes an
`MDKVDocument` to disk and reconstructs it from a manifest and track files.
"""

import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import yaml

from mdkv.core.model import MDKVDocument, Track


MANIFEST_NAME = "manifest.yaml"


def _manifest_from_doc(doc: MDKVDocument) -> Dict[str, Any]:
    """Build a manifest dict from an `MDKVDocument`.

    The manifest records metadata and a table of track descriptors; track content
    itself is kept in separate files inside the ZIP under `tracks/`.
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
    """Construct an `MDKVDocument` from a manifest + ZIP file reader.

    Expects `manifest.yaml` schema as produced by `_manifest_from_doc`.
    """
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
    """Write `doc` to a `.mdkv` file at `output_path`.

    Writes each track content at its `Track.path` and a `manifest.yaml` file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = _manifest_from_doc(doc)
    with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for track in doc.tracks.values():
            zf.writestr(track.path, track.content)
        zf.writestr(MANIFEST_NAME, yaml.safe_dump(manifest, sort_keys=False))


def load_mdkv(input_path: Path) -> MDKVDocument:
    """Read a `.mdkv` file from `input_path` and return an `MDKVDocument`."""
    with zipfile.ZipFile(Path(input_path), mode="r") as zf:
        with zf.open(MANIFEST_NAME) as f:
            manifest = yaml.safe_load(f.read().decode("utf-8"))
        return _doc_from_manifest(manifest, zf)


