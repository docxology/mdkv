from __future__ import annotations

"""Pydantic schema definitions for MDKV manifest and JSON representations."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from mdkv.core.model import validate_track_id, validate_track_path


class TrackManifestModel(BaseModel):
    """Schema for a single track entry in manifest.yaml."""

    track_id: str = Field(..., min_length=1, description="Unique track identifier")
    track_type: str = Field(..., min_length=1, description="Track type identifier")
    path: str = Field(..., min_length=1, description="Path within container")
    language: str | None = Field(default=None, description="ISO language code")

    @field_validator("track_id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return validate_track_id(value)

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return validate_track_path(value)


class MDKVManifestModel(BaseModel):
    """Schema for manifest.yaml in .mdkv ZIP container.

    Legacy scalar author/metadata forms are normalized without coercing nested
    collections or arbitrary Python objects into misleading string metadata.
    """

    title: str = Field(default="", description="Document title")
    authors: list[str] = Field(default_factory=list, description="List of author names")
    created: datetime = Field(..., description="Document creation timestamp")
    version: str = Field(default="0.1", description="Document format/content version")
    metadata: dict[str, str] = Field(default_factory=dict, description="Custom string key-value metadata")
    tracks: list[TrackManifestModel] = Field(default_factory=list, description="Indexed tracks")

    @field_validator("authors", mode="before")
    @classmethod
    def ensure_authors_list(cls, value: Any) -> Any:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if not isinstance(value, (list, tuple)):
            raise ValueError("authors must be a string or a list of strings")
        return value

    @field_validator("metadata", mode="before")
    @classmethod
    def ensure_metadata_dict(cls, value: Any) -> dict[str, str]:
        if value is None:
            return {}

        def scalar_text(item: Any) -> str:
            if item is not None and not isinstance(item, (str, int, float, bool, date)):
                raise ValueError("metadata keys and values must be scalar values")
            return str(item)

        if not isinstance(value, dict):
            return {scalar_text(value): ""}
        normalized: dict[str, str] = {}
        for key, item in value.items():
            text_key = scalar_text(key)
            if text_key in normalized:
                raise ValueError(f"duplicate metadata key after normalization: {text_key}")
            normalized[text_key] = scalar_text(item)
        return normalized

    @field_validator("tracks")
    @classmethod
    def ensure_unique_tracks(cls, tracks: list[TrackManifestModel]) -> list[TrackManifestModel]:
        ids: set[str] = set()
        paths: set[str] = set()
        for track in tracks:
            if track.track_id in ids:
                raise ValueError(f"duplicate track_id: {track.track_id}")
            if track.path in paths:
                raise ValueError(f"tracks share path '{track.path}'")
            ids.add(track.track_id)
            paths.add(track.path)
        return tracks
