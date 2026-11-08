from __future__ import annotations

"""Core data model for MDKV.

Defines track types and the `Track` and `MDKVDocument` classes used across the
library, plus small management helpers.

Invariants:
- `Track.track_type` must be one of the allowed types returned by
  `allowed_track_types()`.
- `Track.path` must live under the `tracks/` directory.
- An `MDKVDocument` maps unique `track_id` values to `Track` instances.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .errors import ValidationError
from .registry import get_registry


def allowed_track_types() -> list[str]:
    """Return the list of supported track type identifiers.

    Order is informational only; callers should not rely on ordering.
    """
    return get_registry().all_types()


def validate_track_id(track_id: str) -> str:
    """Require a nonempty textual identifier without control characters."""
    if not isinstance(track_id, str) or not track_id.strip():
        raise ValueError("track_id must not be empty")
    if any(ord(char) < 32 or ord(char) == 127 for char in track_id):
        raise ValueError("track_id must not contain control characters")
    return track_id


def validate_track_path(path: str) -> str:
    """Require a safe relative file path below ``tracks/``; never normalize it."""
    if not isinstance(path, str) or not path.startswith("tracks/"):
        raise ValueError("track path must be under 'tracks/' directory")
    if "\\" in path or "\x00" in path or any(
        part in {"", ".", ".."} for part in path.split("/")
    ):
        raise ValueError("track path must be a safe relative path under 'tracks/'")
    return path


@dataclass
class Track:
    """A single Markdown content track within a document.

    Fields:
    - `track_id`: unique identifier within the document
    - `track_type`: one of `allowed_track_types()`
    - `language`: ISO 639-1/BCP-47 code or None for non-linguistic tracks
    - `path`: safe relative file path below `tracks/`
    - `content`: UTF-8 Markdown text
    """
    track_id: str
    track_type: str
    language: str | None
    path: str
    content: str

    def __post_init__(self) -> None:
        if not isinstance(self.track_type, str) or not get_registry().is_registered(self.track_type):
            raise ValueError(f"Unsupported track_type: {self.track_type}")
        validate_track_id(self.track_id)
        validate_track_path(self.path)
        if self.language is not None and not isinstance(self.language, str):
            raise ValueError("track language must be a string or None")
        if not isinstance(self.content, str):
            raise ValueError("track content must be a string")

    def __repr__(self) -> str:
        return (
            f"Track(track_id={self.track_id!r}, track_type={self.track_type!r}, "
            f"language={self.language!r}, path={self.path!r}, content=<{len(self.content)} chars>)"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Track):
            return NotImplemented
        return (
            self.track_id == other.track_id
            and self.track_type == other.track_type
            and self.language == other.language
            and self.path == other.path
            and self.content == other.content
        )

    def __hash__(self) -> int:
        return hash((self.track_id, self.track_type, self.path))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for JSON/YAML emission."""
        return {
            "track_id": self.track_id,
            "track_type": self.track_type,
            "language": self.language,
            "path": self.path,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Track:
        """Reconstruct a Track from a plain dict (inverse of ``to_dict``)."""
        return cls(
            track_id=data["track_id"],
            track_type=data["track_type"],
            language=data.get("language"),
            path=data["path"],
            content=data.get("content", ""),
        )


@dataclass
class MDKVDocument:
    """In-memory representation of a `.mdkv` document.

    Includes metadata and a mapping of `track_id` → `Track`.
    ``TrackHistory`` is a separate in-memory API: document mutations and
    container saves do not automatically record or persist revision history.
    """
    title: str
    authors: list[str]
    created: datetime
    version: str = "0.1"
    tracks: dict[str, Track] = field(default_factory=dict)
    metadata: dict[str, str] = field(default_factory=dict)

    def add_track(self, track: Track) -> None:
        """Add a new `track`.

        Raises `ValidationError` if `track_id` already exists.
        """
        if track.track_id in self.tracks:
            raise ValidationError(f"duplicate track_id: {track.track_id}")
        self.tracks[track.track_id] = track

    def get_track(self, track_id: str) -> Track | None:
        """Return track by id or None if missing."""
        return self.tracks.get(track_id)

    def remove_track(self, track_id: str) -> Track:
        """Remove and return a track by id.

        Raises `KeyError` if missing.
        """
        if track_id not in self.tracks:
            raise KeyError(track_id)
        return self.tracks.pop(track_id)

    def list_languages(self) -> list[str]:
        """Return sorted list of languages present across tracks (excluding None)."""
        langs = {t.language for t in self.tracks.values() if t.language}
        return sorted(langs)

    @property
    def track_ids(self) -> list[str]:
        """Return the list of track IDs in insertion order."""
        return list(self.tracks.keys())

    # management helpers
    def find_tracks_by_type(self, track_type: str) -> list[Track]:
        """Return all tracks with the given `track_type`."""
        return [t for t in self.tracks.values() if t.track_type == track_type]

    def count_tracks_by_type(self) -> dict[str, int]:
        """Return a mapping of ``track_type`` → count across all tracks."""
        counts: dict[str, int] = {}
        for track in self.tracks.values():
            counts[track.track_type] = counts.get(track.track_type, 0) + 1
        return counts

    def update_track_content(self, track_id: str, new_content: str) -> None:
        """Replace the Markdown `content` of the track `track_id`.

        Raises `KeyError` if missing.
        """
        track = self.get_track(track_id)
        if track is None:
            raise KeyError(track_id)
        track.content = new_content

    def rename_track(self, old_id: str, new_id: str) -> None:
        """Rename `old_id` to `new_id` and adjust its path if it targets a `.md` file.

        Preserves insertion order. Invalid IDs or colliding paths raise
        ``ValueError`` before changing the document; missing IDs raise ``KeyError``.
        """
        validate_track_id(new_id)
        track = self.get_track(old_id)
        if track is None:
            raise KeyError(old_id)
        if old_id == new_id:
            return
        if new_id in self.tracks:
            raise ValueError(f"track id exists: {new_id}")
        new_path = f"tracks/{new_id}.md" if track.path.endswith(".md") else track.path
        validate_track_path(new_path)
        if any(t is not track and t.path == new_path for t in self.tracks.values()):
            raise ValueError(f"track path exists: {new_path}")
        renamed_tracks = {
            new_id if tid == old_id else tid: value for tid, value in self.tracks.items()
        }
        track.track_id = new_id
        track.path = new_path
        self.tracks = renamed_tracks

    def move_track(self, track_id: str, after_id: str | None) -> None:
        """Reorder ``track_id`` to appear immediately after ``after_id`` in the track ordering.

        If ``after_id`` is ``None``, move ``track_id`` to the first position.
        Raises ``KeyError`` if ``track_id`` is missing, or if ``after_id`` is
        provided but not found.
        """
        if track_id not in self.tracks:
            raise KeyError(track_id)
        if after_id is not None and after_id not in self.tracks:
            raise KeyError(after_id)
        if track_id == after_id:
            return
        # Rebuild the dict in the new order
        track = self.tracks.pop(track_id)
        new_tracks: dict[str, Track] = {}
        if after_id is None:
            new_tracks[track_id] = track
            new_tracks.update(self.tracks)
        else:
            for tid, t in self.tracks.items():
                new_tracks[tid] = t
                if tid == after_id:
                    new_tracks[track_id] = track
        self.tracks = new_tracks

    # metadata helpers
    def set_metadata(self, key: str, value: str) -> None:
        """Set or replace a metadata key/value pair."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: str | None = None) -> str | None:
        """Get a metadata value or `default` if missing."""
        return self.metadata.get(key, default)

    def remove_metadata(self, key: str) -> None:
        """Remove a metadata key if present."""
        self.metadata.pop(key, None)

    # serialization helpers
    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for JSON/YAML emission.

        Track content is included inline (unlike the storage manifest which
        stores tracks as separate files).
        """
        return {
            "title": self.title,
            "authors": list(self.authors),
            "created": self.created.isoformat(),
            "version": self.version,
            "metadata": dict(self.metadata),
            "tracks": [t.to_dict() for t in self.tracks.values()],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MDKVDocument:
        """Reconstruct an MDKVDocument from a plain dict (inverse of ``to_dict``).

        Raises ``KeyError`` if required keys (title, created) are missing.
        Raises ``ValidationError`` if track IDs collide.
        """
        created = data["created"]
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        doc = cls(
            title=data["title"],
            authors=list(data.get("authors", [])),
            created=created,
            version=data.get("version", "0.1"),
        )
        doc.metadata.update(data.get("metadata", {}))
        for track_data in data.get("tracks", []):
            track = Track.from_dict(track_data)
            doc.add_track(track)
        return doc

    def __repr__(self) -> str:
        return (
            f"MDKVDocument(title={self.title!r}, authors={self.authors!r}, "
            f"version={self.version!r}, tracks={len(self.tracks)}, metadata={len(self.metadata)})"
        )
