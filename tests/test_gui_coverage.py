"""Targeted tests to improve GUI server coverage from 73% to 85%+."""
from pathlib import Path

from fastapi.testclient import TestClient

from mdkv.demo import build_multitrack_demo_document
from mdkv.gui.server import create_app, state
from mdkv.storage import save_mdkv


def _setup(tmp_path: Path):
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    return create_app(), TestClient(create_app())


def test_favicon():
    """favicon.ico endpoint."""
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.get("/favicon.ico")
    assert r.status_code == 200
    assert "svg" in r.headers.get("content-type", "")


def test_root_page():
    """GET / returns index.html."""
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.get("/")
    assert r.status_code == 200
    assert "<html" in r.text.lower() or "MDKV" in r.text


def test_open_file_success(tmp_path: Path):
    """POST /api/open with a valid file."""
    doc = build_multitrack_demo_document()
    p = tmp_path / "doc.mdkv"
    save_mdkv(doc, p)
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/open", json={"path": str(p)})
    assert r.status_code == 200
    assert r.json()["title"] == "MDKV Demo"


def test_open_file_corrupt(tmp_path: Path):
    """POST /api/open with a corrupt file returns 400."""
    bad = tmp_path / "bad.mdkv"
    bad.write_bytes(b"PK\x03\x04bogus")
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/open", json={"path": str(bad)})
    assert r.status_code == 400


def test_save_success(tmp_path: Path):
    """POST /api/save with a loaded document."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/save")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_save_no_path(tmp_path: Path):
    """POST /api/save without a path set returns 400."""
    state.path = None
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/save")
    assert r.status_code == 400


def test_render_html(tmp_path: Path):
    """GET /api/render/html."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/render/html")
    assert r.status_code == 200
    assert "<" in r.text  # HTML output


def test_render_markdown(tmp_path: Path):
    """GET /api/render/markdown."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/render/markdown")
    assert r.status_code == 200
    assert "markdown" in r.json()


def test_render_track_html(tmp_path: Path):
    """GET /api/render/track_html?track_id=..."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/render/track_html", params={"track_id": "primary"})
    assert r.status_code == 200
    assert "<" in r.text


def test_render_track_html_missing(tmp_path: Path):
    """GET /api/render/track_html with nonexistent track returns 404."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/render/track_html", params={"track_id": "nonexistent"})
    assert r.status_code == 404


def test_render_all_html(tmp_path: Path):
    """GET /api/render/all_html."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/render/all_html")
    assert r.status_code == 200
    assert "<" in r.text


def test_render_tracks_html_all(tmp_path: Path):
    """POST /api/render/tracks_html with no track_ids (renders all)."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/render/tracks_html", json={})
    assert r.status_code == 200
    assert "<" in r.text


def test_render_tracks_html_empty_list(tmp_path: Path):
    """POST /api/render/tracks_html with empty list renders nothing."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/render/tracks_html", json={"track_ids": []})
    assert r.status_code == 200


def test_render_tracks_html_subset(tmp_path: Path):
    """POST /api/render/tracks_html with a subset of track_ids."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/render/tracks_html", json={"track_ids": ["primary", "annotations"]})
    assert r.status_code == 200
    assert "<" in r.text


def test_render_tracks_html_invalid_ids_type(tmp_path: Path):
    """POST /api/render/tracks_html with non-list track_ids returns 422."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/render/tracks_html", json={"track_ids": "not-a-list"})
    assert r.status_code == 422


def test_render_track_html_no_doc():
    """GET /api/render/track_html without a document returns 400."""
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/render/track_html", params={"track_id": "x"})
    assert r.status_code == 400


def test_render_html_no_doc():
    """GET /api/render/html without a document returns 400."""
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/render/html")
    assert r.status_code == 400


def test_render_all_html_no_doc():
    """GET /api/render/all_html without a document returns 400."""
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/render/all_html")
    assert r.status_code == 400


def test_render_markdown_no_doc():
    """GET /api/render/markdown without a document returns 400."""
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/render/markdown")
    assert r.status_code == 400


def test_render_tracks_html_no_doc():
    """POST /api/render/tracks_html without a document returns 400."""
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/render/tracks_html", json={})
    assert r.status_code == 400


def test_validate_track_with_validation_error(tmp_path: Path):
    """GET /api/validate-track on a track that triggers a ValidationError."""
    from datetime import datetime

    from mdkv.core.model import MDKVDocument, Track
    doc = MDKVDocument(title="T", authors=["A"], created=datetime(2025, 1, 1))
    doc.add_track(Track("primary", "primary", "en", "tracks/primary.md", "content"))
    state.path = tmp_path / "t.mdkv"
    state.doc = doc
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/validate-track", params={"track_id": "primary"})
    assert r.status_code == 200


def test_move_track_missing_track_id(tmp_path: Path):
    """POST /api/move-track without track_id returns 422."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/move-track", json={})
    assert r.status_code == 422


def test_move_track_no_doc():
    """POST /api/move-track without a document returns 400."""
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/move-track", json={"track_id": "x"})
    assert r.status_code == 400


def test_open_file_missing_path():
    """POST /api/open with missing file returns 404."""
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/open", json={"path": "/nonexistent/file.mdkv"})
    assert r.status_code == 404


def test_save_no_doc():
    """POST /api/save without a document returns 400."""
    state.path = None
    state.doc = None
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/save")
    assert r.status_code == 400


def test_document_post_partial_update(tmp_path: Path):
    """POST /api/document with only title (no authors/version/metadata)."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/document", json={"title": "New Title Only"})
    assert r.status_code == 200
    assert state.doc.title == "New Title Only"


def test_get_track_missing(tmp_path: Path):
    """GET /api/track/{id} with nonexistent track returns 404."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    c = TestClient(app)
    r = c.get("/api/track/nonexistent")
    assert r.status_code == 404
