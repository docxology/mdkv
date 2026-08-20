from __future__ import annotations

"""Pydantic schema definitions for MDKV manifest and JSON representations."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class TrackManifestModel(BaseModel):
    """Schema for a single track entry in manifest.yaml."""

    track_id: str = Field(..., min_length=1, description="Unique track identifier")
    track_type: str = Field(..., min_length=1, description="Track type identifier")
    path: str = Field(..., min_length=1, description="Path within container")
    language: str | None = Field(default=None, description="ISO language code")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v.startswith("tracks/"):
            raise ValueError("track path must be under 'tracks/' directory")
        return v


class MDKVManifestModel(BaseModel):
    """Schema for manifest.yaml in .mdkv ZIP container."""

    title: str = Field(default="", description="Document title")
    authors: list[str] = Field(default_factory=list, description="List of author names")
    created: datetime = Field(..., description="Document creation timestamp")
    version: str = Field(default="0.1", description="Document format/content version")
    metadata: dict[str, str] = Field(default_factory=dict, description="Custom string key-value metadata")
    tracks: list[TrackManifestModel] = Field(default_factory=list, description="Indexed tracks")

    @field_validator("authors", mode="before")
    @classmethod
    def ensure_authors_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)

    @field_validator("metadata", mode="before")
    @classmethod
    def ensure_metadata_dict(cls, v: Any) -> dict[str, str]:
        if v is None:
            return {}
        if isinstance(v, dict):
            return {str(k): str(val) for k, val in v.items()}
        return {str(v): ""}
