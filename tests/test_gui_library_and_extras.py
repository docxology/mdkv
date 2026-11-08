from __future__ import annotations

"""Comprehensive tests targeting full GUI endpoint coverage (including /api/library and run())."""

from pathlib import Path

from fastapi.testclient import TestClient

from mdkv.demo import build_multitrack_demo_document
from mdkv.gui.server import create_app, state
from mdkv.storage import save_mdkv


def test_gui_favicon_missing(tmp_path: Path):
    """Test favicon when favicon.svg does not exist in static_dir."""
    app = create_app(static_dir=tmp_path)
    client = TestClient(app, base_url="http://localhost")
    resp = client.get("/favicon.ico")
    assert resp.status_code == 200
    assert resp.text == ""


def test_gui_library_built_existing(tmp_path: Path):
    """Test /api/library when built files already exist."""
    app = create_app()
    client = TestClient(app, base_url="http://localhost")
    resp = client.get("/api/library")
    assert resp.status_code == 200
    data = resp.json()
    assert "files" in data
    assert isinstance(data["files"], list)


def test_gui_track_upsert_validation_error(tmp_path: Path):
    """Test /api/track with invalid track attributes (empty track_id or invalid type)."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    client = TestClient(app, base_url="http://localhost")

    # Missing ID
    r1 = client.post("/api/track", json={"id": ""})
    assert r1.status_code == 422

    # Invalid track_type for new track
    r2 = client.post("/api/track", json={"id": "bad_track", "type": "invalid_type"})
    assert r2.status_code == 400

    # Invalid track_type update on existing track
    r3 = client.post("/api/track", json={"id": "primary", "type": "nonexistent_type"})
    assert r3.status_code == 400
    assert "Unsupported track_type" in r3.json()["detail"]

    # Valid track update on existing track with language and content
    r4 = client.post("/api/track", json={"id": "primary", "type": "primary", "language": "en-US", "content": "# Updated Primary"})
    assert r4.status_code == 200
    assert state.doc is not None
    track = state.doc.get_track("primary")
    assert track is not None
    assert track.content == "# Updated Primary"
    assert track.language == "en-US"




def test_gui_validate_document_error(tmp_path: Path):
    """Deleting the primary track leaves an editable but invalid document."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    client = TestClient(create_app(), base_url="http://localhost")
    removed = client.delete("/api/track", params={"track_id": "primary"})
    assert removed.status_code == 200
    assert state.doc.get_track("primary") is None
    response = client.post("/api/validate")
    assert response.status_code == 200
    assert response.json()["ok"] is False


def test_gui_import_track_edge_cases(tmp_path: Path):
    """Test /api/import missing fields and validation error."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    client = TestClient(app, base_url="http://localhost")

    # Missing path
    r1 = client.post("/api/import", json={})
    assert r1.status_code == 422

    # File not found
    r2 = client.post("/api/import", json={"path": str(tmp_path / "nonexistent.md"), "id": "t1"})
    assert r2.status_code == 404

    # Invalid track_type
    f = tmp_path / "valid.md"
    f.write_text("content", encoding="utf-8")
    r3 = client.post("/api/import", json={"path": str(f), "id": "t1", "type": "bad_type"})
    assert r3.status_code == 400


def test_gui_diff_edge_cases(tmp_path: Path):
    """Test /api/diff and /api/diff/view error branches."""
    state.path = tmp_path / "a.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    client = TestClient(app, base_url="http://localhost")

    # Missing path in /api/diff
    r1 = client.post("/api/diff", json={})
    assert r1.status_code == 422

    # Corrupt target in /api/diff
    corrupt = tmp_path / "corrupt.mdkv"
    corrupt.write_bytes(b"not a zip")
    r2 = client.post("/api/diff", json={"path": str(corrupt)})
    assert r2.status_code == 400

    # Corrupt target in /api/diff/view
    r3 = client.get("/api/diff/view", params={"other_path": str(corrupt)})
    assert r3.status_code == 400


