"""Tests for enhanced GUI endpoints: /api/search, /api/stats, /api/diff, /api/validate warnings."""
from pathlib import Path

from fastapi.testclient import TestClient

from mdkv.gui.server import create_app, state
from mdkv.demo import build_multitrack_demo_document
from mdkv.storage import save_mdkv


def test_search_endpoint(tmp_path: Path):
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/search", params={"pattern": "MDKV"})
    assert r.status_code == 200
    data = r.json()
    assert "matches" in data
    assert len(data["matches"]) > 0
    m = data["matches"][0]
    assert "track_id" in m
    assert "track_type" in m
    assert "extract" in m


def test_search_case_insensitive(tmp_path: Path):
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/search", params={"pattern": "mdkv", "case_insensitive": "true"})
    assert r.status_code == 200
    assert len(r.json()["matches"]) > 0


def test_search_with_type_filter(tmp_path: Path):
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/search", params={"pattern": ".", "types": "primary"})
    assert r.status_code == 200
    matches = r.json()["matches"]
    assert all(m["track_type"] == "primary" for m in matches)


def test_search_no_doc_loaded():
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/search", params={"pattern": "test"})
    assert r.status_code == 400


def test_stats_endpoint(tmp_path: Path):
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["track_count"] == 5
    assert "primary" in data["tracks_by_type"]
    assert data["total_characters"] > 0
    assert data["total_lines"] > 0


def test_stats_no_doc():
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/stats")
    assert r.status_code == 400


def test_diff_endpoint(tmp_path: Path):
    # set up the primary doc
    state.path = tmp_path / "a.mdkv"
    state.doc = build_multitrack_demo_document()
    # create a second doc
    other = tmp_path / "b.mdkv"
    save_mdkv(build_multitrack_demo_document(), other)
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/diff", json={"path": str(other)})
    assert r.status_code == 200
    data = r.json()
    # identical docs → all empty
    assert data["title_changed"] == []
    assert data["tracks_added"] == []
    assert data["tracks_removed"] == []


def test_diff_with_changes(tmp_path: Path):
    from mdkv.core.model import MDKVDocument, Track
    state.path = tmp_path / "a.mdkv"
    state.doc = build_multitrack_demo_document()
    # create a modified version
    other_doc = MDKVDocument(title="Different", authors=["X"], created=state.doc.created)
    other_doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "# Modified"))
    other_path = tmp_path / "b.mdkv"
    save_mdkv(other_doc, other_path)
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/diff", json={"path": str(other_path)})
    assert r.status_code == 200
    data = r.json()
    assert data["title_changed"] == ["MDKV Demo", "Different"]
    assert "primary" in data["tracks_modified"]


def test_diff_missing_path(tmp_path: Path):
    state.path = tmp_path / "a.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/diff", json={"path": str(tmp_path / "missing.mdkv")})
    assert r.status_code == 404


def test_validate_returns_warnings(tmp_path: Path):
    from mdkv.core.model import MDKVDocument, Track
    doc = MDKVDocument(title="T", authors=["A"], created=state.doc.created if state.doc else __import__("datetime").datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "content"))
    doc.add_track(Track("notes", "commentary", None, "tracks/notes.md", "  "))  # empty → warn
    doc.version = "bad"  # bad version → warn
    state.path = tmp_path / "warn.mdkv"
    state.doc = doc
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/validate")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert len(data["warnings"]) >= 2  # empty content + bad version


def test_delete_track_404(tmp_path: Path):
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.delete("/api/track/nonexistent")
    assert r.status_code == 404


def test_document_includes_version_and_created(tmp_path: Path):
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/document")
    assert r.status_code == 200
    data = r.json()
    assert "version" in data
    assert "created" in data
