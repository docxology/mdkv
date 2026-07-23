"""Tests for MDKVDocument and Track serialization, repr, and count methods."""
from datetime import datetime, timezone

import json

from mdkv.core.model import MDKVDocument, Track


def _doc() -> MDKVDocument:
    d = MDKVDocument(title="T", authors=["A", "B"], created=datetime(2025, 1, 1), version="1.0.0")
    d.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Primary\n\nHello"))
    d.add_track(Track("notes", "commentary", None, "tracks/notes.md", "Note"))
    d.add_track(Track("fr", "translation", "fr", "tracks/fr.md", "Bonjour"))
    d.set_metadata("project", "test")
    return d


def test_track_to_dict():
    t = Track("primary", "primary", "en", "tracks/primary.md", "content")
    d = t.to_dict()
    assert d["track_id"] == "primary"
    assert d["track_type"] == "primary"
    assert d["language"] == "en"
    assert d["path"] == "tracks/primary.md"
    assert d["content"] == "content"


def test_track_from_dict():
    data = {"track_id": "t1", "track_type": "commentary", "language": "en", "path": "tracks/t1.md", "content": "hi"}
    t = Track.from_dict(data)
    assert t.track_id == "t1"
    assert t.track_type == "commentary"
    assert t.content == "hi"


def test_track_to_from_dict_roundtrip():
    t = Track("primary", "primary", "en", "tracks/primary.md", "content")
    restored = Track.from_dict(t.to_dict())
    assert restored.track_id == t.track_id
    assert restored.track_type == t.track_type
    assert restored.language == t.language
    assert restored.path == t.path
    assert restored.content == t.content


def test_document_to_dict():
    doc = _doc()
    d = doc.to_dict()
    assert d["title"] == "T"
    assert d["authors"] == ["A", "B"]
    assert d["version"] == "1.0.0"
    assert len(d["tracks"]) == 3
    assert d["metadata"] == {"project": "test"}


def test_document_from_dict():
    data = {
        "title": "X",
        "authors": ["Y"],
        "created": "2025-06-01T12:00:00",
        "version": "2.0.0",
        "metadata": {"key": "val"},
        "tracks": [
            {"track_id": "primary", "track_type": "primary", "language": "en", "path": "tracks/primary.md", "content": "hi"},
        ],
    }
    doc = MDKVDocument.from_dict(data)
    assert doc.title == "X"
    assert doc.version == "2.0.0"
    assert doc.get_metadata("key") == "val"
    assert "primary" in doc.tracks


def test_document_to_from_dict_roundtrip():
    doc = _doc()
    data = doc.to_dict()
    restored = MDKVDocument.from_dict(data)
    assert restored.title == doc.title
    assert restored.authors == doc.authors
    assert restored.version == doc.version
    assert set(restored.tracks) == set(doc.tracks)
    for tid in doc.tracks:
        assert restored.tracks[tid].content == doc.tracks[tid].content
    assert restored.metadata == doc.metadata


def test_document_to_dict_json_serializable():
    doc = _doc()
    data = doc.to_dict()
    s = json.dumps(data)  # should not raise
    assert json.loads(s)["title"] == "T"


def test_track_repr():
    t = Track("primary", "primary", "en", "tracks/primary.md", "hello world")
    r = repr(t)
    assert "Track" in r
    assert "primary" in r
    assert "11 chars" in r


def test_document_repr():
    doc = _doc()
    r = repr(doc)
    assert "MDKVDocument" in r
    assert "title='T'" in r
    assert "tracks=3" in r


def test_count_tracks_by_type():
    doc = _doc()
    counts = doc.count_tracks_by_type()
    assert counts["primary"] == 1
    assert counts["commentary"] == 1
    assert counts["translation"] == 1
    assert "code" not in counts


def test_count_tracks_by_type_empty():
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    assert doc.count_tracks_by_type() == {}
