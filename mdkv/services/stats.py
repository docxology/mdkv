from __future__ import annotations

"""Statistics utilities for MDKV documents."""

from dataclasses import dataclass, field
from typing import Any

from mdkv.core.model import MDKVDocument


@dataclass
class DocumentStats:
    """Aggregated statistics about an MDKV document."""

    title: str
    version: str
    track_count: int
    tracks_by_type: dict[str, int] = field(default_factory=dict)
    languages: list[str] = field(default_factory=list)
    metadata_keys: list[str] = field(default_factory=list)
    total_characters: int = 0
    total_lines: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for JSON."""
        return {
            "title": self.title,
            "version": self.version,
            "track_count": self.track_count,
            "tracks_by_type": self.tracks_by_type,
            "languages": self.languages,
            "metadata_keys": self.metadata_keys,
            "total_characters": self.total_characters,
            "total_lines": self.total_lines,
        }


def compute_stats(doc: MDKVDocument) -> DocumentStats:
    """Compute statistics about an MDKV document."""
    total_chars = sum(len(t.content) for t in doc.tracks.values())
    total_lines = sum(t.content.count("\n") + 1 for t in doc.tracks.values())
    return DocumentStats(
        title=doc.title,
        version=doc.version,
        track_count=len(doc.tracks),
        tracks_by_type=doc.count_tracks_by_type(),
        languages=doc.list_languages(),
        metadata_keys=sorted(doc.metadata),
        total_characters=total_chars,
        total_lines=total_lines,
    )
