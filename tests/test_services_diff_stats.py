"""Tests for shared diff_documents and compute_stats services."""
from datetime import datetime

from mdkv.core.model import MDKVDocument, Track
from mdkv.services.diff import diff_documents, DiffResult
from mdkv.services.stats import compute_stats, DocumentStats


def _doc_a() -> MDKVDocument:
    d = MDKVDocument(title="A", authors=["X"], created=datetime(2025, 1, 1), version="1.0.0")
    d.add_track(Track("primary", "primary", "en", "tracks/primary.md", "original content"))
    d.add_track(Track("notes", "commentary", None, "tracks/notes.md", "note"))
    d.set_metadata("project", "test")
    return d


def _doc_b() -> MDKVDocument:
    d = MDKVDocument(title="B", authors=["Y"], created=datetime(2025, 1, 1), version="2.0.0")
    d.add_track(Track("primary", "primary", "en", "tracks/primary.md", "modified content"))
    d.add_track(Track("extra", "commentary", None, "tracks/extra.md", "new"))
    d.set_metadata("project", "test")
    d.set_metadata("status", "draft")
    return d


# === DiffResult tests ===

def test_diff_identical():
    a = _doc_a()
    b = _doc_a()
    result = diff_documents(a, b)
    assert not result.has_changes


def test_diff_has_changes():
    result = diff_documents(_doc_a(), _doc_b())
    assert result.has_changes


def test_diff_title_changed():
    result = diff_documents(_doc_a(), _doc_b())
    assert result.title_changed == ["A", "B"]


def test_diff_authors_changed():
    result = diff_documents(_doc_a(), _doc_b())
    assert result.authors_changed == [["X"], ["Y"]]


def test_diff_version_changed():
    result = diff_documents(_doc_a(), _doc_b())
    assert result.version_changed == ["1.0.0", "2.0.0"]


def test_diff_tracks_added():
    result = diff_documents(_doc_a(), _doc_b())
    assert "extra" in result.tracks_added


def test_diff_tracks_removed():
    result = diff_documents(_doc_a(), _doc_b())
    assert "notes" in result.tracks_removed


def test_diff_tracks_modified_content():
    result = diff_documents(_doc_a(), _doc_b())
    assert "primary" in result.tracks_modified


def test_diff_tracks_modified_type_only():
    a = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    a.add_track(Track("p", "primary", "en", "tracks/p.md", "same"))
    b = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    b.add_track(Track("p", "commentary", "en", "tracks/p.md", "same"))
    result = diff_documents(a, b)
    assert "p" in result.tracks_modified


def test_diff_metadata_added():
    result = diff_documents(_doc_a(), _doc_b())
    assert "status" in result.metadata_added


def test_diff_metadata_unchanged():
    result = diff_documents(_doc_a(), _doc_b())
    # "project" exists in both with same value
    assert len(result.metadata_changed) == 0


def test_diff_to_dict():
    result = diff_documents(_doc_a(), _doc_b())
    d = result.to_dict()
    assert d["title_changed"] == ["A", "B"]
    assert "extra" in d["tracks_added"]
    assert "notes" in d["tracks_removed"]


def test_diff_result_has_changes_empty():
    result = DiffResult()
    assert not result.has_changes


def test_diff_result_has_changes_nonempty():
    result = DiffResult(title_changed=["a", "b"])
    assert result.has_changes


# === compute_stats tests ===

def test_stats_basic():
    stats = compute_stats(_doc_a())
    assert stats.title == "A"
    assert stats.version == "1.0.0"
    assert stats.track_count == 2
    assert stats.tracks_by_type == {"primary": 1, "commentary": 1}
    assert stats.total_characters > 0
    assert stats.total_lines > 0


def test_stats_languages():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("p", "primary", "en", "tracks/p.md", "hi"))
    d.add_track(Track("fr", "translation", "fr", "tracks/fr.md", "salut"))
    stats = compute_stats(d)
    assert stats.languages == ["en", "fr"]


def test_stats_metadata_keys():
    d = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    d.add_track(Track("p", "primary", "en", "tracks/p.md", "hi"))
    d.set_metadata("zebra", "z")
    d.set_metadata("alpha", "a")
    stats = compute_stats(d)
    assert stats.metadata_keys == ["alpha", "zebra"]  # sorted


def test_stats_to_dict():
    stats = compute_stats(_doc_a())
    d = stats.to_dict()
    assert d["title"] == "A"
    assert d["track_count"] == 2
    assert "tracks_by_type" in d
    assert d["total_characters"] > 0


def test_stats_empty_doc():
    d = MDKVDocument(title="Empty", authors=["A"], created=datetime(2025, 1, 1))
    stats = compute_stats(d)
    assert stats.track_count == 0
    assert stats.total_characters == 0
    assert stats.total_lines == 0
    assert stats.tracks_by_type == {}
