from __future__ import annotations

"""Bounded, non-extracting reads and atomic writes of MDKV ZIP containers.

Containers persist document metadata and tracks, not ``TrackHistory`` objects.

The reader accepts single-disk, non-ZIP64 archives with no prepended/trailing
data and stored or deflated members only. BZIP2/LZMA are deliberately rejected:
some Python ZIP decoders allocate beyond a forged declared uncompressed size.
Every member, including unreferenced extras, is streamed and checked for its
actual size and CRC; extras need not be UTF-8 or document content.
"""

import os
import stat
import struct
import tempfile
import zipfile
import zlib
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import yaml

from mdkv.core.errors import ValidationError
from mdkv.core.model import MDKVDocument, Track
from mdkv.storage.schema import MDKVManifestModel

MANIFEST_NAME = "manifest.yaml"
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_TRACK_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_MEMBERS = 4096
MAX_TRACKS = 1024
MAX_YAML_DEPTH = 32
MAX_YAML_NODES = 10000
_SUPPORTED_COMPRESSION = frozenset({zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED})


class MDKVFormatError(Exception):
    """Raised when a ``.mdkv`` container is structurally invalid."""


class _ManifestLoader(yaml.SafeLoader):
    """Reject YAML aliases, anchors, duplicate keys, and excessive complexity."""

    def __init__(self, stream: str) -> None:
        super().__init__(stream)
        self._depth = 0
        self._nodes = 0

    def compose_node(self, parent: Any, index: Any) -> Any:
        peek = cast(Callable[[], yaml.Event | None], self.peek_event)
        event = peek()
        if isinstance(event, yaml.AliasEvent) or getattr(event, "anchor", None) is not None:
            raise yaml.YAMLError("manifest YAML anchors and aliases are not allowed")
        self._nodes += 1
        self._depth += 1
        try:
            if self._depth > MAX_YAML_DEPTH:
                raise yaml.YAMLError("manifest YAML nesting depth exceeds limit")
            if self._nodes > MAX_YAML_NODES:
                raise yaml.YAMLError("manifest YAML node count exceeds limit")
            return super().compose_node(parent, index)
        finally:
            self._depth -= 1

    def construct_mapping(self, node: Any, deep: bool = False) -> dict[Any, Any]:
        if not isinstance(node, yaml.MappingNode):
            return super().construct_mapping(node, deep=deep)
        keys: set[Any] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                if key in keys:
                    raise yaml.YAMLError(f"duplicate manifest key: {key!r}")
                keys.add(key)
            except TypeError as exc:
                raise yaml.YAMLError("manifest mapping keys must be scalar values") from exc
        return super().construct_mapping(node, deep=deep)


def _parse_manifest(data: bytes) -> dict[str, Any]:
    try:
        loader = _ManifestLoader(data.decode("utf-8"))
        try:
            manifest = loader.get_single_data()
        finally:
            loader.dispose()
    except (yaml.YAMLError, UnicodeError, ValueError, TypeError, KeyError,
            AttributeError, IndexError, OverflowError) as exc:
        # SafeLoader's explicit scalar constructors also raise ordinary Python
        # exceptions for malformed !!timestamp, !!int, !!bool and !!float tags.
        raise MDKVFormatError(f"invalid manifest YAML: {exc}") from exc
    if not isinstance(manifest, dict):
        raise MDKVFormatError("manifest is not a valid YAML mapping")
    return manifest


def _manifest_from_doc(doc: MDKVDocument) -> dict[str, Any]:
    """Create the manifest without coercing invalid mutable document fields."""
    if not isinstance(doc.created, datetime):
        raise ValidationError("document created must be a datetime")
    return {
        "title": doc.title,
        "authors": doc.authors,
        "created": doc.created.isoformat(),
        "version": doc.version,
        "metadata": doc.metadata,
        "tracks": [
            {
                "track_id": track.track_id,
                "track_type": track.track_type,
                "language": track.language,
                "path": track.path,
            }
            for track in doc.tracks.values()
        ],
    }


