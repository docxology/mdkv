"""Standalone, in-memory track revision history.

Document mutations do not automatically record versions, and MDKV container
saves do not persist ``TrackHistory`` instances. Use ``to_dict`` explicitly when
an application needs to serialize this separate history API.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class TrackVersion:
    """A single version snapshot of a track's content."""

    timestamp: datetime
    content: str
    track_type: str
    language: str | None
    track_id: str


@dataclass
class TrackHistory:
    """Chronological revision history, separate from document persistence.

    Equal timestamps preserve ingestion order. Naive and timezone-aware times
    cannot be mixed: ingestion and queries reject them before mutating history.
    """

    track_id: str
    versions: list[TrackVersion] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.versions = self._ordered_versions()

    def _ordered_versions(self) -> list[TrackVersion]:
        if any(not isinstance(version.timestamp, datetime) for version in self.versions):
            raise ValueError("history timestamps must be datetime instances")
        try:
            return sorted(self.versions, key=lambda version: version.timestamp)
        except TypeError as exc:
            raise ValueError("history timestamps must have comparable timezones") from exc

    @staticmethod
    def _version_at(versions: list[TrackVersion], timestamp: datetime) -> TrackVersion | None:
        if not isinstance(timestamp, datetime):
            raise ValueError("history timestamps must be datetime instances")
        result = None
        try:
            for version in versions:
                if version.timestamp <= timestamp:
                    result = version
                else:
                    break
        except TypeError as exc:
            raise ValueError("history timestamps must have comparable timezones") from exc
        return result

    def add_version(self, content: str, track_type: str, language: str | None,
                    timestamp: datetime | None = None) -> None:
        """Record a version chronologically without partially changing history.

        An omitted timestamp uses UTC for empty/aware histories and local naive
        time for an existing naive history, keeping the existing time convention.
        """
        ordered = self._ordered_versions()
        if timestamp is None:
            timestamp = datetime.now(UTC)
            if ordered and ordered[0].timestamp.utcoffset() is None:
                timestamp = datetime.now()
        if not isinstance(timestamp, datetime):
            raise ValueError("history timestamps must be datetime instances")
        candidate = TrackVersion(timestamp, content, track_type, language, self.track_id)
        try:
            updated = sorted([*ordered, candidate], key=lambda version: version.timestamp)
        except TypeError as exc:
            raise ValueError("history timestamps must have comparable timezones") from exc
        self.versions = updated

    def get_current(self) -> TrackVersion | None:
        """Return the chronologically most recent version, or None if empty."""
        ordered = self._ordered_versions()
        return ordered[-1] if ordered else None

    def get_version_at(self, timestamp: datetime) -> TrackVersion | None:
        """Return the latest version at or before a comparable timestamp."""
        return self._version_at(self._ordered_versions(), timestamp)

    def list_versions(self) -> list[TrackVersion]:
        """Return a chronological copy, including externally reordered versions."""
        return self._ordered_versions()

    def restore_to(self, timestamp: datetime) -> TrackVersion | None:
        """Keep versions up to the requested time; invalid queries change nothing."""
        ordered = self._ordered_versions()
        target = self._version_at(ordered, timestamp)
        if target is None:
            return None
        # Keep every equal-timestamp ingestion, even a repeated snapshot object.
        index = max(i for i, version in enumerate(ordered) if version is target)
        self.versions = ordered[:index + 1]
        return target

    def to_dict(self) -> dict[str, Any]:
        """Serialize this standalone history in chronological order."""
        return {
            "track_id": self.track_id,
            "versions": [
                {
                    "timestamp": version.timestamp.isoformat(),
                    "content": version.content,
                    "track_type": version.track_type,
                    "language": version.language,
                }
                for version in self.list_versions()
            ],
        }
