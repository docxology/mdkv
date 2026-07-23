from __future__ import annotations

"""Validation helpers for MDKV documents.

Validates required fields, track invariants, and content integrity.
Returns a list of issues and raises ``ValidationError`` if any ERROR-level
issues exist.  WARN-level issues are returned but never raised.
"""

import re
from dataclasses import dataclass
from typing import List

from .errors import ValidationError


# Semver-like pattern: MAJOR.MINOR or MAJOR.MINOR.PATCH with optional pre-release
_VERSION_RE = re.compile(r"^\d+\.\d+(?:\.\d+)?(?:[-+].+)?$")


@dataclass
class ValidationIssue:
    """A single validation finding.

    Fields:
    - ``level``: ``"ERROR"`` or ``"WARN"``
    - ``message``: human-readable description
    - ``track_id``: track involved, or ``None`` for document-level issues
    """

    level: str  # ERROR/WARN
    message: str
    track_id: str | None = None


def validate_document(doc) -> List[ValidationIssue]:
    """Validate required fields, track invariants, and content.

    Returns a list of ``ValidationIssue`` objects.  Raises ``ValidationError``
    if any ERROR-level issues are found.
    """
    issues: List[ValidationIssue] = []

    # --- Document-level checks ---
    if not doc.title:
        issues.append(ValidationIssue("ERROR", "title is required"))
    if not doc.authors:
        issues.append(ValidationIssue("ERROR", "at least one author is required"))

    # Primary track requirement
    has_primary = any(t.track_type == "primary" for t in doc.tracks.values())
    if not has_primary:
        issues.append(ValidationIssue("ERROR", "primary track is required"))

    # Version format (warn only — don't block on non-strict semver)
    if doc.version and not _VERSION_RE.match(doc.version):
        issues.append(
            ValidationIssue("WARN", f"version '{doc.version}' does not follow semver (MAJOR.MINOR[.PATCH])")
        )

    # --- Track-level checks ---
    seen_paths: dict[str, str] = {}  # path → track_id
    for tid, track in doc.tracks.items():
        # Path uniqueness
        if track.path in seen_paths:
            issues.append(
                ValidationIssue(
                    "ERROR",
                    f"track '{tid}' shares path '{track.path}' with track '{seen_paths[track.path]}'",
                    track_id=tid,
                )
            )
        else:
            seen_paths[track.path] = tid

        # Empty content warning
        if not track.content.strip():
            issues.append(
                ValidationIssue("WARN", f"track '{tid}' has empty content", track_id=tid)
            )

        # Track type-specific content heuristics
        if track.track_type == "code" and "```" not in track.content:
            issues.append(
                ValidationIssue("WARN", f"code track '{tid}' contains no fenced code blocks", track_id=tid)
            )

        # Language should be set for translation tracks
        if track.track_type == "translation" and not track.language:
            issues.append(
                ValidationIssue("WARN", f"translation track '{tid}' has no language set", track_id=tid)
            )

    # Multiple primary tracks warning
    primary_count = sum(1 for t in doc.tracks.values() if t.track_type == "primary")
    if primary_count > 1:
        issues.append(
            ValidationIssue("WARN", f"{primary_count} primary tracks found (expected 1)")
        )

    # Fail on any ERROR
    errors = [i for i in issues if i.level == "ERROR"]
    if errors:
        raise ValidationError("; ".join(i.message for i in errors))
    return issues