def _member_chunks(zf: zipfile.ZipFile, info: zipfile.ZipInfo, limit: int) -> Iterator[bytes]:
    """Bound raw deflate output before allocation, checking true size and CRC.

    ZipExtFile clamps output to the declared size, which can hide trailing
    uncompressed bytes. Use it only to validate local headers/overlap, never
    to decode. The standard ZIP local header then locates the compressed bytes.
    """
    if info.compress_type not in _SUPPORTED_COMPRESSION:
        raise MDKVFormatError(f"unsupported ZIP compression method: {info.compress_type}")
    if info.file_size > limit:
        raise MDKVFormatError(f"member '{info.filename}' exceeds uncompressed size limit")
    with zf.open(info):
        pass
    source = zf.fp
    if source is None:
        raise MDKVFormatError("cannot read a closed ZIP archive")
    source.seek(info.header_offset)
    header = source.read(30)
    if len(header) != 30 or header[:4] != b"PK\x03\x04":
        raise MDKVFormatError("invalid ZIP local header")
    name_size, extra_size = struct.unpack_from("<HH", header, 26)
    source.seek(name_size + extra_size, os.SEEK_CUR)
    remaining = info.compress_size
    decoder = zlib.decompressobj(-15) if info.compress_type == zipfile.ZIP_DEFLATED else None
    count = crc = 0
    while remaining:
        compressed = source.read(min(64 * 1024, remaining))
        if not compressed:
            raise MDKVFormatError("truncated compressed ZIP member")
        remaining -= len(compressed)
        pending = compressed
        while True:
            chunk = (decoder.decompress(pending, min(64 * 1024, min(limit, info.file_size) - count + 1))
                     if decoder is not None else pending)
            count += len(chunk)
            if count > limit or count > info.file_size:
                raise MDKVFormatError(f"member '{info.filename}' has invalid uncompressed size")
            crc = zlib.crc32(chunk, crc)
            if chunk:
                yield chunk
            pending = decoder.unconsumed_tail if decoder is not None else b""
            if decoder is not None and decoder.eof:
                if decoder.unused_data or pending or remaining:
                    raise MDKVFormatError(f"member '{info.filename}' has trailing compressed data")
                break
            if not pending and (not chunk or decoder is None):
                break
    if decoder is not None and not decoder.eof:
        raise MDKVFormatError(f"member '{info.filename}' has truncated deflate data")
    if count != info.file_size or crc != info.CRC:
        raise MDKVFormatError(f"member '{info.filename}' has invalid size or CRC")


def _read_member(zf: zipfile.ZipFile, name: str, limit: int) -> bytes:
    try:
        info = zf.getinfo(name)
    except KeyError as exc:
        raise MDKVFormatError(f"track file '{name}' not found in container") from exc
    return b"".join(_member_chunks(zf, info, limit))


def _doc_from_manifest(manifest: dict[str, Any], file_reader: zipfile.ZipFile) -> MDKVDocument:
    """Reconstruct metadata and referenced tracks from a validated ZIP handle."""
    if not isinstance(manifest, dict):
        raise MDKVFormatError("manifest is not a valid YAML mapping")
    for key in ("title", "created"):
        if key not in manifest or manifest[key] is None:
            raise MDKVFormatError(f"manifest missing required key: {key}")
    if isinstance(manifest.get("tracks"), list) and len(manifest["tracks"]) > MAX_TRACKS:
        raise MDKVFormatError("manifest track count exceeds limit")
    try:
        validated = MDKVManifestModel.model_validate(manifest)
    except ValueError as exc:
        raise MDKVFormatError(f"manifest schema validation failed: {exc}") from exc
    doc = MDKVDocument(
        title=validated.title,
        authors=list(validated.authors),
        created=validated.created,
        version=validated.version,
        metadata=dict(validated.metadata),
    )
    for entry in validated.tracks:
        content = _read_member(file_reader, entry.path, MAX_TRACK_BYTES).decode("utf-8")
        try:
            track = Track(
                track_id=entry.track_id,
                track_type=entry.track_type,
                language=entry.language,
                path=entry.path,
                content=content,
            )
        except ValueError as exc:
            raise MDKVFormatError(f"invalid track definition for '{entry.track_id}': {exc}") from exc
        doc.add_track(track)
    return doc


