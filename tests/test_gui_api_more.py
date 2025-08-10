from pathlib import Path

from fastapi.testclient import TestClient

from mdkv.gui.server import create_app, state
from mdkv.demo import build_multitrack_demo_document


def test_open_save_update_delete_and_errors(tmp_path: Path):
    app = create_app()
    c = TestClient(app)

    # open error for missing file
    r_missing = c.post("/api/open", json={"path": str(tmp_path / "missing.mdkv")})
    assert r_missing.status_code == 404

    # preload a demo and save
    state.path = tmp_path / "t.mdkv"
    state.doc = build_multitrack_demo_document()

    r_save = c.post("/api/save")
    assert r_save.status_code == 200 and r_save.json()["ok"] is True

    # document update
    r_doc_update = c.post("/api/document", json={"title": "New Title", "authors": ["A", "B"]})
    assert r_doc_update.status_code == 200

    # upsert track
    r_upsert = c.post("/api/track", json={"id": "scratch", "type": "commentary", "content": "note"})
    assert r_upsert.status_code == 200

    # delete track
    r_delete = c.delete("/api/track/scratch")
    assert r_delete.status_code == 200

    # error branches when no doc is loaded
    state.path = None
    state.doc = None
    assert c.post("/api/save").status_code == 400
    assert c.get("/api/document").status_code == 400
    assert c.post("/api/document", json={}).status_code == 400
    assert c.post("/api/track", json={"id": "x"}).status_code == 400
    assert c.delete("/api/track/x").status_code == 400
    assert c.get("/api/render/html").status_code == 400
    assert c.get("/api/render/markdown").status_code == 400
    assert c.get("/api/render/track_html", params={"track_id": "x"}).status_code == 400
    assert c.get("/api/render/all_html").status_code == 400
    assert c.post("/api/validate").status_code == 400


