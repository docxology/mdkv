from __future__ import annotations

"""Persistence layer for MDKV containers.

A ``.mdkv`` file is a ZIP archive containing a ``manifest.yaml`` and a
``tracks/`` directory with UTF-8 Markdown files. This module
serializes/deserializes ``MDKVDocument`` instances to/from that container
format.
"""

import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import yaml

from mdkv.core.model import MDKVDocument, Track
from mdkv.core.errors import ValidationError


MANIFEST_NAME = "manifest.yaml"


class MDKVFormatError(Exception):
    """Raised when a ``.mdkv`` container is structurally invalid."""


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
    """Reconstruct a document from a parsed manifest and the ZIP handle.

    Raises ``MDKVFormatError`` if the manifest is missing required keys
    or a referenced track file does not exist in the archive.
    """
    # Required manifest fields
    for key in ("title", "created"):
        if key not in manifest:
            raise MDKVFormatError(f"manifest missing required key: {key}")

    doc = MDKVDocument(
        title=manifest["title"],
        authors=list(manifest.get("authors", [])),
        created=datetime.fromisoformat(manifest["created"]),
        version=manifest.get("version", "0.1"),
    )
    doc.metadata.update(manifest.get("metadata", {}))
    for entry in manifest.get("tracks", []):
        for key in ("track_id", "track_type", "path"):
            if key not in entry:
                raise MDKVFormatError(f"track entry missing required key: {key}")
        path = entry["path"]
        # Verify the track file exists in the archive
        try:
            with file_reader.open(path) as f:
                content = f.read().decode("utf-8")
        except KeyError:
            raise MDKVFormatError(f"track file '{path}' not found in container")
        try:
            track = Track(
                track_id=entry["track_id"],
                track_type=entry["track_type"],
                language=entry.get("language"),
                path=path,
                content=content,
            )
        except ValueError as exc:
            raise MDKVFormatError(f"invalid track definition for '{entry.get('track_id', '?')}': {exc}")
        doc.add_track(track)
    return doc


def save_mdkv(
    doc: MDKVDocument,
    output_path: Path,
    compression: int = zipfile.ZIP_DEFLATED,
    compresslevel: int | None = None,
) -> None:
    """Write ``doc`` to ``output_path`` as a ``.mdkv`` ZIP container.

    Overwrites existing files. Creates parent directories as needed.
    Raises ``ValidationError`` if two tracks share the same container path
    (which would cause silent data loss in the ZIP).

    Args:
        doc: Document to save.
        output_path: Target file path.
        compression: ZIP compression method (default ``ZIP_DEFLATED``).
            Use ``ZIP_STORED`` for no compression (faster for already-compressed content).
        compresslevel: Compression level 0-9 (default: zlib default). Only affects
            ``ZIP_DEFLATED``. Ignored on Python < 3.7.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = _manifest_from_doc(doc)
    # Detect duplicate paths — ZIP would silently overwrite one track with another
    seen_paths: dict[str, str] = {}
    for track in doc.tracks.values():
        if track.path in seen_paths:
            raise ValidationError(
                f"tracks '{seen_paths[track.path]}' and '{track.track_id}' share path '{track.path}'"
            )
        seen_paths[track.path] = track.track_id
    kwargs: dict[str, Any] = {"mode": "w", "compression": compression}
    if compresslevel is not None:
        kwargs["compresslevel"] = compresslevel
    with zipfile.ZipFile(output_path, **kwargs) as zf:
        for track in doc.tracks.values():
            zf.writestr(track.path, track.content)
        zf.writestr(MANIFEST_NAME, yaml.safe_dump(manifest, sort_keys=False))


def save_mdkv_incremental(doc: MDKVDocument, output_path: Path) -> bool:
    """Save to an existing .mdkv file, reusing unchanged track content.

    Reads the existing container's manifest and track bytes, then writes a
    new container that carries unchanged tracks over verbatim and only
    rewrites the tracks whose content changed (plus the manifest). Falls
    back to a full ``save_mdkv`` if the file doesn't exist or its manifest
    is unreadable.

    Returns ``True`` if the file existed and was rewritten incrementally,
    ``False`` if a full save fallback was performed.
    """
    output_path = Path(output_path)
    if not output_path.exists():
        save_mdkv(doc, output_path)
        return False
    try:
        # Read existing manifest and track contents so unchanged tracks can be
        # carried over instead of rewritten.
        with zipfile.ZipFile(output_path, mode="r") as zf_old:
            if MANIFEST_NAME not in zf_old.namelist():
                save_mdkv(doc, output_path)
                return False
            old_manifest = yaml.safe_load(zf_old.open(MANIFEST_NAME).read().decode("utf-8"))
            if not isinstance(old_manifest, dict):
                save_mdkv(doc, output_path)
                return False
            old_contents: dict[str, str] = {}
            for entry in old_manifest.get("tracks", []):
                path = entry.get("path", "")
                if not path:
                    continue
                try:
                    old_contents[path] = zf_old.open(path).read().decode("utf-8")
                except KeyError:
                    pass
    except (zipfile.BadZipFile, OSError, UnicodeDecodeError, yaml.YAMLError):
        save_mdkv(doc, output_path)
        return False
    # Write everything to a temp file, then rename (atomic on POSIX)
    new_manifest = _manifest_from_doc(doc)
    tmp_path = output_path.with_suffix(".mdkv.tmp")
    with zipfile.ZipFile(tmp_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for track in doc.tracks.values():
            old = old_contents.get(track.path)
            content = track.content if old is None or old != track.content else old
            zf.writestr(track.path, content)
        zf.writestr(MANIFEST_NAME, yaml.safe_dump(new_manifest, sort_keys=False))
    tmp_path.replace(output_path)
    return True


def load_mdkv(input_path: Path) -> MDKVDocument:
    """Load a ``.mdkv`` document from ``input_path``.

    Raises ``MDKVFormatError`` for corrupt or missing manifests.
    Raises ``FileNotFoundError`` if the file does not exist.
    """
    p = Path(input_path)
    if not p.exists():
        raise FileNotFoundError(f"file not found: {p}")
    try:
        with zipfile.ZipFile(p, mode="r") as zf:
            if MANIFEST_NAME not in zf.namelist():
                raise MDKVFormatError(f"manifest '{MANIFEST_NAME}' not found in container")
            with zf.open(MANIFEST_NAME) as f:
                manifest = yaml.safe_load(f.read().decode("utf-8"))
            if not isinstance(manifest, dict):
                raise MDKVFormatError("manifest is not a valid YAML mapping")
            return _doc_from_manifest(manifest, zf)
    except zipfile.BadZipFile:
        raise MDKVFormatError(f"not a valid ZIP archive: {p}")
