from __future__ import annotations

"""Diff utilities for MDKV documents.

Compares two documents and reports differences in title, authors, version,
tracks (added/removed/modified), and metadata (added/removed/changed).
"""

from dataclasses import dataclass, field
from typing import Any

from mdkv.core.model import MDKVDocument


@dataclass
class DiffResult:
    """Structured result of comparing two MDKV documents.

    All list fields are empty when the documents are identical.
    """

    title_changed: list[str] = field(default_factory=list)
    authors_changed: list[Any] = field(default_factory=list)
    version_changed: list[str] = field(default_factory=list)
    tracks_added: list[str] = field(default_factory=list)
    tracks_removed: list[str] = field(default_factory=list)
    tracks_modified: list[str] = field(default_factory=list)
    metadata_added: list[str] = field(default_factory=list)
    metadata_removed: list[str] = field(default_factory=list)
    metadata_changed: list[dict[str, str]] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Return True if any differences were found."""
        return any(
            len(getattr(self, f)) > 0
            for f in (
                "title_changed", "authors_changed", "version_changed",
                "tracks_added", "tracks_removed", "tracks_modified",
                "metadata_added", "metadata_removed", "metadata_changed",
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for JSON."""
        return {
            "title_changed": self.title_changed,
            "authors_changed": self.authors_changed,
            "version_changed": self.version_changed,
            "tracks_added": self.tracks_added,
            "tracks_removed": self.tracks_removed,
            "tracks_modified": self.tracks_modified,
            "metadata_added": self.metadata_added,
            "metadata_removed": self.metadata_removed,
            "metadata_changed": self.metadata_changed,
        }


def diff_documents(doc_a: MDKVDocument, doc_b: MDKVDocument) -> DiffResult:
    """Compare two documents and return a ``DiffResult``.

    A track is considered "modified" if its content, type, language, or path
    differs between the two documents.
    """
    result = DiffResult()

    # Document-level
    if doc_a.title != doc_b.title:
        result.title_changed = [doc_a.title, doc_b.title]
    if doc_a.authors != doc_b.authors:
        result.authors_changed = [doc_a.authors, doc_b.authors]
    if doc_a.version != doc_b.version:
        result.version_changed = [doc_a.version, doc_b.version]

    # Tracks
    ids_a = set(doc_a.tracks)
    ids_b = set(doc_b.tracks)
    result.tracks_added = sorted(ids_b - ids_a)
    result.tracks_removed = sorted(ids_a - ids_b)
    for tid in sorted(ids_a & ids_b):
        ta, tb = doc_a.tracks[tid], doc_b.tracks[tid]
        if (ta.content != tb.content
                or ta.track_type != tb.track_type
                or ta.language != tb.language
                or ta.path != tb.path):
            result.tracks_modified.append(tid)

    # Metadata
    meta_a, meta_b = doc_a.metadata, doc_b.metadata
    result.metadata_added = sorted(set(meta_b) - set(meta_a))
    result.metadata_removed = sorted(set(meta_a) - set(meta_b))
    for k in sorted(set(meta_a) & set(meta_b)):
        if meta_a[k] != meta_b[k]:
            result.metadata_changed.append({"key": k, "from": meta_a[k], "to": meta_b[k]})

    return result