def _serialize_document(doc: MDKVDocument) -> tuple[bytes, list[tuple[str, bytes]]]:
    """Validate mutated fields and serialize all content before opening a temp file."""
    if not isinstance(doc, MDKVDocument) or not isinstance(doc.tracks, dict):
        raise ValidationError("document must contain a track mapping")
    if len(doc.tracks) > MAX_TRACKS:
        raise ValidationError("document track count exceeds limit")
    ids: set[str] = set()
    paths: dict[str, str] = {}
    tracks: list[tuple[str, bytes]] = []
    total = 0
    for key, track in doc.tracks.items():
        if not isinstance(track, Track):
            raise ValidationError("document tracks must be Track instances")
        try:
            Track.__post_init__(track)
            if track.track_id in ids:
                raise ValidationError(f"duplicate track_id: {track.track_id}")
            if key != track.track_id:
                raise ValidationError(f"track mapping key '{key}' does not match track_id '{track.track_id}'")
            if track.path in paths:
                raise ValidationError(
                    f"tracks '{paths[track.path]}' and '{track.track_id}' share path '{track.path}'"
                )
            content = track.content.encode("utf-8")
        except (ValueError, UnicodeError) as exc:
            raise ValidationError(f"invalid track definition: {exc}") from exc
        if len(content) > MAX_TRACK_BYTES:
            raise ValidationError(f"track '{track.track_id}' exceeds uncompressed size limit")
        ids.add(track.track_id)
        paths[track.path] = track.track_id
        total += len(content)
        if total > MAX_TOTAL_BYTES:
            raise ValidationError("document total uncompressed size exceeds limit")
        tracks.append((track.path, content))
    try:
        manifest = MDKVManifestModel.model_validate(_manifest_from_doc(doc))
        data = yaml.safe_dump(manifest.model_dump(mode="json"), sort_keys=False).encode("utf-8")
        if len(data) > MAX_MANIFEST_BYTES:
            raise ValidationError("manifest exceeds uncompressed size limit")
        # Enforce the same YAML complexity contract on our own serialized output.
        _parse_manifest(data)
    except (ValueError, TypeError, yaml.YAMLError, MDKVFormatError) as exc:
        raise ValidationError(f"invalid document manifest: {exc}") from exc
    if total + len(data) > MAX_TOTAL_BYTES:
        raise ValidationError("document total uncompressed size exceeds limit")
    return data, tracks


