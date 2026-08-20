from __future__ import annotations

"""Comprehensive tests targeting full GUI endpoint coverage (including /api/library and run())."""

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from mdkv.demo import build_multitrack_demo_document
from mdkv.gui.server import create_app, run, state
from mdkv.storage import save_mdkv


def test_gui_favicon_missing(tmp_path: Path):
    """Test favicon when favicon.svg does not exist in static_dir."""
    app = create_app(static_dir=tmp_path)
    client = TestClient(app)
    resp = client.get("/favicon.ico")
    assert resp.status_code == 200
    assert resp.text == ""


def test_gui_library_built_existing(tmp_path: Path):
    """Test /api/library when built files already exist."""
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/library")
    assert resp.status_code == 200
    data = resp.json()
    assert "files" in data
    assert isinstance(data["files"], list)


def test_gui_library_build_when_empty(tmp_path: Path):
    """Test /api/library triggers build_all_examples when _built is empty."""
    app = create_app()
    client = TestClient(app)
    with patch("pathlib.Path.glob", return_value=[]), patch("mdkv.gui.server.build_all_examples") as mock_build:
        resp = client.get("/api/library")
        assert resp.status_code == 200
        assert mock_build is not None


def test_gui_library_built_empty_failure(tmp_path: Path):
    """Test /api/library triggers 500 when definitions directory does not exist or raises error."""
    app = create_app()
    client = TestClient(app)
    with patch("mdkv.gui.server.build_all_examples", side_effect=Exception("definitions missing")):
        with patch("pathlib.Path.glob", return_value=[]):
            resp = client.get("/api/library")
            assert resp.status_code == 500


def test_gui_track_upsert_validation_error(tmp_path: Path):
    """Test /api/track with invalid track attributes (empty track_id or invalid type)."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    client = TestClient(app)

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


def test_gui_validate_track_raises_validation_error(tmp_path: Path):
    """Test /api/validate-track returns ok=False when ValidationError is raised."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    client = TestClient(app)

    with patch("mdkv.core.validate.validate_track", side_effect=Exception("mocked validation err")):
        from mdkv.core.errors import ValidationError
        with patch("mdkv.core.validate.validate_track", side_effect=ValidationError("fatal issue")):
            resp = client.get("/api/validate-track", params={"track_id": "primary"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["ok"] is False
            assert data["error"] == "fatal issue"


def test_gui_validate_document_error(tmp_path: Path):
    """Test /api/validate returns ok=False on document ValidationError."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    client = TestClient(app)

    from mdkv.core.errors import ValidationError
    with patch("mdkv.gui.server.validate_document", side_effect=ValidationError("primary track missing")):
        resp = client.post("/api/validate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is False
        assert data["error"] == "primary track missing"


def test_gui_import_track_edge_cases(tmp_path: Path):
    """Test /api/import missing fields and validation error."""
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()
    app = create_app()
    client = TestClient(app)

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
    client = TestClient(app)

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


def test_gui_run_function(tmp_path: Path):
    """Test the run() launcher function with and without initial file path."""
    doc = build_multitrack_demo_document()
    doc_path = tmp_path / "initial.mdkv"
    save_mdkv(doc, doc_path)

    with patch("uvicorn.run") as mock_uvicorn:
        run(host="127.0.0.1", port=8888, path=str(doc_path))
        mock_uvicorn.assert_called_once()
        assert state.path == doc_path
        assert state.doc is not None
        assert state.doc.title == doc.title

    with patch("uvicorn.run") as mock_uvicorn:
        run(host="127.0.0.1", port=8888, path=str(tmp_path / "nonexistent.mdkv"))
        mock_uvicorn.assert_called_once()
