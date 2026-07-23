"""Track versioning subsystem for MDKV.

Stores content revision history per track_id, enabling undo/restore
and revision-track integration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


@dataclass
class TrackVersion:
    """A single version snapshot of a track's content."""

    timestamp: datetime
    content: str
    track_type: str
    language: Optional[str]
    track_id: str


@dataclass
class TrackHistory:
    """Revision history for a single track.

    Stores ordered list of (timestamp, content) tuples.
    The most recent entry is the current content.
    """

    track_id: str
    versions: List[TrackVersion] = field(default_factory=list)

    def add_version(self, content: str, track_type: str, language: Optional[str],
                    timestamp: Optional[datetime] = None) -> None:
        """Record a new version of the track content."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        self.versions.append(TrackVersion(
            timestamp=timestamp,
            content=content,
            track_type=track_type,
            language=language,
            track_id=self.track_id,
        ))

    def get_current(self) -> Optional[TrackVersion]:
        """Return the most recent version, or None if empty."""
        if not self.versions:
            return None
        return self.versions[-1]

    def get_version_at(self, timestamp: datetime) -> Optional[TrackVersion]:
        """Return the version that was current at the given timestamp."""
        result = None
        for v in self.versions:
            if v.timestamp <= timestamp:
                result = v
            else:
                break
        return result

    def list_versions(self) -> List[TrackVersion]:
        """Return all versions in chronological order."""
        return list(self.versions)

    def restore_to(self, timestamp: datetime) -> Optional[TrackVersion]:
        """Truncate history to the version at the given timestamp.

        Returns the restored version, or None if no version matches.
        """
        target = self.get_version_at(timestamp)
        if target is None:
            return None
        # Keep only versions up to and including the target
        idx = self.versions.index(target)
        self.versions = self.versions[: idx + 1]
        return target

    def to_dict(self) -> dict:
        """Serialize to a plain dict."""
        return {
            "track_id": self.track_id,
            "versions": [
                {
                    "timestamp": v.timestamp.isoformat(),
                    "content": v.content,
                    "track_type": v.track_type,
                    "language": v.language,
                }
                for v in self.versions
            ],
        }
