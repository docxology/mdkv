from __future__ import annotations

"""Validation helpers for MDKV documents."""

from dataclasses import dataclass
from typing import List

from .errors import ValidationError


@dataclass
class ValidationIssue:
    level: str  # ERROR/WARN
    message: str


def validate_document(doc) -> List[ValidationIssue]:
    """Validate required fields and presence of a primary track.

    Returns a list of issues and raises `ValidationError` if any ERRORs exist.
    """
    issues: List[ValidationIssue] = []
    if not doc.title:
        issues.append(ValidationIssue("ERROR", "title is required"))
    if not doc.authors:
        issues.append(ValidationIssue("ERROR", "at least one author is required"))
    if "primary" not in doc.tracks:
        issues.append(ValidationIssue("ERROR", "primary track is required"))
    # fail on any ERROR
    errors = [i for i in issues if i.level == "ERROR"]
    if errors:
        raise ValidationError(
            "; ".join(i.message for i in errors)
        )
    return issues