def save_mdkv(
    doc: MDKVDocument,
    output_path: Path,
    compression: int = zipfile.ZIP_DEFLATED,
    compresslevel: int | None = None,
) -> None:
    """Atomically replace a container after prevalidation and serialization.

    Creates parent directories as needed. Existing destination permissions are
    preserved. A unique same-directory temporary is removed on every failure;
    invalid in-memory documents raise ``ValidationError`` without changing the
    destination. ``compression`` supports stored/deflate only, matching the
    bounded reader; ``compresslevel`` is passed through to Python's ZIP writer.
    """
    manifest, tracks = _serialize_document(doc)
    if compression not in _SUPPORTED_COMPRESSION:
        raise ValueError(f"unsupported ZIP compression method: {compression}")
    if compresslevel is not None:
        if compression == zipfile.ZIP_DEFLATED and not -1 <= compresslevel <= 9:
            raise ValueError("deflate compresslevel must be between -1 and 9")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        mode = stat.S_IMODE(output_path.stat().st_mode)
    except FileNotFoundError:
        mode = None
    fd, name = tempfile.mkstemp(prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w+b") as stream:
            with zipfile.ZipFile(stream, mode="w", compression=compression, compresslevel=compresslevel) as zf:
                for path, content in tracks:
                    zf.writestr(path, content)
                zf.writestr(MANIFEST_NAME, manifest)
            if stream.tell() > MAX_ARCHIVE_BYTES:
                raise ValidationError("compressed archive size exceeds limit")
            if mode is not None:
                os.fchmod(stream.fileno(), mode)
        os.replace(temporary, output_path)
    finally:
        temporary.unlink(missing_ok=True)


def save_mdkv_incremental(doc: MDKVDocument, output_path: Path) -> bool:
    """Perform a validated full atomic rewrite using the existing public API.

    Returns ``True`` only if the destination was an existing valid container;
    returns ``False`` when a missing or invalid container required a full-save
    fallback. No ZIP append optimization or old-content cache is used.
    """
    output_path = Path(output_path)
    try:
        load_mdkv(output_path)
    except (FileNotFoundError, MDKVFormatError):
        existing_valid = False
    else:
        existing_valid = True
    save_mdkv(doc, output_path)
    return existing_valid


def _preflight_directory(source: Any, archive_size: int) -> None:
    """Count actual standard central records before ZipFile allocates ZipInfos.

    Only the bounded EOCD/comment window and one fixed central header are read
    at a time. Variable fields are skipped only after their lengths are checked
    against the directory boundary. Counts in the EOCD are consistency checks,
    never a substitute for walking records.
    """
    window_size = min(archive_size, 22 + 65535)
    source.seek(archive_size - window_size)
    tail = source.read(window_size)
    marker = tail.rfind(b"PK\x05\x06")
    if marker < 0 or len(tail) - marker < 22:
        raise MDKVFormatError("missing or truncated ZIP end record")
    end = struct.unpack_from("<4s4H2IH", tail, marker)
    _, disk, directory_disk, disk_count, declared_count, size, offset, comment_size = end
    end_offset = archive_size - window_size + marker
    if marker + 22 + comment_size != len(tail):
        raise MDKVFormatError("invalid ZIP comment length or trailing data")
    if disk or directory_disk or disk_count != declared_count:
        raise MDKVFormatError("multidisk ZIP archives are not supported")
    if declared_count == 0xFFFF or size == 0xFFFFFFFF or offset == 0xFFFFFFFF:
        raise MDKVFormatError("ZIP64 archives are not supported")
    # zipfile reads a ZIP64 locator from the 20 bytes immediately before this
    # EOCD and would replace the directory selected above with the locator's.
    locator = marker - 20
    if locator >= 0 and tail[locator:locator + 4] == b"PK\x06\x07":
        raise MDKVFormatError("ZIP64 archives are not supported")
    if offset + size != end_offset:
        raise MDKVFormatError("invalid ZIP central directory bounds")
    position = offset
    count = 0
    first_local_offset = offset
    while position < end_offset:
        if end_offset - position < 46:
            raise MDKVFormatError("truncated ZIP central directory header")
        source.seek(position)
        header = source.read(46)
        if len(header) != 46 or header[:4] != b"PK\x01\x02":
            raise MDKVFormatError("invalid ZIP central directory header")
        fields = struct.unpack("<4s6H3I5H2I", header)
        count += 1
        if count > MAX_MEMBERS:
            raise MDKVFormatError("archive member count exceeds limit")
        if fields[4] not in _SUPPORTED_COMPRESSION:
            raise MDKVFormatError(f"unsupported ZIP compression method: {fields[4]}")
        if fields[2] >= 45 or 0xFFFFFFFF in (fields[8], fields[9], fields[16]):
            raise MDKVFormatError("ZIP64 or extended ZIP versions are not supported")
        if fields[13]:
            raise MDKVFormatError("multidisk ZIP archives are not supported")
        next_position = position + 46 + fields[10] + fields[11] + fields[12]
        if next_position > end_offset or fields[16] + 30 > offset:
            raise MDKVFormatError("invalid ZIP central directory member bounds")
        first_local_offset = min(first_local_offset, fields[16])
        position = next_position
    if count != declared_count:
        raise MDKVFormatError("ZIP central directory member count mismatch")
    if first_local_offset != 0:
        raise MDKVFormatError("prepended ZIP data is not supported")
    source.seek(0)


def _validate_archive(zf: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    infos = zf.infolist()
    if len(infos) > MAX_MEMBERS:
        raise MDKVFormatError("archive member count exceeds limit")
    names: set[str] = set()
    total = 0
    for info in infos:
        if info.filename in names:
            raise MDKVFormatError(f"duplicate archive member: {info.filename}")
        names.add(info.filename)
        if info.orig_filename != info.filename:
            raise MDKVFormatError("archive member name contains NUL")
        if info.flag_bits & 1:
            raise MDKVFormatError(f"encrypted archive member is not supported: {info.filename}")
        if info.compress_type not in _SUPPORTED_COMPRESSION:
            raise MDKVFormatError(f"unsupported ZIP compression method: {info.compress_type}")
        total += info.file_size
        if total > MAX_TOTAL_BYTES:
            raise MDKVFormatError("archive total declared uncompressed size exceeds limit")
    if MANIFEST_NAME not in names:
        raise MDKVFormatError(f"manifest '{MANIFEST_NAME}' not found in container")
    return infos


def _check_unreferenced(zf: zipfile.ZipFile, infos: list[zipfile.ZipInfo], referenced: set[str]) -> None:
    """Check CRC/decompression of extra members without caching their content."""
    for info in infos:
        if info.filename in referenced:
            continue
        for _ in _member_chunks(zf, info, MAX_TOTAL_BYTES):
            pass


def load_mdkv(input_path: Path) -> MDKVDocument:
    """Load a bounded container without extracting any archive members.

    Corrupt ZIP, UTF-8, YAML, schema, CRC and decompression errors become
    ``MDKVFormatError``. Missing files still raise ``FileNotFoundError``.
    """
    path = Path(input_path)
    with path.open("rb") as source:
        archive_size = os.fstat(source.fileno()).st_size
        if archive_size > MAX_ARCHIVE_BYTES:
            raise MDKVFormatError("compressed archive size exceeds limit")
        try:
            _preflight_directory(source, archive_size)
            with zipfile.ZipFile(source, mode="r") as zf:
                infos = _validate_archive(zf)
                manifest = _parse_manifest(_read_member(zf, MANIFEST_NAME, MAX_MANIFEST_BYTES))
                doc = _doc_from_manifest(manifest, zf)
                referenced = {MANIFEST_NAME, *(track.path for track in doc.tracks.values())}
                _check_unreferenced(zf, infos, referenced)
                return doc
        except MDKVFormatError:
            raise
        except (zipfile.BadZipFile, zipfile.LargeZipFile, UnicodeError, yaml.YAMLError,
                ValueError, TypeError, RuntimeError, NotImplementedError, EOFError,
                OSError, zlib.error) as exc:
            raise MDKVFormatError(f"invalid MDKV container '{path}': {exc}") from exc
