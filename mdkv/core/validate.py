from __future__ import annotations

"""Validation helpers for MDKV documents.

Validates required fields, track invariants, and content integrity.
Returns a list of issues and raises ``ValidationError`` if any ERROR-level
issues exist.  WARN-level issues are returned but never raised.
"""

import re
from dataclasses import dataclass

from mdkv.core.model import MDKVDocument, Track

from .errors import ValidationError
from .registry import get_registry

# Semver-like pattern: MAJOR.MINOR or MAJOR.MINOR.PATCH with optional pre-release
_VERSION_RE = re.compile(r"^\d+\.\d+(?:\.\d+)?(?:[-+].+)?$")

# Track IDs that could confuse the GUI or CLI
_RESERVED_TRACK_IDS = frozenset({"all", "none", "null", "true", "false", ""})


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


def validate_document(doc: MDKVDocument) -> list[ValidationIssue]:
    """Validate required fields, track invariants, and content.

    Returns a list of ``ValidationIssue`` objects.  Raises ``ValidationError``
    if any ERROR-level issues are found.
    """
    issues: list[ValidationIssue] = []

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
    seen_ids: set[str] = set()
    for tid, track in doc.tracks.items():
        try:
            track_issues = validate_track(track)
        except ValidationError as exc:
            issues.append(ValidationIssue("ERROR", str(exc), track_id=tid))
            continue
        issues.extend(track_issues)
        if tid != track.track_id:
            issues.append(ValidationIssue("ERROR", "track mapping key does not match track_id", track_id=tid))
        if track.track_id in seen_ids:
            issues.append(ValidationIssue("ERROR", f"duplicate track_id: {track.track_id}", track_id=tid))
        seen_ids.add(track.track_id)
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


def validate_track(track: Track) -> list[ValidationIssue]:
    """Validate a single ``Track`` in isolation.

    Returns a list of ``ValidationIssue`` objects.  Raises ``ValidationError``
    if any ERROR-level issues are found.
    """
    if not isinstance(track, Track):
        raise ValidationError("track must be an instance of Track")
    try:
        Track.__post_init__(track)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    issues: list[ValidationIssue] = []
    tid = track.track_id

    # Reserved track_id
    if tid.lower() in _RESERVED_TRACK_IDS:
        issues.append(
            ValidationIssue("WARN", f"track_id '{tid}' is a reserved word and may cause issues", track_id=tid)
        )

    # Empty content
    if not track.content.strip():
        issues.append(
            ValidationIssue("WARN", f"track '{tid}' has empty content", track_id=tid)
        )

    # Code track without fences
    if track.track_type == "code" and "```" not in track.content:
        issues.append(
            ValidationIssue("WARN", f"code track '{tid}' contains no fenced code blocks", track_id=tid)
        )

    # Translation without language
    if track.track_type == "translation" and not track.language:
        issues.append(
            ValidationIssue("WARN", f"translation track '{tid}' has no language set", track_id=tid)
        )

    registry = get_registry()
    for message in registry.validate(track.track_type, track.content):
        issues.append(ValidationIssue("WARN", message, track_id=tid))
    for message in registry.check_heuristics(track.track_type, track.content):
        issues.append(ValidationIssue("WARN", message, track_id=tid))

    return issues
