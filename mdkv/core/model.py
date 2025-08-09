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
from typing import Dict, List, Optional

from .errors import ValidationError


def allowed_track_types() -> List[str]:
    """Return the list of supported track type identifiers.

    Order is informational only; callers should not rely on ordering.
    """
    return [
        "primary",
        "translation",
        "commentary",
        "code",
        "reference",
        "media_ref",
        "revision",
    ]


@dataclass
class Track:
    """A single Markdown content track within a document.

    Fields:
    - `track_id`: unique identifier within the document
    - `track_type`: one of `allowed_track_types()`
    - `language`: ISO 639-1/BCP-47 code or None for non-linguistic tracks
    - `path`: path inside the container (must start with `tracks/`)
    - `content`: UTF-8 Markdown text
    """
    track_id: str
    track_type: str
    language: Optional[str]
    path: str
    content: str

    def __post_init__(self) -> None:
        if self.track_type not in allowed_track_types():
            raise ValueError(f"Unsupported track_type: {self.track_type}")
        if not self.track_id:
            raise ValueError("track_id must not be empty")
        if not self.path.startswith("tracks/"):
            raise ValueError("track path must be under 'tracks/' directory")


@dataclass
class MDKVDocument:
    """In-memory representation of a `.mdkv` document.

    Includes metadata and a mapping of `track_id` → `Track`.
    """
    title: str
    authors: List[str]
    created: datetime
    version: str = "0.1"
    tracks: Dict[str, Track] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)

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

    def list_languages(self) -> List[str]:
        """Return sorted list of languages present across tracks (excluding None)."""
        langs = {t.language for t in self.tracks.values() if t.language}
        return sorted(langs)

    # management helpers
    def find_tracks_by_type(self, track_type: str) -> List[Track]:
        """Return all tracks with the given `track_type`."""
        return [t for t in self.tracks.values() if t.track_type == track_type]

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

        Raises `ValueError` if `new_id` exists or `KeyError` if `old_id` missing.
        """
        if new_id in self.tracks:
            raise ValueError(f"track id exists: {new_id}")
        track = self.get_track(old_id)
        if track is None:
            raise KeyError(old_id)
        # update mapping and track path
        self.tracks.pop(old_id)
        track.track_id = new_id
        if track.path.startswith("tracks/") and track.path.endswith(".md"):
            track.path = f"tracks/{new_id}.md"
        self.tracks[new_id] = track

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


